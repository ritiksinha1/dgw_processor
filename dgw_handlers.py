#! /usr/local/bin/python3
""" These are the handlers for all the head and body rule types.
      head        :
            ( class_credit_head
            | if_then
            | lastres
            | maxclass
            | maxcredit
            | maxpassfail
            | maxperdisc
            | maxterm
            | maxtransfer
            | mingrade
            | minclass
            | mincredit
            | mingpa
            | minperdisc
            | minres
            | optional
            | remark
            | share
            | standalone
            | subset
            | under
            )*
            ;
body        :
            ( block
            | blocktype
            | class_credit_body
            | copy_rules
            | group
            | if_then
            | label
            | noncourse
            | remark
            | rule_complete
            | subset
            )*
            ;
$ ack -v '/' debug | awk '{ print $3, $4 }'|sort|uniq
  Head: Class_credit_head
  Head: If_then
  Head: Lastres
  Head: Maxclass
  Head: Maxcredit
  Head: Maxpassfail
  Head: Maxperdisc
  Head: Maxtransfer
  Head: Minclass
  Head: Mincredit
  Head: Mingpa
  Head: Mingrade
  Head: Minperdisc
  Head: Minres
  Head: Remark
  Head: Share
  Head: Subset

  Body: Block
  Body: Blocktype
  Body: Class_credit_body
  Body: Copy_rules
  Body: Group
  Body: If_then
  Body: Noncourse
  Body: Remark
  Body: Subset
"""

from dgw_utils import class_name,\
    class_or_credit


# Handlers
# =================================================================================================
def class_credit_head(ctx):
  """
class_credit_head   : (num_classes | num_credits)
                      (logical_op (num_classes | num_credits))?
                      (IS? pseudo | header_tag | tag)*
                      display* label?;
num_classes         : NUMBER CLASS allow_clause?;
num_credits         : NUMBER CREDIT allow_clause?;

"""

  if ctx.num_classes():
    assert len(ctx.num_classes()) == 1
    number = ctx.num_classes()[0].NUMBER().getText().strip()
    if ':' in number:
      min_classes, max_classes = number.replace(' ', '').split(':')
    else:
      min_classes = max_classes = number
    if ctx.num_classes()[0].allow_clause():
      allow_classes = ctx.num_classes()[0].allow_clause().NUMBER().getText().strip()
    else:
      allow_classes = None
  else:
    min_classes = max_classes = allow_classes = None

  if ctx.num_credits():
    assert len(ctx.num_credits()) == 1
    number = ctx.num_credits()[0].NUMBER().getText().strip()
    if ':' in number:
      min_credits, max_credits = number.replace(' ', '').split(':')
    else:
      min_credits = max_credits = number
    if ctx.num_credits()[0].allow_clause():
      allow_credits = ctx.num_credits()[0].allow_clause().NUMBER().getText().strip()
    else:
     allow_credits = None
  else:
    min_credits = max_credits = allow_credits = None

  if ctx.logical_op():
    conjunction = ctx.logical_op().getText()
  else:
    conjunction = None
  assert conjunction is None and (not min_classes or not min_credits) or\
         conjunction is not None and not(min_classes and min_credits), 'Bad class_credit_head'

  is_pseudo = True if ctx.pseudo() else False

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    display_text = display_text.strip()
  else:
    display_text = None

  if ctx.label():
    label_text = ctx.label()
  else:
    label_text = None

  return {'tag': 'class_credit_head',
          'min_classes': min_classes,
          'max_classes': max_classes,
          'allow_classes': allow_classes,
          'min_credits': min_credits,
          'max_credits': max_credits,
          'allow_credits': allow_credits,
          'conjunction': conjunction,
          'is_pseudo': is_pseudo,
          'display': display_text,
          'label': label_text}


def if_then_head(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def lastres(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def maxclass(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def maxcredit(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def maxpassfail(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def maxperdisc(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def maxterm(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def maxtransfer(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def mingrade(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def minclass(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def mincredit(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def mingpa(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def minperdisc(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def minres(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def optional(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def remark(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def share(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def standalone(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def subset_head(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def under(ctx):
  print(class_name(ctx), 'not implemented yet')
  return{}


def block(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def blocktype(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def class_credit_body(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def copy_rules(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def group(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def if_then_body(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def noncourse(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def remark(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def rule_complete(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


def subset_body(ctx):
  print(class_name(ctx), 'not implemented yet')
  return {}


# Dispatch Tables
# =================================================================================================
""" There are two in case If-then and Share need to be handled differently in Head and Body.
"""
dispatch_head = {
    'class_credit_head': class_credit_head,
    'if_then': if_then_head,
    'lastres': lastres,
    'maxclass': maxclass,
    'maxcredit': maxcredit,
    'maxpassfail': maxpassfail,
    'maxperdisc': maxperdisc,
    'maxterm': maxterm,
    'maxtransfer': maxtransfer,
    'mingrade': mingrade,
    'minclass': minclass,
    'mincredit': mincredit,
    'mingpa': mingpa,
    'minperdisc': minperdisc,
    'minres': minres,
    'optional': optional,
    'remark': remark,
    'share': share,
    'standalone': standalone,
    'subset': subset_head,
    'under': under
}

dispatch_body = {
    'block': block,
    'blocktype': blocktype,
    'class_credit_body': class_credit_body,
    'copy_rules': copy_rules,
    'group': group,
    'if_then': if_then_body,
    'noncourse: ': noncourse,
    'remark': remark,
    'rule_complete': rule_complete,
    'subset': subset_body
}


# dispatch()
# -------------------------------------------------------------------------------------------------
def dispatch(ctx: any, which_part: str):
  """ Invoke the appropriate handler given its top-level context.
  """
  if which_part == 'head':
    return dispatch_head[class_name(ctx).lower()](ctx)
  else:
    return dispatch_body[class_name(ctx).lower()](ctx)
