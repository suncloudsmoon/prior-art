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


def run_hook(event, plugin_root=ROOT, path=None):
    """Run the hook as Claude Code does on macOS/Linux: substitute ${CLAUDE_PLUGIN_ROOT}, then `sh -c` from the user's project with hook input on stdin."""
    _, hook = hook_config(event)
    command = hook["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_root))
    env = {**os.environ, "PATH": path} if path else None
    with tempfile.TemporaryDirectory() as project:
        return subprocess.run(
            ["/bin/sh", "-c", command],
            input=json.dumps({"hook_event_name": event, "cwd": project}),
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


if __name__ == "__main__":
    unittest.main()
