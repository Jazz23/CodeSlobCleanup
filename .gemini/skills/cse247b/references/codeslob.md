Code Slob Removal (Python)
name: codeslob
Objective: Coding agents can add "slob" (increase technical debt). Leverage coverage and integration testing to remove useless functions and automate code refactoring (too long/complex, private vs. public, etc.).
Description: Create a set of scripts/prompts to guide coding agents (MCP or skills) to refactor Python code to reduce technical debt.
There are 4 main components:
Identify targets for optimization (this can be metrics like LoC or cyclomatic complexity for functions or many other things)
Mostly compiler driven, but LLM/Coding Agent could also check
Transform the code optimization LLM, but can be also compiler assisted
Check that the transformation did not introduce a bug
https://hypothesis.readthedocs.io/en/latest/
https://github.com/google/atheris
Get it work as an Coding Agent Skill (should work in claude code + codex + ???)
