#!/bin/bash

# install.sh - One-command setup for CodeSlobCleanup
# Usage: curl -LsSf https://raw.githubusercontent.com/Jazz23/CodeSlobCleanup/main/scripts/install.sh | sh

set -e

REPO_URL="https://github.com/Jazz23/CodeSlobCleanup.git"
INSTALL_DIR="${HOME}/.codeslob"
BIN_DIR="${INSTALL_DIR}/bin"

echo ">>> Starting CodeSlobCleanup installation..."

# 1. Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo ">>> uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source uv environment if possible, or assume it's in PATH after install
    if [ -f "$HOME/.cargo/env" ]; then
        . "$HOME/.cargo/env"
    fi
    # Add to current path for this session just in case
    export PATH="$HOME/.astral-bin:$PATH"
else
    echo ">>> uv is already installed."
fi

# 2. Setup/Update the repository
if [ ! -d "$INSTALL_DIR" ]; then
    echo ">>> Cloning CodeSlobCleanup to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    echo ">>> Updating existing CodeSlobCleanup at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull
fi

# 3. Create bin directory and wrapper
mkdir -p "$BIN_DIR"

echo ">>> Creating 'codeslob' wrapper..."
cat <<EOF > "$BIN_DIR/codeslob"
#!/bin/bash
# Wrapper for CodeSlobCleanup identify tool
uv run --project "$INSTALL_DIR" "$INSTALL_DIR/skills/code-slob-cleanup/scripts/identify.py" "\$@"
EOF

chmod +x "$BIN_DIR/codeslob"

# 4. Final instructions
echo ""
echo ">>> Installation complete!"
echo ">>> Please add the following to your .bashrc or .zshrc:"
echo "export PATH=\"\$BIN_DIR:\$PATH\""
echo ""
echo ">>> After restarting your shell or running the export command above, you can run:"
echo "codeslob --help"
