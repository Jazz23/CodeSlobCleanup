---
name: cse247b-skill
description: Updates a user's overview.md and task markdown files in their respective project directory within the cse247b_reports_w26 repository. Use when the user mentions "overview" or "task".
---

# CSE247B Class Assistant Skill

This skill is designed to assist students in the CSE247B class with their project reporting and task management.

## Context Resolution (always perform this first)
1.  **Identify the Project**: The user will have provided two main context directories:
    *   A private project directory (containing their source code).
    *   The `cse247b_reports_w26` master repository.
2.  **Locate Report Folder**: Find the subdirectory in `cse247b_reports_w26` that corresponds to the user's private project directory name. This is the **Target Report Directory**.
3.  **Load Domain Context**: Look for a corresponding markdown file in the `references` folder of this skill's directory (e.g., if the project is `asm2cpp` or similar, look for `references/asm2cpp.md`). Use the content of this file to understand the project's goals and domain when generating content.

## Workflows

### 1. Overview Maintenance (always perform this workflow after completing one of the other workflows)
*   **Action**: Check `overview.md` in the **Target Report Directory**.
*   **Condition**: If the file is empty, sparse, or if a new task has just been generated.
*   **Resolution**:
    *   Perform deep research on the project topic (utilizing the `references` file and general knowledge). Search the internet for relevant information.
    *   Write or update `overview.md` with a comprehensive summary of the project and its architectural approach.
    *   **Always** trigger this update immediately after generating new tasks.

### 2. Task Status Management (conditionally perform this workflow)
*   **Trigger**: User indicates a task is finished (e.g., "Task succeeded", "Task failed", "I'm done with this task").
*   **Action**:
    1.  **Identify Active Task**: Locate the active task file (usually `task.md`, or the specific file mentioned).
    2.  **Determine Destination**:
        *   If success: `completed/` directory.
        *   If failure: `failed/` directory.
    3.  **Remove Empty task1.md**:
        *   If the target folder contains an *empty* task1.md, remove it.
    4.  **Calculate Next Sequence Number**:
        *   Scan both `completed/` and `failed/` directories for files matching `taskN.md`.
        *   Find the highest number `N`. The new sequence number is `N + 1`.
        *   *Example*: If `completed/task1.md` and `failed/task2.md` exist, the new file will be `task3.md`.
        *   If the task is `taska.md` for example, the new file will be `taska1.md`
    5.  **Move and Rename**: Move the active task file to the destination directory and rename it to `task{N+1}.md` (e.g., `completed/task3.md`).
    6.  **Generate Next Task**:
        *   Create a new `task.md` file in the root of the **Target Report Directory**. If the task they completed/failed ends in a letter, reuse that letter when creating the new file.
        *   Fill it with the immediate next step for the project, based on the `overview.md` and the result of the previous task.

### 3. Task Generation (conditionally perform this workflow)
*   **Trigger**: User says something like "Create an n week long task" or "Create n week long tasks for a group of 2".
*   **Action**:
    1.  Determine if there is a `task.md` file in the **Target Report Directory** that starts with "SAMPLE TASK". If so, delete this file.
    2.  Analyze the current state of the project and the `overview.md`.
    3.  Perform deep research (search the internet if necessary) to figure out the next logical steps of the project.
    4.  Generate n new task files (depending on group size) in the **Target Report Directory** root. E.g. `taska.md` and `taskb.md` for a group size of 2. If only a team of one (or not group size is mentioned), omit the letter and just put `task.md`.
    5.  Fill these files with distinct, relevant, and substantial work items suitable for the desired number of weeks of effort for n separate students. Ensure the tasks advance the project goals defined in the reference material.