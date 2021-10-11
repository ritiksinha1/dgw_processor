#! /usr/local/bin/python3
""" These are the handlers for all the head and body rule types defined in ReqBlock.g4
    This revised version changes the structure of the dicts, mainly to eliminate the 'tag' key.
"""

import os
import sys

from typing import Any

from dgw_utils import class_name,\
    build_course_list,\
    class_or_credit,\
    concentration_list,\
    context_path,\
    expression_to_str,\
    get_display,\
    get_groups,\
    get_label,\
    get_rules,\
    get_qualifiers,\
    num_class_or_num_credit

from traceback import print_stack
from pprint import pprint

DEBUG = os.getenv('DEBUG_HANDLERS')

# Handlers
# =================================================================================================


# block()
# -------------------------------------------------------------------------------------------------
def block(ctx, institution, requirement_id):
  """
      block           : NUMBER BLOCK expression rule_tag? label;

      The expression will be a {block-type, block-value} pair enclosed in parens and separated by
      an equal sign.
  """
  return_dict = {'number': ctx.NUMBER().getText()}

  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      symbols = context.getText().split('=')
  assert isinstance(symbols, list) and len(symbols) == 2, (f'Assertion Error: Invalid block '
                                                           f'expression ('
                                                           f'{ctx.expression().getText()}) '
                                                           f'in block()')
  return_dict['block_type'] = symbols[0].upper().strip()
  return_dict['block_value'] = symbols[1].upper().strip()

  return_dict['label'] = get_label(ctx)

  return {'block': return_dict}


# blocktype()
# -------------------------------------------------------------------------------------------------
def blocktype(ctx, institution, requirement_id):
  """
      blocktype       : NUMBER BLOCKTYPE expression label;

      The expression is a block type, enclosed in parentheses
  """
  return_dict = {'number': ctx.NUMBER().getText()}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['block_type'] = context.getText().strip().upper()

  assert 'block_type' in return_dict.keys(), (f'Assertion Error: Invalid blocktype '
                                              f'({ctx.expression().getText()}) in blocktype()')

  return_dict['label'] = get_label(ctx)

  return {'blocktype': return_dict}


# class_credit_head()
# -------------------------------------------------------------------------------------------------
def class_credit_head(ctx, institution, requirement_id):
  """
      class_credit_head   : (num_classes | num_credits)
                            (logical_op (num_classes | num_credits))?
                            (IS? pseudo | display | proxy_advice | header_tag | label | tag)*
                          ;

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;
      allow_clause        : LP allow NUMBER RP;

      Note: header_tag and allow are used only for audit presentation, and are ignored here.
"""
  return_dict = num_class_or_num_credit(ctx)

  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return {'class_credit_head': return_dict}


# class_credit_body()
# -------------------------------------------------------------------------------------------------
def class_credit_body(ctx, institution, requirement_id):
  """
      class_credit_body : (num_classes | num_credits)
                          (logical_op (num_classes | num_credits))? course_list_body?
                          (IS? pseudo | display | proxy_advice | remark | share | rule_tag | label
                          | tag )*

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;

      course_list_body    : course_list ( qualifier tag? | proxy_advice )*;

    Ignore proxy_advice, rule_tag and tag.
  """
  if DEBUG:
    print(f'*** class_credit_body({class_name(ctx)=}, {institution=}, {requirement_id=})',
          file=sys.stderr)

  return_dict = num_class_or_num_credit(ctx)

  if ctx.course_list_body():
    if qualifiers := get_qualifiers(ctx.course_list_body().qualifier(),
                                    institution, requirement_id):
      return_dict.update(qualifiers)
    return_dict.update(build_course_list(ctx.course_list_body().course_list(),
                                         institution, requirement_id))

  if ctx.pseudo():
    return_dict['is_pseudo'] = True

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  if ctx.remark():
    return_dict['remark'] = ' '.join([s.getText().strip(' "')
                                     for c in ctx.remark()
                                     for s in c.string()])

  if share_contexts := ctx.share():
    if not isinstance(share_contexts, list):
      share_contexts = [share_contexts]
    return_dict['share'] = '; '.join([share(share_ctx.share(), institution, requirement_id)
                                      for share_ctx in share_contexts])

  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  return {'class_credit_body': return_dict}


