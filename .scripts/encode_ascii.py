#!/usr/bin/python
"""
Encode a given number or a packet to it's modbus ascii payload representation
Usages:
encode_ascii.py <numer_to_encode>
encode_ascii.py -f <full_payload_to_encode>
"""
import sys
import re

def set_parity(hex_char):
    """
    Setting the parity bit in a number if needed
    """
    number_representation = int(hex_char, 16)

    # If the number of set bits is odd
    if bin(number_representation).count('1') % 2 != 0:
        # Set the MSB to 1
        number_representation |= (1<<7)

    return format(number_representation, 'X').rjust(2, '0')

def parse_number(hex_string):
    """
    Encoding a hex number to it's ascii representation
    """
    encoded_hex_chars_with_parity = [set_parity(format(ord(x), 'X')) for x in hex_string]
    return "".join(encoded_hex_chars_with_parity)

def prepare_hex_string(number, base=10):
    """
    Gets an int number, and returns the hex representation with even length padded to the left with zeroes
    """
    int_number = int(number, base)
    hex_number = format(int_number, 'X')

    # Takes the string and pads to the left to make sure the number of characters is even
    justify_hex_number = hex_number.rjust((len(hex_number) % 2) + len(hex_number), '0')

    return justify_hex_number

def append_checksum(hex_string):
    """
    Appends the checksum to the string.
    The checksum is the last 2 bytes, of the negative sum of the bytes
    """
    list_of_bytes = re.findall(r'.{1,2}', hex_string)
    #list_of_ints = map(lambda x: int(x, 16), list_of_bytes)
    list_of_ints = [int(x, 16) for x in list_of_bytes]
    negative_sum_of_chars = -sum(list_of_ints)
    checksum_value = format(negative_sum_of_chars & 0xFF, 'X')

    string_with_checksum = hex_string + checksum_value
    return string_with_checksum


def main():
    """
    Main function
    """
    if sys.argv[1] == '-f':
        print parse_number(":" + append_checksum(prepare_hex_string(sys.argv[2])) + "\x0d\x0a")
    elif sys.argv[1] == '-hf':
        print parse_number(":" + append_checksum(prepare_hex_string(sys.argv[2], 16)) + "\x0d\x0a")
    else:
        print parse_number(prepare_hex_string(sys.argv[1]))



if __name__ == "__main__":
    main()

