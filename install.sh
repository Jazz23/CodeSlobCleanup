#!/bin/bash

# CodeSlobCleanup Skill Installation Script
# Repository: https://github.com/Jazz23/CodeSlobCleanup

set -e

echo "Starting CodeSlobCleanup skill installation..."

# 1. Check for git
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git and try again."
    exit 1
fi

# 2. Check for uv and install if not already installed
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the cargo env if it's there, just in case
    [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
    # Add to path for current session
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "uv is already installed."
fi

# 3. Identify the agent folder in the Current Working Directory
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
    read -p "Please enter the folder name to install the skill into (e.g., .gemini): " USER_DIR
    
    # Ensure it's treated as a path relative to CWD if not absolute
    if [[ "$USER_DIR" == /* ]]; then
        AGENT_DIR="$USER_DIR"
    else
        AGENT_DIR="$PWD/$USER_DIR"
    fi
fi

# 4. Ensure the agent and skills directory exists
SKILLS_DIR="$AGENT_DIR/skills"
if [ ! -d "$SKILLS_DIR" ]; then
    echo "Creating directory: $SKILLS_DIR"
    mkdir -p "$SKILLS_DIR"
fi

# 5. Clone the repository to a temporary directory
TEMP_REPO_DIR=$(mktemp -d)
echo "Cloning CodeSlobCleanup repository to $TEMP_REPO_DIR..."
git clone --depth 1 https://github.com/Jazz23/CodeSlobCleanup.git "$TEMP_REPO_DIR"

# 6. Copy the code-slob-cleanup skill
SKILL_SOURCE="$TEMP_REPO_DIR/skills/code-slob-cleanup"

if [ -d "$SKILL_SOURCE" ]; then
    echo "Installing CodeSlobCleanup skill to $SKILLS_DIR..."
    rm -rf "$SKILLS_DIR/code-slob-cleanup"
    cp -r "$SKILL_SOURCE" "$SKILLS_DIR/"
    echo "Skill installed successfully!"
else
    echo "Error: Could not find skills/code-slob-cleanup in the cloned repository."
    rm -rf "$TEMP_REPO_DIR"
    exit 1
fi

# 7. Cleanup
echo "Cleaning up temporary files..."
rm -rf "$TEMP_REPO_DIR"

echo "Done!"
