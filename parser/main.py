#! /usr/local/bin/python3

import sys
from antlr4 import *
from BLOCKLexer import BLOCKLexer
from BLOCKParser import BLOCKParser


def main(argv):
    input_stream = FileStream(argv[1])
    lexer = BLOCKLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = BLOCKParser(stream)
    tree = parser.req_block()


if __name__ == '__main__':
    main(sys.argv)
