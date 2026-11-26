#!/bin/sh
# prior-art stop check. `mark` records that code, or a document that may be a plan or spec, was written;
# `stop` and `subagent-stop` hand Claude the matching check once before it finishes. Shell builtins plus
# cat, mkdir and rm only.
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
planned=$wrote.plan
asked=$wrote.asked

if [ "$1" = mark ]; then
  path=$(field file_path)
  mark=$wrote
  case $path in
    *.md|*.mdx)
      # Markdown under a hidden folder is a tool's own notes (memory, research). The path is read from the
      # project root, and from inside a worktree, so those can sit under a hidden folder themselves.
      doc=${path#"$(field cwd)"/}
      case $doc in */worktrees/*) doc=${doc##*/worktrees/}; doc=${doc#*/} ;; esac
      case /$doc in */.*|*\\.*) exit 0 ;; esac
      mark=$planned ;;
    *.txt|*.rst|*.json|*.yaml|*.yml|*.toml|*.lock|*.csv) exit 0 ;;
  esac
  mkdir -p "$dir" && : > "$mark"
  exit 0
fi

if [ -f "$asked" ]; then
  rm -f "$asked"
  # Claude is answering the check: what it wrote since then is the fix, not new work to check.
  case $input in *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) rm -f "$wrote" "$planned"; exit 0 ;; esac
fi
# A turn that wrote code gets the code check, even if it also touched a plan: that plan was checked when written.
if [ -f "$wrote" ]; then check=$1
elif [ -f "$planned" ]; then check=$1-plan
else exit 0
fi
rm -f "$wrote" "$planned"
: > "$asked"
cat "${0%/*}/$check.json"
