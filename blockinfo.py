#! /usr/local/bin/python3

import sys


def ifs(v: any):
  """ Convert a value, v, from str to a float, int, or leave it as a str
  """
  if isinstance(v, list):
    return v
  try:
    fv = iv = None
    fv = float(v)
    iv = int(v)
    if iv == fv:
      fv = int(fv)
  except ValueError:
    pass
  if fv:
    v = fv
  return v


class BlockInfo(dict):
  """ Information about a program or subprogram, which will become part of the context list of a
      requirement by the course_mapper app. Information comes from:
        * CF acad_plan and acad_subplan tables
        * DGW dap_requirement_block metadata, if available
        * Scribe block header objects, if available

      plan_info:
       'plan'. 'plan_type', 'plan_name', 'plan_cip_code', 'plan_effective_date',
       'plan_enrollment', 'subplans',
      subplan_info:
       'subplan', 'subplan_type', 'subplan_name', 'subplan_cip_code',
       'subplan_effective_date', 'subplan_enrollment', 'plans',
  """
  _valid_keys = ['institution', 'plan_info', 'subplan_info',
                 'requirement_id', 'block_type', 'block_value', 'block_title', 'catalog_years',
                 'class_credits', 'min_residency', 'min_grade', 'min_gpa', 'max_transfer',
                 'max_classes', 'max_credits']

  def __init__(self, **kwargs):
    """ Capture whatever arguments are passed.
    """
    # self._blockinfo = {}
    for k, v in kwargs.items():
      if k in BlockInfo._valid_keys:
        if isinstance(v, str):
          v = ifs(v)
        if isinstance(v, str):
          exec(f'self.{k} = "{v}"')
        else:
          exec(f'self.{k} = {v}')
      else:
        raise ValueError(f'“{k}” is not a valid BlockInfo key')

  def add_items(self, items: dict):
    """ Verify that each key in dict is valid, and if all are valid add each one, with its value, to
        the _blockinfo dict. If a key already exists, replace its value silently.
        Returns the updated dict.
    """
    for k, v in items.items():
      if k in self._valid_keys:
        v = ifs(v)
        if isinstance(v, str):
          exec(f'self.{k} = "{v}"')
        else:
          exec(f'self.{k} = {v}')
      else:
        raise ValueError(f'“{k}” is not a valid BlockInfo key')
    return self.__dict__

  def _asdict(self):
    """ Returns the dict.
    """
    return self.__dict__


if __name__ == '__main__':
  """ Accept list of name=value strings on command line and pass them to the BlockInfo constructor.
      Show the resulting BlockInfo dict, then read additional name=value strings, and add them to
      the dict.
  """
  args = {}
  for arg in sys.argv[1:]:
    k, v = arg.split('=')
    # key has to be one of the _valid_keys
    # value can be int, float, str, or list
    args[k] = ifs(v)
  blinfo = BlockInfo(**args)
  print(blinfo._asdict())

  while True:
    print('More? ', end='')
    sys.stdout.flush()
    line = sys.stdin.readline()
    if len(line.strip()) == 0 or line[0] in 'QqEe':
      exit()
    if '=' in line:
      args = {}
      for arg in line.strip().split(' '):
        k, v = arg.split('=')
        args[k] = v
      print(blinfo.add_items(args))
    else:
      for key in line.strip().split(' '):
        print(f'{key}: {blinfo._asdict()[key]}')
