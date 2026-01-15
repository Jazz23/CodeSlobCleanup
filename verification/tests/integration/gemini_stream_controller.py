import subprocess
import sys
import json
import argparse
import signal
import select
import os

def cleanup_process(process):
    """Safely terminates the subprocess."""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

def main():
    parser = argparse.ArgumentParser(description="Stream Gemini output and control process.")
    parser.add_argument(
        "prompt", 
        help="The prompt to send to Gemini"
    )
    args = parser.parse_args()

    command = [
        "gemini",
        "-p", args.prompt,
        "--model", "gemini-3-flash-preview",
        "--output-format", "stream-json",
        "--yolo"
    ]

    print(f"Executing: {' '.join(command)}")
    
    # Start the process. 
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False, # Use bytes for more reliable non-blocking reads
        bufsize=0,
        shell=False
    )

    # Set up signal handlers
    def signal_handler(sig, frame):
        cleanup_process(process)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Use select to monitor stdout, stderr, and stdin
    inputs = [process.stdout, process.stderr, sys.stdin]
    
    try:
        while inputs:
            # Wait for any of the streams to be ready for reading
            readable, _, _ = select.select(inputs, [], [], 0.1)
            
            for r in readable:
                if r is sys.stdin:
                    # Any input detected kills the process
                    try:
                        os.read(sys.stdin.fileno(), 1024)
                    except EOFError:
                        pass
                    print("\nInput detected. Killing process...")
                    cleanup_process(process)
                    return
                else:
                    # Read from stdout or stderr
                    data = os.read(r.fileno(), 4096)
                    if not data:
                        inputs.remove(r)
                    else:
                        output = data.decode('utf-8', errors='replace')
                        if r is process.stderr:
                            print(f"[ERROR] {output}", end="")
                        else:
                            print(output, end="")
                        sys.stdout.flush()
            
            # If the process has exited, we should stop listening to stdin
            if process.poll() is not None:
                if sys.stdin in inputs:
                    inputs.remove(sys.stdin)
                # If we've also finished reading stdout and stderr, we can exit the loop
                if process.stdout not in inputs and process.stderr not in inputs:
                    break

        process.wait()
        if process.returncode == 0:
            print("\nProcess completed successfully.")
        elif process.returncode in (-15, -9, 143, 137):
            print("\nProcess was terminated.")
        else:
            print(f"\nProcess exited with code {process.returncode}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        cleanup_process(process)
    finally:
        cleanup_process(process)

if __name__ == "__main__":
    main()
