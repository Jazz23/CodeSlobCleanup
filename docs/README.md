# Code Slob Cleanup Documentation

Welcome to the documentation for the **Code Slob Cleanup** project. This project provides an automated toolchain and a packaged skill for coding agents, designed to identify, refactor, and rigorously verify Python code to remove "code slob"—subtle technical debt, unnecessary verbosity, and complexity often introduced by AI coding agents or rapid development.

## Getting Started

### Installation

- You must have [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python installed.
- You should have a coding agent that supports agent skills. Copy [skills/code-slob-cleanup](https://github.com/Jazz23/CodeSlobCleanup/tree/main/skills/code-slob-cleanup) into your agent's `skills` directory.
- During the first run, a `code-slob-cleanup.json` file will be auto-generated in your project root to manage exclusions and track edits for potential reverts.
- During the cleanup process, a temporary directory `.code-slob-tmp` will be created. It is recommended to add this to your `.gitignore` file.

### Usage

There are multiple workflows you can trigger with natural language. Below is a comprehensive list of example prompts to utilize Code Slob Cleanup:

- **"Clean up my code"** -> This will trigger the agent to crawl your entire repository looking for code slob. The agent will provide you with it's findings and ask you what you wish to refactor.
- **"Clean up code in the `src/helpers` folder"** -> The agent will only cleanup the `src/helpers` folder.
- **"Revert cleanup changes made to the 'verify_user' function"** -> The agent will look at the commit it originally modified and revert the function.
- **"Clean up global variables only"** -> The agent will skip other code slob identifiers and only look for global variables.
- **"Remove all code that is not covered by `test_e2e.py`"** -> A Python script will run your provided test script to identify all code that is not covered by the test script and remove it.

### Exclusions

See [exclusions](exclusions.md) for how to specify functions, files, or folders to ignore during the cleanup process.

### Slob Identifiers

- Cyclomatic complexity
- Lines of code (LoC)
- Global variables
- Dead code (code not covered by tests)
- Public methods/classes (that should be private)
- Too many classes in a file

## How It Works

Code Slob Cleanup identifies, tests, and applies code refactorings in a rigorous multi-stage workflow.

1.  **Scanner**: Detects "slob" candidates using static analysis (complexity, LoC) and semantic analysis using your agent.
2.  **Verifier**: Ensures that refactoring does not break functionality using [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing.
3.  **Refactor** Applies refactored code to the codebase if verification passes.

## Documentation Sections

- [**Workflow Guide**](workflow.md): A detailed walkthrough of the 5-phase cleanup lifecycle.
- [**Exclusions**](exclusions.md): How to control the cleanup scope.
- [**Scripts Reference**](scripts.md): Documentation for the various Python scripts that power the toolchain.
