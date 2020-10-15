#! /usr/local/bin/python3
""" These are the handlers for all the head and body rule types defined in ReqBlock.g4
"""

import sys
from dgw_utils import class_name,\
    build_course_list,\
    class_or_credit,\
    context_path,\
    get_qualifiers,\
    num_class_or_num_credit


# Handlers
# =================================================================================================


# block()
# -------------------------------------------------------------------------------------------------
def block(ctx, institution):
  """
      block           : NUMBER BLOCK expression rule_tag? label;

      The expression will be a {block-type, block-value} pair enclosed in parens and separated by
      an equal sign.
  """
  return_dict = {'tag': 'block', 'number': ctx.NUMBER().getText()}

  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      symbols = context.getText().split('=')
  assert isinstance(symbols, list) and len(symbols) == 2, (f'Invalid block expression: '
                                                           f'{ctx.expression().getText()}')
  return_dict['block_type'] = symbols[0].upper().strip()
  return_dict['block_value'] = symbols[1].upper().strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')
  return return_dict


# blocktype()
# -------------------------------------------------------------------------------------------------
def blocktype(ctx, institution):
  """
      blocktype       : NUMBER BLOCKTYPE expression label;

      The expression is a block type, enclosed in parentheses
  """
  return_dict = {'tag': 'blocktype', 'number': ctx.NUMBER().getText()}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['block_type'] = context.getText().strip().upper()

  assert 'block_type' in return_dict.keys(), f'Invalid blocktype {ctx.expression().getText()}'

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# class_credit_head()
# -------------------------------------------------------------------------------------------------
def class_credit_head(ctx, institution):
  """
      class_credit_head   : (num_classes | num_credits)
                            (logical_op (num_classes | num_credits))?
                            (IS? pseudo | header_tag | tag)*
                            display* label?;

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;
      allow_clause        : LP allow NUMBER RP;

      Note: header_tag is used only for audit presentation, and is ignored here.
"""
  return_dict = {'tag': 'class_credit'}
  return_dict.update(num_class_or_num_credit(ctx))

  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# class_credit_body()
# -------------------------------------------------------------------------------------------------
def class_credit_body(ctx, institution):
  """
      class_credit_body   : (num_classes | num_credits)
                            (logical_op (num_classes | num_credits))? course_list_body?
                            (IS? pseudo | proxy_advice | share | rule_tag | tag)*
                            display* proxy_advice? label?;

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;
      allow_clause        : LP allow NUMBER RP;

      course_list_body           : course_list (course_list_body_qualifier tag?)* label? ;
      course_list_body_qualifier : maxpassfail
                                 | maxperdisc
                                 | maxspread
                                 | maxtransfer
                                 | minarea
                                 | minclass
                                 | mincredit
                                 | mingpa
                                 | mingrade
                                 | minperdisc
                                 | minspread
                                 | rule_tag
                                 | samedisc
                                 | share

      Note: rule_tag is used only for audit presentation, and is ignored here.

      "Allowable rule qualifiers: DontShare, Exclusive, Hide, HideRule, HighPriority, LowPriority,
      LowestPriority, MaxPassFail, MaxPerDisc, MaxSpread, MaxTerm, MaxTransfer, MinAreas, MinGrade,
      MinPerDisc, MinSpread, MinTerm, NotGPA, ProxyAdvice, RuleTag, SameDisc, ShareWith, With."
  """
  return_dict = {'tag': 'class_credit'}
  return_dict.update(num_class_or_num_credit(ctx))
  if ctx.course_list_body():
    return_dict['courses'] = build_course_list(ctx.course_list_body().course_list(), institution)
    if context := ctx.course_list_body().course_list_body_qualifier():
      return_dict['courses']['qualifiers'] = get_qualifiers(context, institution)
    if context := ctx.course_list_body().label():
      return_dict['courses']['label'] = (context
                                         .string()
                                         .getText()
                                         .strip('"')
                                         .replace('\'', '’'))
  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.share():
    print(context_path(ctx), share(ctx.share(), institution))
    return_dict['share'] = share(ctx.share(), institution)

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# copy_rules()
# -------------------------------------------------------------------------------------------------
def copy_rules(ctx, institution):
  """
      copy_rules      : COPY_RULES expression SEMICOLON?;

      The expression is a rule_id enclosed in parentheses.
  """
  return_dict = {'tag': 'copy_rules', 'institution': institution}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['rule_id'] = context.getText().strip().upper()

  assert 'rule_id' in return_dict.keys(), f'Invalid copyrules {ctx.expression().getText()}'

  return return_dict


