#!/bin/sh

# CodeSlobCleanup One-Command Setup Script
# Usage: curl -LsSf <url> | sh -s -- <ProjectName> <TargetDir>

set -e

PROJECT_NAME="$1"
TARGET_DIR="$2"

if [ -z "$PROJECT_NAME" ] || [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <ProjectName> <TargetDir>"
    echo "Example: $0 myproject ~/work/myproject"
    exit 1
fi

# Expand ~ in TARGET_DIR if present (basic expansion for sh)
case "$TARGET_DIR" in
    ~*) TARGET_DIR="$HOME${TARGET_DIR#~}" ;;
esac

echo "Starting setup for project: $PROJECT_NAME in $TARGET_DIR"

# 1. Ensure common paths are in PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

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

# 3. Create Target Directory
if [ -d "$TARGET_DIR" ]; then
    echo "Target directory already exists. Cleaning it for a fresh install..."
    # We remove it to avoid permission issues with existing .git directories
    # or conflicting old wrappers.
    rm -rf "$TARGET_DIR"
fi
mkdir -p "$TARGET_DIR"

# 4. Fetch the repository
# We'll use a temp dir for the initial fetch to handle zip root folders correctly
TEMP_DIR=$(mktemp -d)
REPO_URL="https://github.com/Jazz23/CodeSlobCleanup"

# Check if we are running from the project root and can use local source
# Use a trick to get the script's directory even when piped (though that's rare for local file)
# If $0 is a file that exists, we can use it.
if [ -f "$0" ] && [ -d "$(dirname "$0")/skills/code-slob-cleanup" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    echo "Using local source from $SCRIPT_DIR..."
    # Copy from local source instead of cloning
    cp -Rp "$SCRIPT_DIR/." "$TARGET_DIR/"
elif command -v git > /dev/null 2>&1; then
    echo "Cloning CodeSlobCleanup repository..."
    git clone --depth 1 "$REPO_URL.git" "$TEMP_DIR"
    # Move files to target dir (including hidden ones)
    cp -Rp "$TEMP_DIR/." "$TARGET_DIR/"
else
    echo "git not found. Using curl + unzip..."
    ZIP_URL="$REPO_URL/archive/refs/heads/main.zip"
    curl -LsSf "$ZIP_URL" -o "$TEMP_DIR/repo.zip"
    unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
    # GitHub zips nest everything in RepoName-BranchName
    cp -Rp "$TEMP_DIR/CodeSlobCleanup-main/." "$TARGET_DIR/"
fi

# 5. Setup Project Local Bin
BIN_DIR="$TARGET_DIR/.codeslob/bin"
mkdir -p "$BIN_DIR"

echo "Creating binary wrappers for all scripts..."
# We need to find the scripts in the target directory
SCRIPTS_DIR="$TARGET_DIR/skills/code-slob-cleanup/scripts"
for script_path in "$SCRIPTS_DIR"/*.py; do
    [ -e "$script_path" ] || continue
    script_file=$(basename "$script_path")
    script_name="${script_file%.py}"
    
    # Skip library modules or internal files
    case "$script_name" in
        __init__|common|metrics|semantic) continue ;;
    esac
    
    cat > "$BIN_DIR/$script_name" <<EOF
#!/bin/sh
# Wrapper for $script_file in $PROJECT_NAME
# Self-locating: find the project root relative to this script
SCRIPT_PATH="\$(cd "\$(dirname "\$0")" && pwd)"
PROJECT_ROOT="\$(cd "\$SCRIPT_PATH/../.." && pwd)"
cd "\$PROJECT_ROOT" && uv run skills/code-slob-cleanup/scripts/$script_file "\$@"
EOF
    chmod +x "$BIN_DIR/$script_name"
    echo "  - Created wrapper: $script_name"
done

# Create aliases for the main identification tool
if [ -f "$BIN_DIR/identify" ]; then
    cp "$BIN_DIR/identify" "$BIN_DIR/codeslob"
    if [ "$PROJECT_NAME" != "codeslob" ] && [ "$PROJECT_NAME" != "identify" ]; then
        echo "Creating master help wrapper for $PROJECT_NAME..."
        cat > "$BIN_DIR/$PROJECT_NAME" <<EOF
#!/bin/sh
# Master Wrapper for $PROJECT_NAME
# Self-locating: find the project root relative to this script
SCRIPT_PATH="\$(cd "\$(dirname "\$0")" && pwd)"
BIN_DIR="\$SCRIPT_PATH"
PROJECT_ROOT="\$(cd "\$BIN_DIR/../.." && pwd)"

if [ "\$1" = "--help" ] || [ "\$1" = "-h" ]; then
    echo "=========================================================="
    echo "          $PROJECT_NAME - CODE SLOB CLEANUP SUITE          "
    echo "=========================================================="
    for tool_path in "\$BIN_DIR"/*; do
        tool_name=\$(basename "\$tool_path")
        # Skip aliases to avoid redundancy
        case "\$tool_name" in
            "$PROJECT_NAME"|codeslob|identify) continue ;;
        esac
        
        if [ -x "\$tool_path" ]; then
            echo ""
            echo ">>> HELP FOR: \$tool_name"
            "\$tool_path" --help 2>&1 | sed 's/^/  /'
            echo "----------------------------------------------------------"
        fi
    done
    
    # Finally show the main identify help
    echo ""
    echo ">>> HELP FOR: identify (default tool)"
    "\$BIN_DIR/identify" --help 2>&1 | sed 's/^/  /'
else
    cd "\$PROJECT_ROOT" && "\$BIN_DIR/identify" "\$@"
fi
EOF
        chmod +x "$BIN_DIR/$PROJECT_NAME"
    fi
fi

# 6. Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✨ Setup complete!"
echo "Project location: $TARGET_DIR"
echo ""
echo "To use the '$PROJECT_NAME' command, run this command in your current shell:"
echo "----------------------------------------------------------------------"
echo "export PATH=\"\$PATH:$BIN_DIR\""
echo "----------------------------------------------------------------------"
echo ""
echo "IMPORTANT: Copy the line above EXACTLY. Do not use '~' inside quotes,"
echo "as your shell will not expand it correctly."
echo ""
echo "For permanent access, add the line to your .bashrc or .zshrc."
echo "If you use Zsh, you may also need to run 'rehash' to update your command cache."
echo ""
echo "Then you can run:"
echo "  cd $TARGET_DIR"
echo "  $PROJECT_NAME --help"
