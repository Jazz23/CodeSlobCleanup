import subprocess
import sys
import json

def main():
    command = [
        "gemini",
        "-p", "Count to 6. Wait for 3 seconds between numbers. Output each number.",
        "--model", "gemini-3-flash-preview",
        "--output-format", "stream-json",
        "--yolo"
    ]

    print(f"Executing: {' '.join(command)}")
    
    # Start the process
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        shell=True
    )

    try:
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            # Display the output chunk
            print(f"\nReceived Output:\n{line.strip()}")
            
            # Ask the user
            try:
                choice = input("\n[c]ontinue or [k]ill process? ").strip().lower()
            except EOFError:
                print("\nEOF detected, defaulting to 'c'...")
                choice = 'c'
            
            if choice == 'k':
                print("Killing process...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                print("Process terminated.")
                return

        # Check if process ended on its own
        process.wait()
        if process.returncode == 0:
            print("\nProcess completed successfully.")
        else:
            stderr_output = process.stderr.read()
            print(f"\nProcess exited with code {process.returncode}")
            if stderr_output:
                print(f"Error output:\n{stderr_output}")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Killing process...")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"An error occurred: {e}")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
