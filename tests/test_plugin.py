"""Checks the hook wiring that injects the library-first convention."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_CAP = 10_000  # Claude Code's per-string limit on hook context


def hook_config(event):
    [entry] = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"][event]
    [hook] = entry["hooks"]
    return entry, hook


def run_hook(event, plugin_root=ROOT, path=None, data_dir=None, **fields):
    """Run the hook as Claude Code does on macOS/Linux: substitute ${CLAUDE_PLUGIN_ROOT}, then `sh -c` from the user's project with hook input on stdin."""
    _, hook = hook_config(event)
    command = hook["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_root))
    env = {**os.environ, **({"PATH": path} if path else {}), **({"CLAUDE_PLUGIN_DATA": data_dir} if data_dir else {})}
    with tempfile.TemporaryDirectory() as project:
        return subprocess.run(
            ["/bin/sh", "-c", command],
            input=json.dumps({"hook_event_name": event, "cwd": project, **fields}),
            capture_output=True, text=True, timeout=10, cwd=project, env=env,
        )


def convention(plugin_root=ROOT):
    return (plugin_root / "hooks" / "library-first.md").read_text(encoding="utf-8")


class HookTests(unittest.TestCase):
    def assert_injects(self, result, event, plugin_root=ROOT):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.isascii())
        self.assertEqual(json.loads(result.stdout), {"hookSpecificOutput": {
            "hookEventName": event, "additionalContext": convention(plugin_root)}},
            "hook output is stale: run `python3 hooks/build.py` after editing library-first.md")

    def test_session_start_injects_convention(self):
        entry, hook = hook_config("SessionStart")
        self.assertEqual(entry["matcher"], "startup|resume|clear|compact")
        self.assertEqual(hook["timeout"], 10)
        self.assert_injects(run_hook("SessionStart"), "SessionStart")

    def test_subagent_start_injects_convention_for_every_agent_type(self):
        entry, hook = hook_config("SubagentStart")
        self.assertNotIn("matcher", entry)
        self.assertEqual(hook["timeout"], 10)
        self.assert_injects(run_hook("SubagentStart"), "SubagentStart")

    def test_hooks_run_without_python(self):
        with tempfile.TemporaryDirectory() as bin_dir:
            os.symlink(shutil.which("cat"), Path(bin_dir) / "cat")
            for event in ("SessionStart", "SubagentStart"):
                self.assert_injects(run_hook(event, path=bin_dir), event)

    def test_convention_fits_context_cap(self):
        self.assertLess(len(convention()), CONTEXT_CAP)

    def test_build_and_hooks_handle_spaced_path_and_non_ascii_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            spaced = Path(tmp) / "plugin root with spaces"
            shutil.copytree(ROOT / "hooks", spaced / "hooks")
            with open(spaced / "hooks" / "library-first.md", "a", encoding="utf-8") as f:
                f.write("Prices like 1.234,50 € — fine.\n")
            subprocess.run([sys.executable, spaced / "hooks" / "build.py"], check=True, timeout=10)
            for event in ("SessionStart", "SubagentStart"):
                self.assert_injects(run_hook(event, spaced), event, spaced)


class StopCheckTests(unittest.TestCase):
    """The library-first check Claude gets before it finishes a turn that wrote code."""

    def setUp(self):
        data = tempfile.TemporaryDirectory()
        self.addCleanup(data.cleanup)
        self.data_dir = data.name

    def fire(self, event, path=None, **fields):
        return run_hook(event, path=path, data_dir=self.data_dir, session_id="session-1", **fields)

    def write(self, file_path="/project/app.py", **fields):
        result = self.fire("PostToolUse", tool_name="Write", tool_input={"file_path": file_path, "content": "x = 1\n"}, **fields)
        self.assert_silent(result)

    def assert_asks(self, result, event):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": (ROOT / "hooks" / "stop-check.md").read_text(encoding="utf-8")}},
            "hook output is stale: run `python3 hooks/build.py` after editing stop-check.md")

    def assert_silent(self, result):
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_hooks_are_wired_to_writes_and_stops(self):
        entry, _ = hook_config("PostToolUse")
        self.assertEqual(entry["matcher"], "Write|Edit|MultiEdit|NotebookEdit")
        for event in ("Stop", "SubagentStop"):
            self.assertNotIn("matcher", hook_config(event)[0])

    def test_asks_once_when_the_turn_wrote_code(self):
        self.write()
        self.assert_asks(self.fire("Stop", stop_hook_active=False), "Stop")
        self.assert_silent(self.fire("Stop", stop_hook_active=True))

    def test_silent_when_the_turn_wrote_no_code(self):
        self.assert_silent(self.fire("Stop", stop_hook_active=False))
        for prose_or_data in ("/project/README.md", "/project/config.json", "/project/notes.txt"):
            self.write(prose_or_data)
        self.assert_silent(self.fire("Stop", stop_hook_active=False))

    def test_fixes_made_in_answer_to_the_check_are_not_checked_again(self):
        self.write()
        self.assert_asks(self.fire("Stop", stop_hook_active=False), "Stop")
        self.write()
        self.assert_silent(self.fire("Stop", stop_hook_active=True))
        self.assert_silent(self.fire("Stop", stop_hook_active=False))

    def test_asks_when_another_stop_hook_made_claude_write_more_code(self):
        self.write()
        self.assert_asks(self.fire("Stop", stop_hook_active=True), "Stop")

    def test_the_next_turn_is_checked_after_an_interrupted_one(self):
        self.write()
        self.assert_asks(self.fire("Stop", stop_hook_active=False), "Stop")
        self.write()
        self.assert_asks(self.fire("Stop", stop_hook_active=False), "Stop")

    def test_subagent_answers_for_its_own_code(self):
        self.write(agent_id="agent-7", agent_type="general-purpose")
        self.assert_silent(self.fire("Stop", stop_hook_active=False))
        self.assert_asks(self.fire("SubagentStop", stop_hook_active=False, agent_id="agent-7"), "SubagentStop")
        self.assert_silent(self.fire("SubagentStop", stop_hook_active=True, agent_id="agent-7"))

    def test_code_that_mentions_hook_fields_does_not_confuse_the_check(self):
        tricky = 'print({"session_id": "../../etc", "agent_id": "x", "file_path": "notes.md"})\n'
        self.assert_silent(self.fire("PostToolUse", tool_name="Write", tool_input={"content": tricky, "file_path": "/project/app.py"}))
        self.assert_asks(self.fire("Stop", stop_hook_active=False), "Stop")

    def test_runs_with_only_basic_shell_tools(self):
        with tempfile.TemporaryDirectory() as bin_dir:
            for tool in ("sh", "cat", "mkdir", "rm"):
                os.symlink(shutil.which(tool), Path(bin_dir) / tool)
            self.assert_silent(self.fire("PostToolUse", path=bin_dir, tool_name="Edit",
                                         tool_input={"file_path": "/project/app.py", "old_string": "a", "new_string": "b"}))
            self.assert_asks(self.fire("Stop", path=bin_dir, stop_hook_active=False), "Stop")


if __name__ == "__main__":
    unittest.main()
