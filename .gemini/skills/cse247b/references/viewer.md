Selection (Read-Only Viewer)
name: viewer

Objective: Create an MCP/skill that allows users to visualize results, and users can "point" to elements that become part of the feedback.
Description: For example, using Claude Code for LaTeX editing, the user can point to a paragraph and add a prompt. This creates something like:
User points to "xxxx"
// User explicitly selected "xxxx"
// User is viewing "xxxx"
Please reformat the indicated paragraph to ....
The tool should allow pointing into LaTeX-generated papers and code. Commands are "selected", "points", and "views". If nothing is selected/pointed, it just shows views. If the user clicks, it should create a point. If the user selects a text section, it should record the selected text.