# group()
# -------------------------------------------------------------------------------------------------
def group(ctx, institution):
  """
  """
  print(class_name(ctx), 'not implemented yet', file=sys.stderr)
  return {}


# if_then_head()
# -------------------------------------------------------------------------------------------------
def if_then_head(ctx, institution):
  print(class_name(ctx), 'not implemented yet', file=sys.stderr)
  return {}


# if_then_body()
# -------------------------------------------------------------------------------------------------
def if_then_body(ctx, institution):
  print(class_name(ctx), 'not implemented yet', file=sys.stderr)
  return {}


# lastres()
# -------------------------------------------------------------------------------------------------
def lastres(ctx, institution):
  """
      lastres         : LASTRES NUMBER (OF NUMBER)?
                        class_or_credit
                        course_list? tag? display* label?;
  """
  return_dict = {'tag': 'lastres', 'class_or_credit': class_or_credit(ctx.class_or_credit())}

  numbers = ctx.NUMBER()
  return_dict['number'] = numbers.pop().getText().strip()
  if len(numbers) > 0:
    return_dict['of'] = numbers.pop().getText().strip()

  assert len(numbers) == 0

  if ctx.course_list():
    return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# maxclass()
# --------------------------------------------------------------------------------------------------
def maxclass(ctx, institution):
  """
      maxclass        : MAXCLASS NUMBER course_list? tag?;
  """
  return_dict = {'tag': 'maxclass',
                 'number': ctx.NUMBER().getText().strip()}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  return return_dict


# maxcredit()
# --------------------------------------------------------------------------------------------------
def maxcredit(ctx, institution):
  """
      maxcredit       : MAXCREDIT NUMBER course_list? tag?;
  """
  return_dict = {'tag': 'maxcredit',
                 'number': ctx.NUMBER().getText().strip()}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  return return_dict


