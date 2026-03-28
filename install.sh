#!/bin/sh

# CodeSlobCleanup Skill Installation Script
# Repository: https://github.com/Jazz23/CodeSlobCleanup

# Exit on error
set -e

# Ensure common paths are in PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

echo "Starting CodeSlobCleanup skill installation..."

# Helper: read from terminal even when piped (curl | sh)
read_tty() {
    prompt="$1"
    var_name="$2"
    if [ -t 0 ]; then
        printf "%s" "$prompt"
        read _val
    else
        printf "%s" "$prompt" > /dev/tty
        read _val < /dev/tty
    fi
    eval "$var_name=\$_val"
}

# 1. Check for any existing installations across all known locations

EXISTING_COUNT=0
EXISTING_NAME_1="" EXISTING_PATH_1=""
EXISTING_NAME_2="" EXISTING_PATH_2=""
EXISTING_NAME_3="" EXISTING_PATH_3=""
EXISTING_NAME_4="" EXISTING_PATH_4=""
EXISTING_NAME_5="" EXISTING_PATH_5=""
EXISTING_NAME_6="" EXISTING_PATH_6=""

add_existing() {
    EXISTING_COUNT=$((EXISTING_COUNT + 1))
    eval "EXISTING_NAME_${EXISTING_COUNT}=\"\$1\""
    eval "EXISTING_PATH_${EXISTING_COUNT}=\"\$2\""
}
get_existing_name() { eval "printf '%s' \"\$EXISTING_NAME_${1}\""; }
get_existing_path() { eval "printf '%s' \"\$EXISTING_PATH_${1}\""; }

for _entry in \
    "Claude Code (global):$HOME/.claude/skills" \
    "Gemini CLI (global):$HOME/.gemini/skills" \
    "Codex CLI (global):$HOME/.codex/skills" \
    "Claude Code (local):$PWD/.claude/skills" \
    "Gemini CLI (local):$PWD/.gemini/skills" \
    "Codex CLI (local):$PWD/.agents/skills"; do
    _name="${_entry%%:*}"
    _path="${_entry#*:}"
    if [ -d "$_path/code-slob-cleanup" ]; then
        add_existing "$_name" "$_path"
    fi
done

# SKIP_TO_INSTALL=1 means we resolved targets here; skip the normal install picker below
SKIP_TO_INSTALL=0
SKILLS_DIRS=""
INSTALLED_NAMES=""

# Helper: build selected paths/names from a which-prompt over the existing list
# Sets _selected_paths and _selected_names
pick_existing() {
    _prompt="$1"
    _all_opt=$((EXISTING_COUNT + 1))
    _none_opt=$((EXISTING_COUNT + 2))
    _i=1
    while [ "$_i" -le "$EXISTING_COUNT" ]; do
        printf "  %d) %s\n" "$_i" "$(get_existing_name "$_i")"
        _i=$((_i + 1))
    done
    printf "  %d) All of the above\n" "$_all_opt"
    printf "  %d) None\n" "$_none_opt"
    read_tty "$_prompt [1-${_none_opt}]: " _which

    _selected_paths=""
    _selected_names=""
    case "$_which" in
        ''|*[!0-9]*) echo "Invalid choice, skipping." ;;
        *)
            if [ "$_which" -eq "$_all_opt" ]; then
                _i=1
                while [ "$_i" -le "$EXISTING_COUNT" ]; do
                    _selected_paths="$_selected_paths $(get_existing_path "$_i")"
                    _selected_names="$_selected_names$(get_existing_name "$_i"), "
                    _i=$((_i + 1))
                done
                _selected_paths=$(echo "$_selected_paths" | sed 's/^ //')
                _selected_names=$(echo "$_selected_names" | sed 's/, $//')
            elif [ "$_which" -eq "$_none_opt" ]; then
                :
            elif [ "$_which" -ge 1 ] && [ "$_which" -le "$EXISTING_COUNT" ]; then
                _selected_paths=$(get_existing_path "$_which")
                _selected_names=$(get_existing_name "$_which")
            else
                echo "Choice out of range, skipping."
            fi
            ;;
    esac
}

