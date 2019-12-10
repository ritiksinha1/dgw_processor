#! /usr/local/bin/python3
""" How to set up a token generator that can be used to detect and return sentences of various
types.
"""

def gen(lines):
  for line in lines:
    for token in line.split():
      yield token


def youdo(gen, n):
  token_list = []
  for i in range(n):
    next_item = next(gen)
    token_list.append(next_item[::-1])
  return ' & '.join(token_list), next_item


def nowyoudo(nt, gen, n):
  print('nowyoudo\t', nt)
  for i in range(n):
    token = next(gen)
    print('nowyoudo\t', token)
  return token


test_text = ['First line here', 'Second line there', 'Third line ends the lines.']

tg = (t for t in gen(test_text))

result, next_thing = youdo(tg, 4)
print('LAST WAS', result)
print('LAST WAS', nowyoudo(next_thing, tg, 2))
while 1:
  try:
    print('I do', next(tg))
  except StopIteration:
    exit(f'ALL DONE.')
