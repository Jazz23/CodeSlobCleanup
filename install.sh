#!/bin/bash

# CodeSlobCleanup Skill Installation Script
# Repository: https://github.com/Jazz23/CodeSlobCleanup

set -e

# Ensure common paths are in PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

echo "Starting CodeSlobCleanup skill installation..."

# 1. Check for uv and install if not already installed
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the cargo env if it's there
    [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
    # Ensure local bin is in PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "uv is already installed."
fi

# 2. Identify the agent folder in the Current Working Directory
AGENT_DIR=""
POSSIBLE_DIRS=(".gemini" ".claude" ".agents")

for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$PWD/$dir" ]; then
        AGENT_DIR="$PWD/$dir"
        echo "Found agent folder in CWD: $AGENT_DIR"
        break
    fi
done

# If not found, ask the user for the folder name
if [ -z "$AGENT_DIR" ]; then
    echo "Neither .gemini, .claude, nor .agents folders were found in the current directory ($PWD)."
    
    # When running via 'curl | sh', stdin is the script itself. 
    # We must read from /dev/tty to get actual user input.
    # Also using printf + read for maximum portability across sh/bash/dash.
    if [ -t 0 ]; then
        printf "Please enter the folder name to install the skill into (e.g., .gemini): "
        read USER_DIR
    else
        printf "Please enter the folder name to install the skill into (e.g., .gemini): " > /dev/tty
        read USER_DIR < /dev/tty
    fi
    
    # Ensure it's treated as a path relative to CWD if not absolute
    if [[ "$USER_DIR" == /* ]]; then
        AGENT_DIR="$USER_DIR"
    else
        AGENT_DIR="$PWD/$USER_DIR"
    fi
fi

# 3. Ensure the agent and skills directory exists
SKILLS_DIR="$AGENT_DIR/skills"
if [ ! -d "$SKILLS_DIR" ]; then
    echo "Creating directory: $SKILLS_DIR"
    mkdir -p "$SKILLS_DIR"
fi

# 4. Get the files (Git clone or ZIP fallback)
TEMP_DIR=$(mktemp -d)
REPO_URL="https://github.com/Jazz23/CodeSlobCleanup"

if command -v git &> /dev/null; then
    echo "Cloning CodeSlobCleanup repository..."
    git clone --depth 1 "$REPO_URL.git" "$TEMP_DIR"
    SKILL_SOURCE="$TEMP_DIR/skills/code-slob-cleanup"
else
    echo "git not found. Attempting to download repository as ZIP..."
    if command -v curl &> /dev/null && command -v unzip &> /dev/null; then
        ZIP_URL="$REPO_URL/archive/refs/heads/main.zip"
        curl -LsSf "$ZIP_URL" -o "$TEMP_DIR/repo.zip"
        unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
        # GitHub zips put everything in a subdirectory named 'RepoName-BranchName'
        SKILL_SOURCE="$TEMP_DIR/CodeSlobCleanup-main/skills/code-slob-cleanup"
    else
        echo "Error: Both git and curl/unzip are missing. Please install git or curl and unzip to continue."
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# 5. Copy the code-slob-cleanup skill
if [ -d "$SKILL_SOURCE" ]; then
    echo "Installing CodeSlobCleanup skill to $SKILLS_DIR..."
    rm -rf "$SKILLS_DIR/code-slob-cleanup"
    cp -r "$SKILL_SOURCE" "$SKILLS_DIR/"
    echo "Skill installed successfully!"
else
    echo "Error: Could not find skills/code-slob-cleanup in the downloaded files."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 6. Cleanup
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Done!"
