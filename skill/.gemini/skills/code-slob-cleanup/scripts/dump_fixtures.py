# /// script
# dependencies = [
#     "hypothesis",
# ]
# ///

import os
import sys
import argparse

try:
    # Import common to configure sys.pycache_prefix
    import common
except ImportError:
    pass

from pathlib import Path



def main():

    parser = argparse.ArgumentParser(description="Concatenate and print 'original.py' files from a directory.")

    parser.add_argument("directory", help="The directory to search for 'original.py' files.")

    args = parser.parse_args()



    target_dir = Path(args.directory)



    if not target_dir.exists():

        print(f"Error: Directory not found at {target_dir.absolute()}")

        return



    print(f"--- DUMPING 'original.py' FILES FROM: {target_dir.absolute()} ---")

    

    for root, dirs, files in os.walk(target_dir):

        if "original.py" in files:

            file_path = Path(root) / "original.py"

            try:

                rel_path = file_path.relative_to(target_dir)

            except ValueError:

                rel_path = file_path

            

            print(f"\n{'='*80}")

            print(f"FILE: {rel_path}")

            print(f"{'='*80}\n")

            try:

                with open(file_path, "r", encoding="utf-8") as f:

                    print(f.read())

            except Exception as e:

                print(f"Error reading {file_path}: {e}")

            print(f"\n{'='*80}\n")





if __name__ == "__main__":
    main()