if [ "$EXISTING_COUNT" -eq 1 ]; then
    echo ""
    printf "Found existing installation in %s.\n" "$(get_existing_name 1)"
    echo "  1) Update"
    echo "  2) Remove"
    read_tty "Enter choice [1-2]: " _action

    case "$_action" in
        1)
            SKILLS_DIRS=$(get_existing_path 1)
            INSTALLED_NAMES=$(get_existing_name 1)
            SKIP_TO_INSTALL=1
            ;;
        2)
            rm -rf "$(get_existing_path 1)/code-slob-cleanup"
            printf "Removed from %s.\n" "$(get_existing_name 1)"
            echo "Re-run this script if you wish to reinstall!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Aborting."; exit 1
            ;;
    esac

elif [ "$EXISTING_COUNT" -gt 1 ]; then
    echo ""
    echo "Found existing installations in:"
    _i=1
    while [ "$_i" -le "$EXISTING_COUNT" ]; do
        printf "  %d) %s\n" "$_i" "$(get_existing_name "$_i")"
        _i=$((_i + 1))
    done
    echo ""
    echo "What would you like to do?"
    echo "  1) Update"
    echo "  2) Remove"
    read_tty "Enter choice [1-2]: " _action

    case "$_action" in
        1)
            echo ""
            pick_existing "Which to update?"
            if [ -n "$_selected_paths" ]; then
                SKILLS_DIRS="$_selected_paths"
                INSTALLED_NAMES="$_selected_names"
                SKIP_TO_INSTALL=1
            else
                echo "Nothing selected, exiting."
                exit 0
            fi
            ;;
        2)
            echo ""
            pick_existing "Which to remove?"
            if [ -n "$_selected_paths" ]; then
                for _p in $_selected_paths; do
                    rm -rf "$_p/code-slob-cleanup"
                done
                echo "Removed."
                echo "Re-run this script if you wish to reinstall!"
                exit 0
            else
                echo "Nothing selected, exiting."
                exit 0
            fi
            ;;
        *)
            echo "Invalid choice. Aborting."; exit 1
            ;;
    esac
fi

# 2. Check for uv and install if not already installed
if ! command -v uv > /dev/null 2>&1; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ -f "$HOME/.cargo/env" ]; then
        . "$HOME/.cargo/env"
    fi
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "uv is already installed."
fi

