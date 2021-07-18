#! /usr/local/bin/python3
#

def key_struct(arg, depth=0):
  """
  """
  # print(f'key_struct({arg=}, {depth=}')
  leader = f'..' * depth
  if isinstance(arg, list):
    print(f'{leader}[{len(arg)}')
    for value in arg:
      key_struct(value, 1 + depth)
    print(f'{leader}]')
  elif isinstance(arg, dict):
    for key, value in arg.items():
      print(f'{leader}{key}')
      if isinstance(value, list) or isinstance(value, dict):
        key_struct(value, 1 + depth)
