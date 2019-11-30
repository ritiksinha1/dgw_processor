#! /usr/local/bin/python3

import inspect

import sys
from antlr4 import *
from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener


class MinresListener(ReqBlockListener):
  def enterMinres(self, ctx):
    print(f'At least {ctx.NUMBER()} credits must be completed in residency.')

  def enterNumcredits(self, ctx):
    print(f'This major requires {ctx.NUMBER()} credits.')


def main(argv):
    input_stream = FileStream(argv[1])
    lexer = ReqBlockLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = ReqBlockParser(stream)
    tree = parser.req_block()
    minres = MinresListener()
    walker = ParseTreeWalker()
    walker.walk(minres, tree)


if __name__ == '__main__':
    main(sys.argv)