# maxpassfail()
# --------------------------------------------------------------------------------------------------
def maxpassfail(ctx, institution):
  """
      maxpassfail     : MAXPASSFAIL NUMBER class_or_credit tag?;
  """
  return_dict = {'tag': 'max_pass-fail',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return return_dict


# maxperdisc()
# -------------------------------------------------------------------------------------------------
def maxperdisc(ctx, institution):
  """
      maxperdisc      : MAXPERDISC NUMBER class_or_credit LP SYMBOL (list_or SYMBOL)* RP tag?;
  """
  return_dict = {'tag': 'max_per-disc',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['disciplines'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return return_dict


# maxterm()
# -------------------------------------------------------------------------------------------------
def maxterm(ctx, institution):
  """
      maxterm         : MAXTERM NUMBER class_or_credit course_list tag?;
  """
  return_dict = {'tag': 'max_term',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  return return_dict


# maxtransfer()
# -------------------------------------------------------------------------------------------------
def maxtransfer(ctx, institution):
  """
      maxtransfer     : MAXTRANSFER NUMBER class_or_credit (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
  """
  return_dict = {'tag': 'max_transfer',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  if ctx.SYMBOL():
    symbol_contexts = ctx.SYMBOL()
    return_dict['transfer_types'] = [symbol.getText() for symbol in symbol_contexts]

  return return_dict


# minclass()
# --------------------------------------------------------------------------------------------------
def minclass(ctx, institution):
  """
      minclass        : MINCLASS NUMBER course_list tag? display* label?;
  """
  return_dict = {'tag': 'min_class',
                 'number': ctx.NUMBER().getText(),
                 'course_list': build_course_list(ctx.course_list(), institution)}

  if ctx.display():
    return_dict['display'] = ' '.join([item.string().getText().strip(' "')
                                      for item in ctx.display()]).strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# mincredit()
# --------------------------------------------------------------------------------------------------
def mincredit(ctx, institution):
  """
      mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
  """
  return_dict = {'tag': 'min_credit',
                 'number': ctx.NUMBER().getText()}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# mingpa()
# --------------------------------------------------------------------------------------------------
def mingpa(ctx, institution):
  """
      mingpa          : MINGPA NUMBER (course_list | expression)? tag? display* label?;
  """
  return_dict = {'tag': 'min_gpa', 'number': ctx.NUMBER().getText()}

  if ctx.course_list():
    return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  if ctx.expression():
    return_dict['expression'] = ctx.expression().getText()

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# mingrade()
# -------------------------------------------------------------------------------------------------
def mingrade(ctx, institution):
  """
      mingrade        : MINGRADE NUMBER;
  """
  return {'tag': 'min_grade', 'number': ctx.NUMBER().getText()}


# minperdisc()
# -------------------------------------------------------------------------------------------------
def minperdisc(ctx, institution):
  """
      minperdisc  : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
  """
  return_dict = {'tag': 'min_per-disc',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['discipline'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return return_dict


# minres()
# -------------------------------------------------------------------------------------------------
def minres(ctx, institution):
  """ minres          : MINRES (num_classes | num_credits) display* label? tag?;
  """
  return_dict = num_class_or_num_credit(ctx)
  return_dict['tag'] = 'min_res'

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# noncourse()
# -------------------------------------------------------------------------------------------------
def noncourse(ctx, institution):
  """
      noncourse       : NUMBER NONCOURSE LP expression RP label?;
  """
  return_dict = {'tag': 'noncourse',
                 'number': ctx.NUMBER().getText(),
                 'expression': ctx.expression().getText()}  # Not interpreted (yet)

  return return_dict


# optional()
# -------------------------------------------------------------------------------------------------
def optional(ctx, institution):
  """
      If present, the block’s requirements are optional.
  """
  return {'tag': 'optional'}


# remark()
# -------------------------------------------------------------------------------------------------
def remark(ctx, institution):
  """
      remark          : (REMARK string SEMICOLON?)+;
  """
  # remark_str = ctx.string().getText().strip(' "')
  # print(remark_str, file=sys.stderr)
  # print(ctx.remark()[0].string().getText().strip(' "'), file=sys.stderr)
  # print(ctx.remark()[0].remark()[0].string().getText().strip(' "'), file=sys.stderr)
  # print(ctx.remark()[0].remark()[0].remark()[0].string().getText().strip(' "'), file=sys.stderr)
  remark_str = ' '.join([s.getText().strip(' "') for s in ctx.string()])
  return_dict = {'tag': 'remark',
                 'text': remark_str}
  return return_dict


# rule_complete()
# -------------------------------------------------------------------------------------------------
def rule_complete(ctx, institution):
  """
      rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) label?;
  """
  return_dict = {'tag': 'rule_complete'}
  return_dict['is_complete'] = True if ctx.RULE_COMPLETE() else False

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# share()
# -------------------------------------------------------------------------------------------------
def share(ctx, institution):
  """
      share           : (SHARE | DONT_SHARE) (NUMBER class_or_credit)? expression? tag?;
  """
  return_dict = {'tag': 'share'}

  if ctx.SHARE():
    return_dict['share_type'] = 'allow sharing'
  else:
    return_dict['share_type'] = 'exclusive'

  if ctx.NUMBER():
    return_dict['number'] = ctx.NUMBER().getText().strip()
    return_dict['class_or_credit'] = class_or_credit(ctx.class_or_credit())
  if ctx.expression():
    return_dict['expression'] = ctx.expression().getText()

  return return_dict


# standalone()
# -------------------------------------------------------------------------------------------------
def standalone(ctx, institution):
  """
      standalone      : STANDALONE;
  """
  return{'tag': 'standalone'}


# subset_body()
# -------------------------------------------------------------------------------------------------
def subset_body(ctx, institution):
  """
      /* Body only
       */
      subset            : BEGINSUB
                        ( if_then_body
                          | block
                          | blocktype
                          | class_credit_body
                          | copy_rules
                          | course_list
                          | group
                          | noncourse
                          | rule_complete
                        )+
                        ENDSUB subset_qualifier* label?;

      subset_qualifier  : maxpassfail
                        | maxperdisc
                        | maxspread
                        | maxtransfer
                        | mingpa
                        | mingrade
                        | minperdisc
                        | minspread
                        | rule_tag
                        | share
                        ;
  """
  return_dict = {'tag': 'subset'}

  # The grammar says one or more of each of the rules go between BEGINSUB and ENDSUB. But really
  # each one should appear at most once, except for class_credit_body. So if there is a list and
  # it's not class_credit_body, it must be length one.
  if len(ctx.if_then_body()) > 0:
    return_dict['if_then'] = [if_then_body(context, institution)
                              for context in ctx.if_then_body()]

  if len(ctx.block()) > 0:
    return_dict['block'] = [block(context, institution) for context in ctx.block()]

  if len(ctx.blocktype()) > 0:
    return_dict['blocktype'] = [blocktype(context, institution) for context in ctx.blocktype()]

  if len(ctx.class_credit_body()) > 0:
    # Return a list of class_credit dicts
    return_dict['class_credit'] = [class_credit_body(context, institution)
                                   for context
                                   in ctx.class_credit_body()]

  if len(ctx.copy_rules()) > 0:
    assert len(ctx.copy_rules()) == 1
    return_dict['copy_rules'] = copy_rules(ctx.copy_rules()[0], institution)

  if len(ctx.course_list()) > 0:
    return_dict['courses'] = [build_course_list(context, institution)
                              for context in ctx.course_list()]

  if len(ctx.group()) > 0:
    return_dict['group'] = [group(context, institution) for context in ctx.group()]

  if len(ctx.noncourse()) > 0:
    return_dict['noncourse'] = [noncourse(context, institution) for context in ctx.noncourse()]

  if len(ctx.rule_complete()) > 0:
    assert len(ctx.rule_complete()) == 1
    return_dict['rule_complete'] = rule_complete(ctx.rule_complete()[0], institution)

  return return_dict


# under()
# -------------------------------------------------------------------------------------------------
def under(ctx, institution):
  """
      under           : UNDER NUMBER class_or_credit course_list display* label;
  """
  return_dict = {'tag': 'under',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution)

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# Dispatch Tables
# =================================================================================================
""" There are two in case If-then and Share need to be handled differently in Head and Body.
"""
dispatch_head = {
    'class_credit_head': class_credit_head,
    'if_then_head': if_then_head,
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
    'under': under
}

dispatch_body = {
    'block': block,
    'blocktype': blocktype,
    'class_credit_body': class_credit_body,
    'copy_rules': copy_rules,
    'group': group,
    'if_then_body': if_then_body,
    'noncourse': noncourse,
    'remark': remark,
    'rule_complete': rule_complete,
    'subset': subset_body
}


# dispatch()
# -------------------------------------------------------------------------------------------------
def dispatch(ctx: any, institution: str, which_part: str):
  """ Invoke the appropriate handler given its top-level context.
  """
  if which_part == 'head':
    return dispatch_head[class_name(ctx).lower()](ctx, institution)
  else:
    return dispatch_body[class_name(ctx).lower()](ctx, institution)
