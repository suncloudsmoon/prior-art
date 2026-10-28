#!/usr/bin/env python3
"""Check that the prior-art skill is invoked when it should be, and not otherwise, in a real Claude Code setup.

Same detection as skill-creator's run_eval.py (watch stream-json for a Skill call, stop early),
but against a whole plugin install instead of a temporary copy of the description. Paid: each run
is a real `claude -p` call on your login. Run it after any change to the skill description.

Usage: python3 tests/triggers/run_trigger_eval.py [model] [runs] [evals.json]
  TRIGGER_PLUGIN_DIR=.  test this working copy (the installed prior-art is switched off for the run)
  TRIGGER_TIMEOUT=180   seconds per run (slower models need more)
Pass bar: every should-trigger prompt fires in at least half its runs; every near-miss in fewer.
"""
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).parent
TIMEOUT = int(os.environ.get("TRIGGER_TIMEOUT", "90"))  # seconds per run; slower models need more
MAX_TOOLS = 3  # a verdict comes from the first few tool calls; later ones are the task itself
PLUGIN_DIR = os.environ.get("TRIGGER_PLUGIN_DIR")  # unset: test the installed plugin
PLUGIN_DIR = PLUGIN_DIR and os.path.abspath(PLUGIN_DIR)  # runs start in a temp folder, so pin relative paths now
LABEL = os.environ.get("TRIGGER_LABEL", "")  # suffix for the results file


def run_once(query, model, cwd):
    """Return (skills invoked before the run was stopped, token usage)."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}  # allow nesting, as run_eval.py does
    cmd = ["claude", "-p", query, "--model", model, "--output-format", "stream-json",
           "--verbose", "--no-session-persistence"]
    if PLUGIN_DIR:  # test a working copy: load it and switch the installed copy off for this run
        cmd += ["--plugin-dir", PLUGIN_DIR, "--settings", '{"enabledPlugins": {"prior-art@suncloudsmoon": false}}']
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    watchdog = threading.Timer(TIMEOUT, proc.kill)
    watchdog.start()
    skills, tools, tokens = [], 0, 0
    try:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "result":
                break
            if event.get("type") != "assistant":
                continue
            message = event["message"]
            usage = message.get("usage") or {}
            tokens += sum(usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                                     "cache_read_input_tokens", "output_tokens"))
            for block in message.get("content") or []:
                if block.get("type") == "tool_use":
                    tools += 1
                    if block["name"] == "Skill":
                        skills.append((block.get("input") or {}).get("skill", ""))
            if any("prior-art" in s for s in skills) or tools >= MAX_TOOLS:
                break
    finally:
        watchdog.cancel()
        proc.kill()
        proc.wait()
    return skills, tokens


def main():
    args = sys.argv[1:]
    cwd = tempfile.mkdtemp(prefix="prior-art-trigger-")  # outside any repo, so no project name biases the run
    try:
        if args[:1] == ["--one"]:
            print(run_once(args[1], args[2] if len(args) > 2 else "claude-haiku-5-5", cwd))
            return
        model = args[0] if args else "claude-haiku-5-5"
        runs = int(args[1]) if len(args) > 1 else 3
        evals = json.loads((HERE / (args[2] if len(args) > 2 else "trigger-evals.json")).read_text())
        jobs = [i for i in range(len(evals)) for _ in range(runs)]
        with cf.ThreadPoolExecutor(5) as pool:
            outcomes = list(pool.map(lambda i: (i, *run_once(evals[i]["query"], model, cwd)), jobs))
    finally:
        shutil.rmtree(cwd, ignore_errors=True)

    rows, total_tokens = [], 0
    for i, item in enumerate(evals):
        mine = [(s, t) for j, s, t in outcomes if j == i]
        hits = sum(any("prior-art" in x for x in s) for s, _ in mine)
        total_tokens += sum(t for _, t in mine)
        rate = hits / runs
        passed = (rate >= 0.5) == item["should_trigger"]
        others = sorted({x for s, _ in mine for x in s if "prior-art" not in x})
        rows.append({"query": item["query"], "should_trigger": item["should_trigger"], "hits": hits,
                     "runs": runs, "pass": passed, "other_skills": others})
        print(f"{'PASS' if passed else 'FAIL'} {'trig' if item['should_trigger'] else 'skip'} {hits}/{runs}"
              f"  {item['query'][:70]}  {others or ''}")
    pos = [r for r in rows if r["should_trigger"]]
    neg = [r for r in rows if not r["should_trigger"]]
    summary = {"model": model, "runs_per_query": runs, "total_tokens": total_tokens,
               "should_trigger_passed": sum(r["pass"] for r in pos), "should_trigger_total": len(pos),
               "should_skip_passed": sum(r["pass"] for r in neg), "should_skip_total": len(neg)}
    print(json.dumps(summary))
    (HERE / f"results-{model}{LABEL}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")
    sys.exit(0 if all(r["pass"] for r in rows) else 1)


if __name__ == "__main__":
    main()
