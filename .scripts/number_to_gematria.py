#!/bin/python3

import re
import sys
# -*- coding: utf-8 -*-
# from os import path
# import io
# import yaml
# import json

# PROJ_PATH = path.sep.join(__file__.split(path.sep)[:-2])
# DATA_PATH = path.join(
#     PROJ_PATH, 'hebrew-special-numbers-default.yml')
# specialnumbers = yaml.safe_load(io.open(DATA_PATH, encoding='utf8'))

# specialnumbers = {
#     "version":
#     {
#         "styles":
#         {
#             "default": "2.0.0"
#         },
#         "order":
#         []
#     },
#     "separators":
#     {
#         "geresh": "׳",
#         "gershayim": "״"
#     },
#     "numerals":
#     {
#         "1": u"א",
#         "2": u"ב",
#         "3": u"ג",
#         "4": u"ד",
#         "5": u"ה",
#         "6": u"ו",
#         "7": u"ז",
#         "8": u"ח",
#         "9": u"ט",
#         "10": u"י",
#         "20": u"כ",
#         "30": u"ל",
#         "40": u"מ",
#         "50": u"נ",
#         "60": u"ס",
#         "70": u"ע",
#         "80": u"פ",
#         "90": u"צ",
#         "100": u"ק",
#         "200": u"ר",
#         "300": u"ש",
#         "400": u"ת",
#         "500": u"תק",
#         "600": u"תר",
#         "700": u"תש",
#         "800": u"תת",
#         "900": u"תתק"
#     },
#     "specials":
#     {
#         "0": "0",
#         "15": u"טו",
#         "16": u"טז",
#         "115": u"קטו",
#         "116": u"קטז",
#         "215": u"רטו",
#         "216": u"רטז",
#         "270": u"ער",
#         "272": u"ערב",
#         "274": u"עדר",
#         "275": u"ערה",
#         "298": u"רחצ",
#         "304": u"דש",
#         "315": u"שטו",
#         "316": u"שטז",
#         "344": u"שדמ",
#         "415": u"תטו",
#         "416": u"תטז",
#         "515": u"תקטו",
#         "516": u"תקטז",
#         "615": u"תרטו",
#         "616": u"תרטז",
#         "670": u"עתר",
#         "672": u"תערב",
#         "674": u"עדרת",
#         "698": u"תרחצ",
#         "715": u"תשטו",
#         "716": u"תשטז",
#         "744": u"תשדמ",
#         "815": u"תתטו",
#         "816": u"תתטז",
#         "915": u"תתקטו",
#         "916": u"תתקטז"
#     }
# }


specialnumbers = {
    "version":
    {
        "styles":
        {
            "default": "2.0.0"
        },
        "order":
        []
    },
    "separators":
    {
        "geresh": "׳",
        "gershayim": "״"
    },
    "numerals":
    {
        "1": u"Alef",
        "2": u"Bet",
        "3": u"Gimel",
        "4": u"Dalet",
        "5": u"He",
        "6": u"Vav",
        "7": u"Zain",
        "8": u"Het",
        "9": u"Tet",
        "10": u"Yood",
        "20": u"Kaf",
        "30": u"Lamed",
        "40": u"Mem",
        "50": u"Noon",
        "60": u"Samech",
        "70": u"Ain",
        "80": u"Pe",
        "90": u"Tsadi",
        "100": u"Koof",
        "200": u"Resh",
        "300": u"Shin",
        "400": u"Tav",
        "500": u"Tav Koof",
        "600": u"Tav Resh",
        "700": u"Tav Shin",
        "800": u"Tav Tav",
        "900": u"Tav Tav Koof"
    },
    "specials":
    {
        "0": "0",
        "15": u"Tet Vav",
        "16": u"Tet Zain",
        "115": u"Koof Tet Vav",
        "116": u"Koof Tet Zain",
        "215": u"Resh Tet Vav",
        "216": u"Resh Tet Zain",
        "270": u"Resh Ain",
        "272": u"Resh Ain Bet",
        "274": u"Resh Ain Dalet",
        "275": u"Resh Ain He",
        "298": u"Resh Tsadi Het",
        "304": u"Shin Dalet",
        "315": u"Shin Tet Vav",
        "316": u"Shin Tet Zain",
        "344": u"Shin Mem Dalet",
        "415": u"Tav Tet Vav",
        "416": u"Tav Tet Zain",
        "515": u"Tav Koof Tet Vav",
        "516": u"Tav Koof Tet Zain",
        "615": u"Tav Resh Tet Vav",
        "616": u"Tav Resh Tet Zain",
        "670": u"Tav Resh Ain",
        "672": u"Tav Resh Ain Bet",
        "674": u"Tav Resh Ain Dalet",
        "698": u"Tav Resh Tsadi Het",
        "715": u"Tav Shin Tet Vav",
        "716": u"Tav Shin Tet Zain",
        "744": u"Tav Shin Mem Dalet",
        "815": u"Tav Tav Tet Vav",
        "816": u"Tav Tav Tet Zain",
        "915": u"Tav Tav Koof Tet Vav",
        "916": u"Tav Tav Koof Tet Zain"
    }
}