if [ "$SKIP_TO_INSTALL" -ne 1 ]; then

    # 3. Ask: global or local install?
    echo ""
    echo "Install scope:"
    echo "  1) Global  — available in all projects (~/.claude, ~/.gemini, ~/.codex)"
    echo "  2) Local   — current project only"
    read_tty "Enter choice [1/2] (default: 2): " INSTALL_SCOPE

    case "$INSTALL_SCOPE" in
        1) INSTALL_SCOPE="global" ;;
        *)  INSTALL_SCOPE="local" ;;
    esac

    echo "Installing $INSTALL_SCOPE..."

    # 4. Determine target skills directories

    DETECTED_COUNT=0
    AGENT_NAME_1="" AGENT_PATH_1=""
    AGENT_NAME_2="" AGENT_PATH_2=""
    AGENT_NAME_3="" AGENT_PATH_3=""

    add_agent() {
        DETECTED_COUNT=$((DETECTED_COUNT + 1))
        eval "AGENT_NAME_${DETECTED_COUNT}=\"\$1\""
        eval "AGENT_PATH_${DETECTED_COUNT}=\"\$2\""
    }
    get_agent_name() { eval "printf '%s' \"\$AGENT_NAME_${1}\""; }
    get_agent_path() { eval "printf '%s' \"\$AGENT_PATH_${1}\""; }

    pick_agents() {
        if [ "$DETECTED_COUNT" -eq 0 ]; then
            echo "No supported AI coding tools detected (claude, gemini, codex)."
            echo "Please install at least one of them, or re-run and choose local install."
            exit 1
        fi

        if [ "$DETECTED_COUNT" -eq 1 ]; then
            INSTALLED_NAMES=$(get_agent_name 1)
            SKILLS_DIRS=$(get_agent_path 1)
            return
        fi

        echo ""
        echo "Multiple agents detected. Where would you like to install?"
        i=1
        while [ "$i" -le "$DETECTED_COUNT" ]; do
            printf "  %d) %s (%s)\n" "$i" "$(get_agent_name "$i")" "$(get_agent_path "$i")"
            i=$((i + 1))
        done
        _all_opt=$((DETECTED_COUNT + 1))
        printf "  %d) All of the above\n" "$_all_opt"
        read_tty "Enter choice [1-${_all_opt}]: " AGENT_CHOICE

        SKILLS_DIRS=""
        INSTALLED_NAMES=""
        if [ "$AGENT_CHOICE" = "$_all_opt" ]; then
            i=1
            while [ "$i" -le "$DETECTED_COUNT" ]; do
                SKILLS_DIRS="$SKILLS_DIRS $(get_agent_path "$i")"
                INSTALLED_NAMES="$INSTALLED_NAMES$(get_agent_name "$i"), "
                i=$((i + 1))
            done
            SKILLS_DIRS=$(echo "$SKILLS_DIRS" | sed 's/^ //')
            INSTALLED_NAMES=$(echo "$INSTALLED_NAMES" | sed 's/, $//')
        else
            case "$AGENT_CHOICE" in
                ''|*[!0-9]*) echo "Invalid choice. Aborting."; exit 1 ;;
            esac
            if [ "$AGENT_CHOICE" -lt 1 ] || [ "$AGENT_CHOICE" -gt "$DETECTED_COUNT" ]; then
                echo "Choice out of range. Aborting."; exit 1
            fi
            INSTALLED_NAMES=$(get_agent_name "$AGENT_CHOICE")
            SKILLS_DIRS=$(get_agent_path "$AGENT_CHOICE")
        fi
    }

    if [ "$INSTALL_SCOPE" = "global" ]; then
        if [ -d "$HOME/.claude" ] || command -v claude > /dev/null 2>&1; then
            add_agent "Claude Code" "$HOME/.claude/skills"
        fi
        if [ -d "$HOME/.gemini" ] || command -v gemini > /dev/null 2>&1; then
            add_agent "Gemini CLI" "$HOME/.gemini/skills"
        fi
        if [ -d "$HOME/.codex" ] || command -v codex > /dev/null 2>&1; then
            add_agent "Codex CLI" "$HOME/.codex/skills"
        fi
        pick_agents
    else
        for entry in ".claude:Claude Code" ".gemini:Gemini CLI" ".agents:Codex CLI"; do
            dir="${entry%%:*}"
            name="${entry#*:}"
            if [ -d "$PWD/$dir" ]; then
                add_agent "$name" "$PWD/$dir/skills"
            fi
        done

        if [ "$DETECTED_COUNT" -eq 0 ]; then
            echo "Neither .claude, .gemini, nor .agents folders were found in ($PWD)."
            read_tty "Please enter the folder name to install into (e.g., .claude): " USER_DIR
            case "$USER_DIR" in
                /*) base="$USER_DIR" ;;
                *)  base="$PWD/$USER_DIR" ;;
            esac
            add_agent "$USER_DIR" "$base/skills"
        fi
        pick_agents
    fi

fi # end SKIP_TO_INSTALL

# 5. Create skills directories
for d in $SKILLS_DIRS; do
    if [ ! -d "$d" ]; then
        echo "Creating directory: $d"
        mkdir -p "$d"
    fi
done

# 6. Get the files (Git clone or ZIP fallback)
TEMP_DIR=$(mktemp -d)
REPO_URL="https://github.com/Jazz23/CodeSlobCleanup"

if command -v git > /dev/null 2>&1; then
    echo "Cloning CodeSlobCleanup repository..."
    git clone --depth 1 "$REPO_URL.git" "$TEMP_DIR"
    SKILL_SOURCE="$TEMP_DIR/skills/code-slob-cleanup"
else
    echo "git not found. Attempting to download repository as ZIP..."
    if command -v curl > /dev/null 2>&1 && command -v unzip > /dev/null 2>&1; then
        ZIP_URL="$REPO_URL/archive/refs/heads/main.zip"
        curl -LsSf "$ZIP_URL" -o "$TEMP_DIR/repo.zip"
        unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
        SKILL_SOURCE="$TEMP_DIR/CodeSlobCleanup-main/skills/code-slob-cleanup"
    else
        echo "Error: Both git and curl/unzip are missing. Please install git or curl and unzip to continue."
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# 7. Copy the skill into each target directory
if [ -d "$SKILL_SOURCE" ]; then
    for d in $SKILLS_DIRS; do
        rm -rf "$d/code-slob-cleanup"
        cp -r "$SKILL_SOURCE" "$d/"
    done
    echo "Installed Code Slob Cleanup skill to ${INSTALLED_NAMES}!"
else
    echo "Error: Could not find skills/code-slob-cleanup in the downloaded files."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 8. Cleanup
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Done!"
