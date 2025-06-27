# -*- coding: utf-8 -*-
"""
BehaveX - BDD testing library based on Behave
"""
# pylint: disable=W0403, R0903
# __future__ and six have been added in order to maintain compatibility
from __future__ import absolute_import, print_function

from PIL import Image


def binary_array_to_hex(arr):
    """convert from array to hex"""
    hex_ = 0
    sub = []
    flat_arr = [item for sublist in arr for item in sublist]
    for i, vect in enumerate(flat_arr):
        if vect:
            hex_ += 2 ** (i % 8)
        if (i % 8) == 7:
            sub.append(hex(hex_)[2:].rjust(2, '0'))
            hex_ = 0
    return ''.join(sub)


def binary_array_to_int(arr):
    """convert from binary array to int"""
    return sum([2 ** (i % 8) for i, v in enumerate(arr.flatten()) if v])


class ImageHash(object):
    """
    Hash encapsulation. Can be used for dictionary keys and comparisons.
    """

    def __init__(self, binary_array):
        self.hash = binary_array

    def __str__(self):
        return binary_array_to_hex(self.hash)

    def __repr__(self):
        return repr(self.hash)

    def __sub__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError('unsupported operand type(s) for -')
        if len(self.hash) != len(other.hash) or len(self.hash[0]) != len(other.hash[0]):
            raise ValueError(
                'ImageHashes must be of the same shape!',
                (len(self.hash), len(self.hash[0])),
                (len(other.hash), len(other.hash[0])),
            )
        flat_self = [item for sublist in self.hash for item in sublist]
        flat_other = [item for sublist in other.hash for item in sublist]
        return sum(1 for x, y in zip(flat_self, flat_other) if x != y)

    def __eq__(self, other):
        """Function especial eq"""
        if not isinstance(other, self.__class__):
            return False
        return self.hash == other.hash

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return binary_array_to_int(self.hash)


def dhash(image, hash_size=8):
    """
    Difference Hash computation.
    following http://www.hackerfactor.com/blog/index.php?/archives/
    529-Kind-of-Like-That.html
    @image must be a PIL instance.
    """
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels_data = list(image.getdata())
    pixels = []
    for row_num in range(hash_size):
        row = []
        for col_num in range(hash_size + 1):
            row.append(pixels_data[row_num * (hash_size + 1) + col_num])
        pixels.append(row)

    diff = []
    for row_num in range(hash_size):
        diff_row = []
        for col_num in range(hash_size):
            diff_row.append(pixels[row_num][col_num + 1] > pixels[row_num][col_num])
        diff.append(diff_row)
    return ImageHash(diff)


__dir__ = [ImageHash]
