#! /usr/local/bin/python3

from io import IOBase
import tokenize

headers = ['This is the first header line', 'This is a Proxy-Advice line', 'This has 3:4.5 numbers']


class Lines(IOBase):
  def open(this, lines):
    this.lines = lines

  def readline(this, size=-1):
    for line in this.lines:
      if size != -1:
        yield line
      else:
        yield line[0:size]


izer = Lines.open(headers)
for l in izer():
  print(l)