MAP = (
    (1, u'א'),
    (2, u'ב'),
    (3, u'ג'),
    (4, u'ד'),
    (5, u'ה'),
    (6, u'ו'),
    (7, u'ז'),
    (8, u'ח'),
    (9, u'ט'),
    (10, u'י'),
    (20, u'כ'),
    (30, u'ל'),
    (40, u'מ'),
    (50, u'נ'),
    (60, u'ס'),
    (70, u'ע'),
    (80, u'פ'),
    (90, u'צ'),
    (100, u'ק'),
    (200, u'ר'),
    (300, u'ש'),
    (400, u'ת'),
    (500, u'ך'),
    (600, u'ם'),
    (700, u'ן'),
    (800, u'ף'),
    (900, u'ץ')
)
MAP_DICT = dict([(k, v) for v, k in MAP])
GERESH = set(("'", '׳'))


def gematria_to_int(string):
    res = 0
    for i, char in enumerate(string):
        if char in GERESH and i < len(string)-1:
            res *= 1000
        if char in MAP_DICT:
            res += MAP_DICT[char]
    return res


# adapted from hebrew-special-numbers documentation
def int_to_gematria(num, gershayim=True):
    """convert integers between 1 an 999 to Hebrew numerals.

           - set gershayim flag to False to ommit gershayim
    """
    # 1. Lookup in specials
    if str(num) in specialnumbers['specials']:
        retval = specialnumbers['specials'][str(num)]
        return _add_gershayim(retval) if gershayim else retval

    # 2. Generate numeral normally
    parts = []
    rest = str(num)
    while rest:
        digit = int(rest[0])
        rest = rest[1:]
        if digit == 0:
            continue
        power = 10 ** len(rest)
        parts.append(specialnumbers['numerals'][str(power * digit)])
    retval = ' '.join(parts).strip()
    # 3. Add gershayim
    return _add_gershayim(retval) if gershayim else retval


def _add_gershayim(s):
    if len(s) == 1:
        s += specialnumbers['separators']['geresh']
    else:
        s = ' '.join([
            s[:-1],
            specialnumbers['separators']['gershayim'],
            s[-1:]
        ]).strip()
    return s


def gematriya(num):
    return int_to_gematria(num, gershayim=False)


def translate_with_gematria(input_line):
    # Taking each number in a string and transform it to the gematriya form
    numbers = re.findall(r'\d+', input_line)
    for number in numbers:
        result = gematriya(number)
        input_line = input_line.replace(number, result)
    return input_line


def main():
    # take a string as an input and print the result
    if sys.argv[1:]:
        # print(''.join(sys.argv[1:]))
        transformed_title = translate_with_gematria(''.join(sys.argv[1:]))
        # print(f'translated: {transformed_title}')
        return transformed_title

    raise ValueError('Please provide a string to translate')


if __name__ == "__main__":
    result = main()
    print(result)

# print(translate_with_gematria("Daf Yomi -- Baba Metzia 60"))
# print(translate_with_gematria("Daf Yomi -- 613"))
# print(translate_with_gematria("Daf Yomi -- 18"))
# print(translate_with_gematria("Daf Yomi -- 17"))
# print(translate_with_gematria("Daf Yomi -- 16"))
# print(translate_with_gematria("Daf Yomi -- 15"))
# print(translate_with_gematria("Daf Yomi -- 117"))
# print(translate_with_gematria("Daf Yomi -- 116"))
# print(translate_with_gematria("Daf Yomi -- 115"))
# print(translate_with_gematria("Daf Yomi -- 123"))

# print(gematriya(613))
# print(gematriya(18))
# print(gematriya(17))
# print(gematriya(16))
# print(gematriya(15))
# print(gematriya(117))
# print(gematriya(116))
# print(gematriya(115))
# print(gematriya(123))
#
