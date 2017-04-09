#!/usr/bin/python
"""
Translates and prints ascii to rtu modbus packet
"""

import sys
import re

def main():
    """
    Main function
    """

    crypt = sys.argv[1]
    splitted_chars = re.findall(r'.{1,2}', crypt)
    splitted = [int(x, 16) for x  in splitted_chars]
    list_chars = []
    for index, char in enumerate(splitted):
        # Appending the char with the 8 bit turned off
        validated_char = char & 127

        # If the char is not in the boundary
        if validated_char > 0x48 or validated_char < 0x30:
            if validated_char != 0xa and validated_char != 0xd:
                raise Exception("The given char at index {} is not valid, char is {}".format(index, char))


        list_chars.append(chr(validated_char))


    print ''.join(list_chars)

if __name__ == "__main__":
    main()
