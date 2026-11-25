#!/bin/sh
# prior-art stop check. `mark` records that code was written; `stop` and `subagent-stop` hand Claude
# the library-first check once before it finishes. Shell builtins plus cat, mkdir and rm only.
input=$(cat)

# field NAME: the string value of a key in the hook input. Keys quoted inside written code arrive
# escaped (\"name\"), so they never match.
field() {
  case $input in *"\"$1\""*) ;; *) return ;; esac
  value=${input#*"\"$1\""}
  case $value in :\"*|:\ \"*) ;; *) return ;; esac
  value=${value#*\"}
  printf %s "${value%%\"*}"
}

# A subagent answers for its own code; everything else belongs to the session.
who=$(field agent_id)
[ "$1" = stop ] && who=
[ -n "$who" ] || who=$(field session_id)
case $who in ''|*[!A-Za-z0-9_-]*) exit 0 ;; esac
dir=${CLAUDE_PLUGIN_DATA:-${TMPDIR:-/tmp}/prior-art}/wrote
wrote=$dir/$who
asked=$wrote.asked

if [ "$1" = mark ]; then
  case $(field file_path) in *.md|*.mdx|*.txt|*.rst|*.json|*.yaml|*.yml|*.toml|*.lock|*.csv) exit 0 ;; esac
  mkdir -p "$dir" && : > "$wrote"
  exit 0
fi

if [ -f "$asked" ]; then
  rm -f "$asked"
  # Claude is answering the check: what it wrote since then is the fix, not new work to check.
  case $input in *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) rm -f "$wrote"; exit 0 ;; esac
fi
[ -f "$wrote" ] || exit 0
rm -f "$wrote"
: > "$asked"
cat "${0%/*}/$1.json"
