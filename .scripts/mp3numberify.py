"""
File: mp3numberify.py
Author: Greenblast
Github: https://github.com/Greenblast
Description: Numberifying mp3 files in a given path
"""

import os
import sys
from mutagen.mp3 import EasyMP3

ARGS_COUNT = 2

def organize(path):
    for f in os.listdir(path):
        if f.endswith("mp3"):
            a = EasyMP3(os.path.join(path, f))
            tracknum = str(a["tracknumber"][0].zfill(2))
            os.rename(os.path.join(path, f), os.path.join(path, tracknum + "-" + f))

def print_usage():
    """Prints usage """
    print("Usage %s filepath", sys.argv[0])

def main():
    """
    Main function
        Checks arguments and calls main logic
    """
    if sys.argv.count() == ARGS_COUNT:
        organize(sys.argv[1])
    else:
        print_usage()

if __name__ == "__main__":
    main()