# conditional_head()
# -------------------------------------------------------------------------------------------------
def conditional_head(ctx, institution, requirement_id):
  """
      conditional_head    : IF expression THEN (head_rule | head_rule_group)
                        (proxy_advice | label)* else_head?;
      else_head       : ELSE (head_rule | head_rule_group)
                        (proxy_advice | label)*;
      head_rule_group : (begin_if head_rule+ end_if);
      head_rule         : conditional_head
                        | block
                        | blocktype
                        | class_credit_head
                        | copy_rules
                        | lastres
                        | maxcredit
                        | maxpassfail_head
                        | maxterm
                        | maxtransfer_head
                        | minclass_head
                        | mincredit_head
                        | mingpa
                        | mingrade
                        | minperdisc_head
                        | minres
                        | minterm
                        | noncourse
                        | proxy_advice
                        | remark
                        | rule_complete
                        | share_head
                        ;
  """
  if DEBUG:
    print(f'*** conditional_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = dict()
  condition = expression_to_str(ctx.expression())
  return_dict['condition'] = condition

  # # Concentrations not implemented yet
  # if 'conc' in condition.lower():
  #   return_dict['concentrations'] = concentration_list(condition,
  #                                                      institution,
  #                                                      requirement_id)

  return_dict['label'] = get_label(ctx)

  if ctx.head_rule():
    return_dict['if_true'] = get_rules(ctx.head_rule(), institution, requirement_id)
  elif ctx.head_rule_group():
    return_dict['if_true'] = get_rules(ctx.head_rule_group().head_rule(),
                                       institution,
                                       requirement_id)
  else:
    return_dict['if_true'] = 'Missing True Part'

  if ctx.else_head():
    if ctx.else_head().head_rule():
      return_dict['if_false'] = get_rules(ctx.else_head().head_rule(),
                                          institution, requirement_id)
    elif ctx.else_head().head_rule_group():
      return_dict['if_false'] = get_rules(ctx.else_head().head_rule_group().head_rule(),
                                          institution, requirement_id)
    else:
      return_dict['if_false'] = 'Missing False Part'

  return {'conditional': return_dict}


# conditional_body()
# -------------------------------------------------------------------------------------------------
def conditional_body(ctx, institution, requirement_id):
  """ Just like conditional_head, except the rule or rule_group can be followed by requirements that
      apply to the rule or rule group.

      conditional_body  : IF expression THEN (body_rule | body_rule_group)
                          qualifier* label? else_body?;
      else_body         : ELSE (body_rule | body_rule_group)
                          qualifier* label?;
      body_rule_group : (begin_if body_rule+ end_if);

      body_rule       : conditional_body
                      | block
                      | blocktype
                      | class_credit_body
                      | copy_rules
                      | group_requirement
                      | lastres
                      | maxcredit
                      | maxtransfer
                      | minclass
                      | mincredit
                      | mingrade
                      | minres
                      | noncourse
                      | proxy_advice
                      | remark
                      | rule_complete
                      | share
                      | subset
                      ;
  """
  if DEBUG:
      print(f'*** conditional_body({class_name(ctx)}, {institution}. {requirement_id})',
            file=sys.stderr)

  return_dict = dict()
  condition = expression_to_str(ctx.expression())
  return_dict['condition'] = condition

  # Concentrations
  if 'conc' in condition.lower():
    return_dict['concentrations'] = concentration_list(condition,
                                                       institution,
                                                       requirement_id)

  return_dict['label'] = get_label(ctx)

  if qualifiers := get_qualifiers(ctx, institution, requirement_id):
    return_dict.update(qualifiers)

  if ctx.body_rule():
    return_dict['if_true'] = get_rules(ctx.body_rule(), institution, requirement_id)
  elif ctx.body_rule_group():
    return_dict['if_true'] = get_rules(ctx.body_rule_group().body_rule(),
                                       institution, requirement_id)
  else:
    return_dict['if_true'] = 'Missing True Part'

  if ctx.else_body():
    if ctx.else_body().body_rule():
      return_dict['if_false'] = get_rules(ctx.else_body().body_rule(),
                                          institution, requirement_id)
    elif ctx.else_body().body_rule_group():
      return_dict['if_false'] = get_rules(ctx.else_body().body_rule_group().body_rule(),
                                          institution, requirement_id)
    else:
      return_dict['if_false'] = 'Missing False Part'

  return {'conditional': return_dict}


# copy_rules()
# -------------------------------------------------------------------------------------------------
def copy_rules(ctx, institution, requirement_id):
  """
      copy_rules      : COPY_RULES expression SEMICOLON?;

      The expression is a requirement_id enclosed in parentheses (RA######).
  """
  if DEBUG:
      print(f'*** copy_rules({class_name(ctx)}, {institution}. {requirement_id})',
            file=sys.stderr)

  return_dict = {'institution': institution}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['requirement_id'] = f'{context.getText().strip().upper()}'

  assert 'requirement_id' in return_dict.keys(), (f'Assertion Error: no requirement_id in '
                                                  f'({ctx.expression().getText()}) in copy_rules()')

  return {'copy_rules': return_dict}


# group_requirement()
# -------------------------------------------------------------------------------------------------
def group_requirement(ctx: Any, institution: str, requirement_id: str) -> dict:
  """
group_requirement : NUMBER GROUP groups qualifier* label? ;
groups            : group (logical_op group)*; // But only OR should occur
group             : LP
                  (block
                   | blocktype
                   | course_list
                   | class_credit_body
                   | group_requirement
                   | noncourse
                   | rule_complete)
                  qualifier* label?
                  RP
                ;
  “Qualifiers that must be applied to all rules in the group list must occur after the last right
  parenthesis and before the label at the end of the Group statement. Qualifiers that apply only to
  a specific rule in the group list must appear inside the parentheses for that group item rule.”

  Allowable rule qualifiers: DontShare, Hide, HideRule, HighPriority, LowPriority, LowestPriority,
  MaxPassFail, MaxPerDisc, MaxTransfer, MinGrade, MinPerDisc, NotGPA, ProxyAdvice, SameDisc,
  ShareWith, MinClass, MinCredit, RuleTag.
  """
  if DEBUG:
    print(f'*** group_requirement({class_name(ctx)}, 'f'{institution}, {requirement_id})',
          file=sys.stderr)

  if isinstance(ctx, list):
    group_requirement_contexts = ctx
  else:
    group_requirement_contexts = [ctx]

  requirement_list = []
  for group_requirement_ctx in group_requirement_contexts:

    return_dict = {'number': group_requirement_ctx.NUMBER().getText()}

    return_dict['group_list'] = get_groups(group_requirement_ctx.groups(),
                                           institution, requirement_id)

    if group_requirement_ctx.label():
      return_dict['label'] = get_label(group_requirement_ctx)

    if group_requirement_ctx.qualifier():
      return_dict.update(get_qualifiers(group_requirement_ctx.qualifier(),
                                        institution, requirement_id))

    requirement_list.append({'group_requirement': return_dict})

  return {'group_requirements': requirement_list}


# header_tag()
# -------------------------------------------------------------------------------------------------
def header_tag(ctx, institution, requirement_id):
  """ header_tag  : (HEADER_TAG nv_pair)+;
  """
  if DEBUG:
    print(f'*** header_tag({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  if isinstance(ctx, list):
    header_tags = ctx
  else:
    header_tags = [ctx]

  tag_list = []
  for header_tag in header_tags:
    for pair in header_tag.nv_pair():
      name = pair.SYMBOL()[0].getText()
      value = pair.STRING().getText() if len(pair.SYMBOL()) == 1 else pair.SYMBOL()[1].getText()
      tag_list.append({'name': name, 'value': value})

  return {'headertag': tag_list}


# rule_tag()
# -------------------------------------------------------------------------------------------------
def rule_tag(ctx, institution, requirement_id):
  """ rule_tag  : (RULE_TAG nv_pair)+;
      nv_pair   : SYMBOL '=' (STRING | SYMBOL);

  """
  if DEBUG:
    print(f'*** rule_tag({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  if isinstance(ctx, list):
    rule_tags = ctx
  else:
    rule_tags = [ctx]

  tag_list = []
  for rule_tag in rule_tags:
    for pair in rule_tag.nv_pair():
      name = pair.SYMBOL()[0].getText()
      value = pair.STRING().getText() if len(pair.SYMBOL()) == 1 else pair.SYMBOL()[1].getText()
      tag_list.append({'name': name, 'value': value})

  return {'ruletag': tag_list}


# lastres()
# -------------------------------------------------------------------------------------------------
def lastres(ctx, institution, requirement_id):
  """
      lastres         : LASTRES NUMBER (OF NUMBER)?
                        class_or_credit
                        course_list? tag? display* proxy_advice?;
  """
  if DEBUG:
    print(f'*** lastres({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'class_or_credit': class_or_credit(ctx.class_or_credit())}

  numbers = ctx.NUMBER()
  return_dict['number'] = numbers.pop().getText().strip()
  if len(numbers) > 0:
    return_dict['of_number'] = numbers.pop().getText().strip()

  assert len(numbers) == 0, f'Assertion Error: {len(numbers)} is not zero in lastres()'

  if ctx.course_list():
    return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'lastres': return_dict}


# lastres_head()
# -------------------------------------------------------------------------------------------------
def lastres_head(ctx, institution, requirement_id):
  """
      lastres_head    : lastres label?;
  """
  if DEBUG:
    print(f'*** lastres_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  lastres_ctx = ctx.lastres()
  return_dict.update(lastres(lastres_ctx, institution, requirement_id))

  return {'lastres_head': return_dict}


# maxclass()
# --------------------------------------------------------------------------------------------------
def maxclass(ctx, institution, requirement_id):
  """
      maxclass        : MAXCLASS NUMBER course_list? tag?;

      This is actually only a header production
  """
  if DEBUG:
    print(f'*** maxclass({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText().strip()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxclass': return_dict}


# maxclass_head()
# --------------------------------------------------------------------------------------------------
def maxclass_head(ctx, institution, requirement_id):
  """
      maxclass_head   : maxclass label?;
  """
  if DEBUG:
    print(f'*** maxclass_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  maxclass_ctx = ctx.maxclass()

  return_dict.update(maxclass(maxclass_ctx, institution, requirement_id))

  return {'maxclass_head': return_dict}


# maxcredit()
# --------------------------------------------------------------------------------------------------
def maxcredit(ctx, institution, requirement_id):
  """
      maxcredit_head  : maxcredit label?;
      maxcredit       : MAXCREDIT NUMBER course_list? tag?;

      This is actually only a header production
  """
  if DEBUG:
    print(f'*** maxcredit({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText().strip()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxcredit': return_dict}


# maxcredit_head()
# --------------------------------------------------------------------------------------------------
def maxcredit_head(ctx, institution, requirement_id):
  """
      maxcredit_head  : maxcredit label?;
  """
  if DEBUG:
    print(f'*** maxcredit_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  maxcredit_ctx = ctx.maxcredit()

  return_dict.update(maxcredit(maxcredit_ctx, institution, requirement_id))

  return {'maxcredit_head': return_dict}


# maxpassfail()
# --------------------------------------------------------------------------------------------------
def maxpassfail(ctx, institution, requirement_id):
  """
      maxpassfail      : MAXPASSFAIL NUMBER class_or_credit tag?;
  """
  if DEBUG:
    print(f'*** maxpassfail({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}

  return {'maxpassfail': return_dict}


# maxpassfail_head()
# --------------------------------------------------------------------------------------------------
def maxpassfail_head(ctx, institution, requirement_id):
  """
      maxpassfail_head : maxpassfail label?;
  """
  if DEBUG:
    print(f'*** maxpassfail_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  maxpassfail_ctx = ctx.maxpassfail()

  return_dict.update(maxpassfail(maxpassfail_ctx, institution, requirement_id))

  return {'maxpassfail_head': return_dict}


# maxperdisc()
# -------------------------------------------------------------------------------------------------
def maxperdisc(ctx, institution, requirement_id):
  """
      maxperdisc      : MAXPERDISC NUMBER class_or_credit LP SYMBOL (list_or SYMBOL)* RP tag?;
  """
  if DEBUG:
    print(f'*** maxperdisc({class_name(ctx)=}, {institution=}, {requirement_id=}',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText().strip(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['disciplines'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return {'maxperdisc': return_dict}


# maxperdisc_head()
# -------------------------------------------------------------------------------------------------
def maxperdisc_head(ctx, institution, requirement_id):
  """
      maxperdisc_head : maxperdisc label? ;
  """
  if DEBUG:
    print(f'*** maxperdisc_head({class_name(ctx)=}, {institution=}, {requirement_id=}',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  maxperdisc_ctx = ctx.maxperdisc()

  return_dict = {'number': maxperdisc_ctx.NUMBER().getText().strip(),
                 'class_or_credit': class_or_credit(maxperdisc_ctx.class_or_credit())}
  return_dict['disciplines'] = [discp.getText().upper() for discp in maxperdisc_ctx.SYMBOL()]

  return {'maxperdisc_head': return_dict}


# maxterm()
# -------------------------------------------------------------------------------------------------
def maxterm(ctx, institution, requirement_id):
  """
      maxterm         : MAXTERM NUMBER class_or_credit course_list tag?;
  """
  if DEBUG:
    print(f'*** maxterm({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxterm': return_dict}


# maxterm_head()
# -------------------------------------------------------------------------------------------------
def maxterm_head(ctx, institution, requirement_id):
  """
      maxterm_head    : maxterm label?;
  """
  if DEBUG:
    print(f'*** maxterm({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  maxterm_ctx = ctx.maxterm()

  return_dict.update(maxterm(maxterm_ctx, institution, requirement_id))

  return {'maxterm_head': return_dict}


# maxtransfer()
# -------------------------------------------------------------------------------------------------
def maxtransfer(ctx, institution, requirement_id):
  """
      maxtransfer      : MAXTRANSFER NUMBER class_or_credit (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
  """
  if DEBUG:
    print(f'*** maxtransfer({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  if ctx.SYMBOL():
    symbol_contexts = ctx.SYMBOL()
    return_dict['transfer_types'] = [symbol.getText() for symbol in symbol_contexts]

  return {'maxtransfer': return_dict}


# maxtransfer_head()
# -------------------------------------------------------------------------------------------------
def maxtransfer_head(ctx, institution, requirement_id):
  """
      maxtransfer_head : maxtransfer label?;
  """
  if DEBUG:
    print(f'*** maxtransfer_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  maxtransfer_ctx = ctx.maxtransfer()

  return_dict.update(maxtransfer(maxtransfer_ctx, institution, requirement_id))

  return {'maxtransfer_head': return_dict}


# minclass()
# --------------------------------------------------------------------------------------------------
def minclass(ctx, institution, requirement_id):
  """
      minclass        : MINCLASS NUMBER course_list tag? display* label?;
  """
  if DEBUG:
    print(f'*** minclass({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'courses': build_course_list(ctx.course_list(), institution, requirement_id)}

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'minclass': return_dict}


# minclass_head()
# --------------------------------------------------------------------------------------------------
def minclass_head(ctx, institution, requirement_id):
  """
      minclass_head     : minclass label?;
  """
  if DEBUG:
    print(f'*** minclass_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  minclass_ctx = ctx.minclass()

  return_dict.update(minclass(minclass_ctx, institution, requirement_id))

  return {'minclass_head': return_dict}


# mincredit()
# --------------------------------------------------------------------------------------------------
def mincredit(ctx, institution, requirement_id):
  """
      mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
  """
  if DEBUG:
    print(f'*** mincredit({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'mincredit': return_dict}


# mincredit_head()
# --------------------------------------------------------------------------------------------------
def mincredit_head(ctx, institution, requirement_id):
  """
      mincredit_head     : mincredit label?;
  """
  if DEBUG:
    print(f'*** mincredit_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  mincredit_ctx = ctx.mincredit()

  return_dict.update(mincredit(mincredit_ctx, institution, requirement_id))

  return {'mincredit_head': return_dict}


# mingpa()
# --------------------------------------------------------------------------------------------------
def mingpa(ctx, institution, requirement_id):
  """
      mingpa          : MINGPA NUMBER (course_list | expression)? tag? display* label?;
  """
  if DEBUG:
    print(f'*** mingpa({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText()}

  if ctx.course_list():
    return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.expression():
    return_dict['expression'] = ctx.expression().getText()

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'mingpa': return_dict}


# mingpa_head()
# --------------------------------------------------------------------------------------------------
def mingpa_head(ctx, institution, requirement_id):
  """
      mingpa_head     : mingpa label?;
  """
  if DEBUG:
    print(f'*** mingpa_head({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  label_str = get_label(ctx)
  if label_str:
    return_dict['label'] = label_str

  mingpa_ctx = ctx.mingpa()

  return_dict.update(mingpa(mingpa_ctx, institution, requirement_id))

  return {'mingpa_head': return_dict}


# mingrade()
# -------------------------------------------------------------------------------------------------
def mingrade(ctx, institution, requirement_id):
  """
      mingrade        : MINGRADE NUMBER;
  """
  if DEBUG:
    print(f'*** mingrade({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText()}

  return {'mingrade': return_dict}


# mingrade_head()
# -------------------------------------------------------------------------------------------------
def mingrade_head(ctx, institution, requirement_id):
  """
      mingrade_head   : mingrade label?;
  """
  if DEBUG:
    print(f'*** mingrade_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  label_str = get_label(ctx)
  if label_str:
    return_dict['label'] = label_str

  mingrade_ctx = ctx.mingrade()
  return_dict.update(mingrade(mingrade_ctx, institution, requirement_id))

  return {'mingrade_head': return_dict}


# minperdisc()
# -------------------------------------------------------------------------------------------------
def minperdisc(ctx, institution, requirement_id):
  """
      minperdisc  : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
  """
  if DEBUG:
    print(f'*** minperdisc({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['discipline'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return {'minperdisc': return_dict}


# minperdisc_head()
# -------------------------------------------------------------------------------------------------
def minperdisc_head(ctx, institution, requirement_id):
  """
      minperdisc_head   : minperdisc label?;
  """
  if DEBUG:
    print(f'*** minperdisc_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  minperdisc_ctx = ctx.minperdisc()

  return_dict.update(minperdisc(minperdisc_ctx, institution, requirement_id))

  return {'minperdisc_head': return_dict}


# minres()
# -------------------------------------------------------------------------------------------------
def minres(ctx, institution, requirement_id):
  """
      minres      : MINRES (num_classes | num_credits) display* tag?;

      This is actually only a header production
  """
  if DEBUG:
    print(f'*** minres({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = num_class_or_num_credit(ctx)

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'minres': return_dict}


# minres_head()
# -------------------------------------------------------------------------------------------------
def minres_head(ctx, institution, requirement_id):
  """
      minres_head : minres label?;
  """
  if DEBUG:
    print(f'*** minres_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  minres_ctx = ctx.minres()

  return_dict = {}
  label_str = get_label(ctx)
  if label_str:
    return_dict['label'] = label_str

  return_dict.update(minres(minres_ctx, institution, requirement_id))

  return {'minres_head': return_dict}


# minterm()
# -------------------------------------------------------------------------------------------------
def minterm(ctx, institution, requirement_id):
  """
      minterm         : MINTERM NUMBER class_or_credit course_list? tag? display*;
  """
  if DEBUG:
    print(f'*** minterm({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'minterm': return_dict}


# minterm_head()
# -------------------------------------------------------------------------------------------------
def minterm_head(ctx, institution, requirement_id):
  """
      minterm_head  : minterm label?;
  """
  if DEBUG:
    print(f'*** minterm_head({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {}
  label_str = get_label(ctx)
  if label_str:
    return_dict['label'] = label_str

  minterm_ctx = ctx.minterm()

  return_dict.update(minterm(minterm_ctx, institution, requirement_id))

  return {'minterm_head': return_dict}


# noncourse()
# -------------------------------------------------------------------------------------------------
def noncourse(ctx, institution, requirement_id):
  """
      noncourse       : NUMBER NONCOURSE LP expression RP label?;
  """
  if DEBUG:
    print(f'*** noncourse({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'expression': ctx.expression().getText(),
                 'Development status': 'Expression not interpreted yet'}  # Not interpreted (yet)

  return {'noncourse': return_dict}


# optional()
# -------------------------------------------------------------------------------------------------
def optional(ctx, institution, requirement_id):
  """ If present, the block’s requirements are optional.
  """
  if DEBUG:
    print(f'*** optional({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return {'optional': 'This requirement block is not required.'}


# proxy_advice()
# -------------------------------------------------------------------------------------------------
def proxy_advice(ctx, institution, requirement_id):
  """ Recognizing this, but no plans to do anything with it.
  """
  if DEBUG:
    print(f'*** proxy_advice({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return {}


# remark()
# -------------------------------------------------------------------------------------------------
def remark(ctx, institution, requirement_id):
  """ remark          : (REMARK string SEMICOLON?)+;
  """
  if DEBUG:
    print(f'*** remark({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  if not isinstance(remark_contexts := ctx, list):
    remark_contexts = [remark_contexts]
  remark_str = ''
  for remark_context in remark_contexts:
    remark_str += ' '.join([c.getText().strip(' "') for c in remark_context.string()])
  return {'remark': remark_str}


# rule_complete()
# -------------------------------------------------------------------------------------------------
def rule_complete(ctx, institution, requirement_id):
  """ rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) (proxy_advice | rule_tag | label)*;
  """
  if DEBUG:
    print(f'*** rule_complete({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = dict()
  return_dict['is_complete'] = True if ctx.RULE_COMPLETE() else False

  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  if ctx.rule_tag():
    return_dict['rule_tag'] = rule_tag(ctx.rule_tag(), institution, requirement_id)

  return {'rule_complete': return_dict}


# share()
# -------------------------------------------------------------------------------------------------
def share(ctx, institution, requirement_id):
  """
      share           : (SHARE | DONT_SHARE) (NUMBER class_or_credit)? expression? tag?;
  """
  if DEBUG:
    print(f'*** share({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)

  if class_name(ctx) == 'Share':
    share_ctx = ctx
  else:
    share_ctx = ctx.share()
  share_dict = dict()

  share_dict['allow_sharing'] = True if share_ctx.SHARE() is not None else False

  if ctx.NUMBER():
    share_dict['number'] = ctx.NUMBER().getText().strip()
    share_dict['class_or_credit'] = class_or_credit(ctx.class_or_credit())
  if ctx.expression():
    share_dict['expression'] = ctx.expression().getText()

  return {'share': share_dict}


# share_head()
# -------------------------------------------------------------------------------------------------
def share_head(ctx, institution, requirement_id):
  """
      share_head        : share label?;
  """
  if DEBUG:
    print(f'*** share_head({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)

  return_dict = {}
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  share_ctx = ctx.share()

  return_dict.update(share(share_ctx, institution, requirement_id))

  return {'share_head': return_dict}


# standalone()
# -------------------------------------------------------------------------------------------------
def standalone(ctx, institution, requirement_id):
  """
      standalone      : STANDALONE;
  """
  if DEBUG:
    print(f'*** standalone({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return{'standalone': 'This is a standalone requirement block.'}


# subset()
# -------------------------------------------------------------------------------------------------
def subset(ctx, institution, requirement_id):
  """
      subset            : BEGINSUB
                        ( conditional_body
                          | block
                          | blocktype
                          | class_credit_body
                          | copy_rules
                          | course_list
                          | group_requirement
                          | noncourse
                          | rule_complete
                        )+
                        ENDSUB qualifier* (remark | label)*;

  """
  if DEBUG:
    print(f'*** subset({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = dict()

  if ctx.conditional_body():
    return_dict['conditional'] = [conditional_body(context, institution, requirement_id)
                                  for context in ctx.conditional_body()]

  if ctx.block():
    return_dict['block'] = [block(context, institution, requirement_id) for context in ctx.block()]

  if ctx.blocktype():
    return_dict['blocktype'] = [blocktype(context, institution, requirement_id)
                                for context in ctx.blocktype()]

  if ctx.class_credit_body():
    # Return a list of class_credit dicts
    return_dict['requirements'] = [class_credit_body(context, institution, requirement_id)
                                   for context in ctx.class_credit_body()]

  if ctx.copy_rules():
    assert len(ctx.copy_rules()) == 1, (f'Assertion Error: {len(ctx.copy_rules())} '
                                        f'is not unity in subset')
    return_dict.update(copy_rules(ctx.copy_rules()[0], institution, requirement_id))

  if ctx.course_list():
    return_dict['course_lists'] = [build_course_list(context, institution, requirement_id)
                                   for context in ctx.course_list()]

  if ctx.group_requirement():
    return_dict.update(group_requirement(ctx.group_requirement(), institution, requirement_id))

  if ctx.noncourse():
    return_dict['noncourse'] = [noncourse(context, institution, requirement_id)
                                for context in ctx.noncourse()]

  if ctx.rule_complete():
    assert len(ctx.rule_complete()) == 1, (f'Assertion Error: {len(ctx.rule_complete())} '
                                           f'is not unity in subset')
    return_dict['rule_complete'] = rule_complete(ctx.rule_complete()[0],
                                                 institution, requirement_id)

  if qualifiers := ctx.qualifier():
    return_dict.update(get_qualifiers(qualifiers, institution, requirement_id))

  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  if ctx.remark():
    return_dict['remark'] = ' '.join([s.getText().strip(' "')
                                     for c in ctx.remark()
                                     for s in c.string()])

  return {'subset': return_dict}


# under()
# -------------------------------------------------------------------------------------------------
def under(ctx, institution, requirement_id):
  """
      under           : UNDER NUMBER class_or_credit course_list display* label;

      This seems to be the only item in the header that can have a label. But, also, it is normally
      used in Award blocks, not Degree, major, minor, concentrations.
  """
  if DEBUG:
    print(f'*** under({class_name(ctx)}, {institution}. {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return {'under': return_dict}


# Dispatch Tables
# =================================================================================================
""" There are two in case conditional and Share need to be handled differently in Head and Body.
"""
dispatch_header = {'class_credit_head': class_credit_head,
                   'conditional_head': conditional_head,
                   'lastres_head': lastres_head,
                   'maxclass_head': maxclass_head,
                   'maxcredit_head': maxcredit_head,
                   'maxpassfail_head': maxpassfail_head,
                   'maxperdisc_head': maxperdisc_head,
                   'maxterm_head': maxterm_head,
                   'maxtransfer_head': maxtransfer_head,
                   'mingpa_head': mingpa_head,
                   'mingrade_head': mingrade_head,
                   'minclass_head': minclass_head,
                   'mincredit_head': mincredit_head,
                   'minperdisc_head': minperdisc_head,
                   'minres_head': minres_head,
                   'minterm_head': minterm_head,
                   'optional': optional,
                   'proxy_advice': proxy_advice,
                   'remark': remark,
                   'share_head': share_head,
                   'standalone': standalone,
                   'under': under
                   }

dispatch_body = {'block': block,
                 'blocktype': blocktype,
                 'class_credit_body': class_credit_body,
                 'copy_rules': copy_rules,
                 'group_requirement': group_requirement,
                 'conditional_body': conditional_body,
                 'maxperdisc': maxperdisc,
                 'noncourse': noncourse,
                 'proxy_advice': proxy_advice,
                 'remark': remark,
                 'rule_complete': rule_complete,
                 'rule_tag': rule_tag,
                 'subset': subset
                 }


# dispatch()
# -------------------------------------------------------------------------------------------------
def dispatch(ctx: any, institution: str, requirement_id: str):
  """ Invoke the appropriate handler given its top-level context.
  """
  which_part = 'header' if context_path(ctx).lower().startswith('head') else 'body'
  key = class_name(ctx).lower()
  try:
    if which_part == 'header':
      return dispatch_header[key](ctx, institution, requirement_id)
    else:
      return dispatch_body[key](ctx, institution, requirement_id)
  except KeyError as key_error:
    key_error = str(key_error).strip('\'')
    nested = f' while processing “{key}”' if key != key_error else ''
    # Missing handler: report it and recover ever so gracefully
    print(f'No dispatch method for “{key_error}”{nested}: '
          f'{institution=}; {requirement_id=}; {which_part=}', file=sys.stderr)
    if DEBUG:
      print_stack(file=sys.stderr)
    return {'Dispatch_Error':
            {'method': f'“{key_error}”{nested}',
             'institution': institution,
             'requirement_id': requirement_id,
             'part': which_part}}
