#! /usr/local/bin/python3
""" Utilities for processing header constructs by the course_mapper.
"""

_dict = {'not-yet': True}


# letter_grade()
# -------------------------------------------------------------------------------------------------
def letter_grade(grade_point: float) -> str:
  """ Convert a passing grade_point value to a passing letter grade.
      Treat anything less than 1.0 as "Any" passing grade, and anything above 4.3 as "A+"
        GPA Letter
        4.3    A+
        4.0    A
        3.7    A-
        3.3    B+
        3.0    B
        2.7    B-
        2.3    C+
        2.0    C
        1.7    C-
        1.3    D+
        1.0    D
        0.7    D- => "Any"
  """
  if grade_point < 1.0:
    return 'Any'
  else:
    letter_index, suffix_index = divmod((10 * grade_point) - 7, 10)
  letter = ['D', 'C', 'B', 'A'][min(int(letter_index), 3)]
  suffix = ['-', '', '+'][min(int(suffix_index / 3), 2)]
  return letter + suffix


# header_classcredit()
# -------------------------------------------------------------------------------------------------
def header_classcredit(value: dict, do_proxyadvice: bool) -> dict:
  """
      This is the “total credits and/or total classes” part of the header, which we are calling
      “requirement size”. Conditionals my cause multiple instances to be specified, which is why
      this value is maintained as a list, which may also contain interspersed conditionals.
  """
  return_dict = dict()

  # There's always a label key, but the value may be empty
  if label_str := value['label']:
    return_dict['label'] = label_str

  try:
    # There might or might-not be proxy-advice
    proxy_advice = value['proxy_advice']
    if do_proxyadvice:
      return_dict['proxy_advice'] = value['proxy_advice']
  except KeyError:
    # No proxy-advice (normal))
    pass

  return_dict['is_pseudo'] = value['is_pseudo']

  min_classes = None if value['min_classes'] is None else int(value['min_classes'])
  min_credits = None if value['min_credits'] is None else float(value['min_credits'])
  max_classes = None if value['max_classes'] is None else int(value['max_classes'])
  max_credits = None if value['max_credits'] is None else float(value['max_credits'])

  classes_part = ''
  if min_classes or max_classes:
    assert min_classes and max_classes, f'{min_classes=} {max_classes=}'
    if min_classes == max_classes:
      classes_part = (f'{max_classes} classes')
    else:
      classes_part = (f'{min_classes}-{max_classes} classes')

  credits_part = ''
  if min_credits or max_credits:
    assert min_credits and max_credits, f'{min_credits=} {max_credits=}'
    if min_credits == max_credits:
      credits_part = (f'{max_credits:.1f} credits')
    else:
      credits_part = (f'{min_credits:.1f}-{max_credits:.1f} credits')

  if classes_part and credits_part:
    conjunction = value['conjunction']
    assert conjunction is not None, f'{classes_part=} {credits_part=}'
    return_dict['size'] = f'{classes_part} {conjunction} {credits_part}'
  elif classes_part or credits_part:
    # One of them is blank
    return_dict['size'] = classes_part + credits_part
  else:
    exit('Malformed header_class_credit')

  return return_dict


# header_maxtransfer()
# -------------------------------------------------------------------------------------------------
def header_maxtransfer(value: dict) -> dict:
  """
  """
  mt_dict = {'label': value['label']}

  number = float(value['maxtransfer']['number'])
  class_or_credit = value['maxtransfer']['class_or_credit']
  if class_or_credit == 'credit':
    mt_dict['limit'] = f'{number:3.1f} credits'
  else:
    suffix = '' if int(number) == 1 else 'es'
    mt_dict['limit'] = f'{int(number):3} class{suffix}'
  try:
    mt_dict['transfer_types'] = value['transfer_types']
  except KeyError:
    pass

  return mt_dict


# header_minres()
# -------------------------------------------------------------------------------------------------
def header_minres(value: dict) -> dict:
  """ Return a dict with the number of classes or credits (it's always credits, in practice) plus
      the label if there is one.
  """
  min_classes = value['minres']['min_classes']
  min_credits = value['minres']['min_credits']
  # There must be a better way to do an xor check ...
  match (min_classes, min_credits):
    case [classes, None]:
      minres_str = f'{int(classes)} classes'
    case [None, credits]:
      minres_str = f'{float(credits):.1f} credits'
    case _:
      print(f'Invalid minres {value}', file=sys.stderr)

  label_str = value['label']

  return {'minres': minres_str, 'label': label_str}


# header_mingpa()
# -------------------------------------------------------------------------------------------------
def header_mingpa(value: dict) -> dict:
  """
  """
  mingpa_dict = value['mingpa']
  mingpa_dict['label'] = value['label']

  return mingpa_dict


# header_mingrade()
# -------------------------------------------------------------------------------------------------
def header_mingrade(value: dict) -> dict:
  """
  """
  mingrade_dict = value['mingrade']
  mingrade_dict['letter_grade'] = letter_grade(float(value['mingrade']['number']))
  mingrade_dict['label'] = value['label']

  return mingrade_dict


# header_maxclass()
# -------------------------------------------------------------------------------------------------
def header_maxclass(value: dict) -> dict:
  """
  """
  return _dict


# header_maxcredit()
# -------------------------------------------------------------------------------------------------
def header_maxcredit(value: dict) -> dict:
  """
  """
  return _dict


# header_maxpassfail()
# -------------------------------------------------------------------------------------------------
def header_maxpassfail(value: dict) -> dict:
  """
  """
  return _dict


# header_maxperdisc()
# -------------------------------------------------------------------------------------------------
def header_maxperdisc(value: dict) -> dict:
  """
  """
  return _dict


# header_minclass()
# -------------------------------------------------------------------------------------------------
def header_minclass(value: dict) -> dict:
  """
  """
  return _dict


# header_mincredit()
# -------------------------------------------------------------------------------------------------
def header_mincredit(value: dict) -> dict:
  """
  """
  return _dict


# header_minperdisc()
# -------------------------------------------------------------------------------------------------
def header_minperdisc(value: dict) -> dict:
  """
  """
  return _dict


# header_proxyadvice()
# -------------------------------------------------------------------------------------------------
def header_proxyadvice(value: dict) -> dict:
  """
  """
  return _dict
