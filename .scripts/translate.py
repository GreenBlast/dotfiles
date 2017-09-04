#!/usr/bin/python3
"""
Encodes a given file with a given byte
WIP
"""
from __future__ import print_function
import sys

ARGS_COUNT = 4

def encode(infile, outfile, byte_to_encode):
    """
    Encoding using the byte
    """
    with open(infile, 'rb') as infile_handle:
        with open(outfile, 'wb') as outfile_handle:
            pre_encoded_buffer = infile_handle.readlines()
            for character in pre_encoded_buffer:
                xored_chr = chr(ord(character ^ byte_to_encode))
                print ("original character: {}, xored character:{}".format(character, xored_chr))
                outfile_handle.write(xored_chr)

def print_usage():
    """Prints usage """
    print ("Usage {} infile outfile byte_to_encode")

def main():
    """
    Main function:
        Checks arguments and calls main logic
    """
    if sys.argv.count() == ARGS_COUNT:
        encode(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print_usage()

if __name__ == "__main__":
    main()
