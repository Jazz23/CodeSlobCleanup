SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# If $1 it's claude, the command is `claude --dangerously-skip-permissions`, if it's gemini, the command is `gemini -y`, if it's blank then ask the user for the command to run.

HEADLESS_PROMPT=""

# Parse optional -prompt flag (can appear anywhere in args)
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -prompt)
      HEADLESS_PROMPT="$2"
      shift 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

if [ -z "$1" ]; then
  read -p "Test with (gemini/claude): " MODEL
elif [[ "$1" == "gemini" || "$1" == "claude" ]]; then
  MODEL="$1"
else
  echo "Invalid argument. Please enter 'gemini' or 'claude'."
  exit 1
fi

if [ -z "$2" ]; then
  read -p "Codebase name: " CODEBASE
else
  CODEBASE="$2"
fi

if [ "$MODEL" == "claude" ]; then
  if [ -n "$HEADLESS_PROMPT" ]; then
    COMMAND="claude --dangerously-skip-permissions -p \"$HEADLESS_PROMPT\""
  else
    COMMAND="claude --dangerously-skip-permissions"
  fi
elif [ "$MODEL" == "gemini" ]; then
  if [ -n "$HEADLESS_PROMPT" ]; then
    COMMAND="gemini -y --output-format json -p \"$HEADLESS_PROMPT\""
  else
    COMMAND="gemini -y"
  fi
fi

docker run -i -t --rm -v "$PARENT_DIR/codebases/$CODEBASE:/tempCodebase:ro" -v "$PARENT_DIR/skills:/tempSkill:ro" -v ~/.gemini:/home/node/.gemini -v ~/.claude:/home/node/.claude agent-test bash -c "cp -r /tempCodebase/. /app && mkdir -p /app/.gemini /app/.claude && cp -r /tempSkill/. /app/.gemini/skills && cp -r /tempSkill/. /app/.claude/skills && $COMMAND"
