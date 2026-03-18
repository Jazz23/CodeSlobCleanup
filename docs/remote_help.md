# Scripts folder Access Information

## CodeSlobCleanup/skills/code-slob-cleanup/scripts 

You can set up and access the **CodeSlobCleanup** help system on any machine using these simple steps:

### 1. Run the One-Command Setup
Run this command to install the project and generate the tool suite (replace `myproject` and `~/work/myproject` with your preferred names):

```bash
curl -LsSf https://raw.githubusercontent.com/Jazz23/CodeSlobCleanup/main/install.sh | sh -s -- myproject ~/work/myproject
```

### 2. Update your PATH
The script will output an `export PATH` command. Copy and run it exactly as printed to enable the tools in your current shell:

```bash
# Example:
export PATH="$PATH:/Users/jaisuraj/work/myproject/.codeslob/bin"
```

### 3. Access the Master Help 
Now you can view the consolidated help for an entire directory from anywhere:

```bash
myproject --help
```

### 4. Access Help for any file
Now you can view the consolidated help for a single file:

```bash
benchmark --help
```
