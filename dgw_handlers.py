#! /usr/local/bin/python3
""" These are the handlers for all the head and body rule types defined in ReqBlock.g4
    This revised version changes the structure of the dicts, mainly to eliminate the 'tag' key.
"""

import os
import psycopg
import re
import sys

from typing import Any

from dgw_utils import class_name,\
    build_course_list,\
    class_or_credit,\
    concentration_list,\
    context_path,\
    expression_to_str,\
    analyze_expression,\
    get_display,\
    get_groups,\
    get_label,\
    get_nv_pairs,\
    get_rules,\
    get_qualifiers,\
    num_class_or_num_credit

from traceback import print_stack
from pprint import pprint

from psycopg.rows import namedtuple_row

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

  return_dict = {'label': get_label(ctx)}

  return_dict['number'] = int(ctx.NUMBER().getText())
  assert return_dict['number'] == 1, f'Block with number ne 1'

  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      symbols = context.getText().split('=')
  assert isinstance(symbols, list) and len(symbols) == 2, (f'Assertion Error: Invalid block '
                                                           f'expression ('
                                                           f'{ctx.expression().getText()}) '
                                                           f'in block()')
  return_dict['block_type'] = symbols[0].upper().strip()
  return_dict['block_value'] = symbols[1].upper().strip()
  return_dict['institution'] = institution

  if ctx.rule_tag():
    return_dict['rule_tag'] = get_nv_pairs(ctx.rule_tag())

  return {'block': return_dict}


# blocktype()
# -------------------------------------------------------------------------------------------------
def blocktype(ctx, institution, requirement_id):
  """
      blocktype       : NUMBER BLOCKTYPE expression label;

      The expression is a block type, enclosed in parentheses
  """

  return_dict = {'label': get_label(ctx)}

  return_dict['number'] = ctx.NUMBER().getText()

  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['block_type'] = context.getText().strip().upper()

  assert 'block_type' in return_dict.keys(), (f'Assertion Error: Invalid blocktype '
                                              f'({ctx.expression().getText()}) in blocktype()')

  return {'blocktype': return_dict}


# header_class_credit()
# -------------------------------------------------------------------------------------------------
def header_class_credit(ctx, institution, requirement_id):
  """
      header_class_credit   : (num_classes | num_credits)
                            (logical_op (num_classes | num_credits))?
                            (IS? pseudo | display | proxy_advice | header_tag | label | tag)*
                          ;

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;
      allow_clause        : LP allow NUMBER RP;

      Note: header_tag is presentational, and is included here; allow is used for internal degree
      audit logic, and is ignored here.
      And proxy_advice is being ignored, at least for now, because cases where there are template
      placeholders reference values not available from within the Scribe blocks.
"""

  return_dict = {'label': get_label(ctx)}

  return_dict.update(num_class_or_num_credit(ctx))

  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.header_tag():
    return_dict['header_tag'] = get_nv_pairs(ctx.header_tag())

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  if ctx.proxy_advice():
    return_dict.update(proxy_advice(ctx.proxy_advice(), institution, requirement_id))

  return {'header_class_credit': return_dict}


# body_class_credit()
# -------------------------------------------------------------------------------------------------
def body_class_credit(ctx, institution, requirement_id):
  """
body_class_credit : (num_classes | num_credits)
                  (logical_op (num_classes | num_credits))? course_list_body?
                  (display | proxy_advice | remark | share | rule_tag | label | tag )*
                  ;

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;

      course_list_body  : course_list (qualifier tag? | proxy_advice | remark)*;
      course_list_rule  : course_list_body label?;  # (Not actually relevant here)

    Ignore proxy_advice and tag.
  """

  return_dict = {'label': get_label(ctx)}

  return_dict.update(num_class_or_num_credit(ctx))

  if ctx.course_list_body():
    if qualifiers := get_qualifiers(ctx.course_list_body().qualifier(),
                                    institution, requirement_id):
      return_dict.update(qualifiers)

    return_dict.update(build_course_list(ctx.course_list_body().course_list(),
                                         institution, requirement_id))

  # if ctx.pseudo():
  #   return_dict['is_pseudo'] = True

  # display is student-specific
  # if ctx.display():
  #   return_dict['display'] = get_display(ctx)

  if ctx.rule_tag():
    return_dict['rule_tag'] = get_nv_pairs(ctx.rule_tag())

  if ctx.remark():
    return_dict['remark'] = ' '.join([s.getText().strip(' "')
                                     for c in ctx.remark()
                                     for s in c.string()])

  if share_contexts := ctx.share():
    if not isinstance(share_contexts, list):
      share_contexts = [share_contexts]
    return_dict['share'] = '; '.join([share(share_ctx.share(), institution, requirement_id)
                                      for share_ctx in share_contexts])

  return {'class_credit': return_dict}


# header_conditional()
# -------------------------------------------------------------------------------------------------
def header_conditional(ctx, institution, requirement_id):
  """
      header_conditional    : IF expression THEN (head_rule | head_rule_group) else_head?
      else_head       : ELSE (head_rule | head_rule_group) ;
      head_rule_group : (begin_if head_rule+ end_if);
      head_rule         : header_conditional
                        | block
                        | blocktype
                        | header_class_credit
                        | copy_rules
                        | lastres
                        | maxcredit
                        | header_maxpassfail
                        | maxterm
                        | header_maxtransfer
                        | header_minclass
                        | header_mincredit
                        | mingpa
                        | mingrade
                        | header_minperdisc
                        | minres
                        | minterm
                        | noncourse
                        | proxy_advice
                        | remark
                        | rule_complete
                        | header_share
                        ;
  """
  if DEBUG:
    print(f'*** header_conditional({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'condition_str': expression_to_str(ctx.expression())}
  analyze_expression(ctx.expression(), institution, requirement_id)

  if ctx.header_rule():
    return_dict['if_true'] = get_rules(ctx.header_rule(), institution, requirement_id)
  elif ctx.header_rule_group():
    return_dict['if_true'] = get_rules(ctx.header_rule_group().header_rule(),
                                       institution,
                                       requirement_id)
  else:
    return_dict['if_true'] = 'Missing True Part'

  if ctx.header_else():
    if ctx.header_else().header_rule():
      return_dict['if_false'] = get_rules(ctx.header_else().header_rule(),
                                          institution, requirement_id)
    elif ctx.header_else().header_rule_group():
      return_dict['if_false'] = get_rules(ctx.header_else().header_rule_group().header_rule(),
                                          institution, requirement_id)

  return {'conditional': return_dict}


# body_conditional()
# -------------------------------------------------------------------------------------------------
def body_conditional(ctx, institution, requirement_id):
  """ Just like header_conditional, except the rule or rule_group can be followed by requirements
      that apply to the rule or rule group.

      body_conditional  : IF expression THEN (body_rule | body_rule_group) body_else? ;
      body_else         : ELSE (body_rule | body_rule_group);
      body_rule_group : (begin_if body_rule+ end_if);

      body_rule       :block
                      | blocktype
                      | body_class_credit
                      | body_conditional
                      | course_list_rule
                      | copy_rules
                      | group_requirement
                      | noncourse
                      | proxy_advice
                      | remark
                      | rule_complete
                      | subset
                      ;
  """
  if DEBUG:
      print(f'*** body_conditional({class_name(ctx)}, {institution}, {requirement_id})',
            file=sys.stderr)

  return_dict = {}

  condition_str = expression_to_str(ctx.expression())
  return_dict['condition_str'] = condition_str
  analyze_expression(ctx.expression(), institution, requirement_id)

  if ctx.body_rule():
    return_dict['if_true'] = get_rules(ctx.body_rule(), institution, requirement_id)
  elif ctx.body_rule_group():
    return_dict['if_true'] = get_rules(ctx.body_rule_group().body_rule(),
                                       institution, requirement_id)
  else:
    # This can't happen
    return_dict['if_true'] = 'Missing True Part'

  if ctx.body_else():
    if ctx.body_else().body_rule():
      return_dict['if_false'] = get_rules(ctx.body_else().body_rule(),
                                          institution, requirement_id)
    elif ctx.body_else().body_rule_group():
      return_dict['if_false'] = get_rules(ctx.body_else().body_rule_group().body_rule(),
                                          institution, requirement_id)
    else:
      # This can't happen
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
      print(f'*** copy_rules({class_name(ctx)}, {institution}, {requirement_id})',
            file=sys.stderr)

  return_dict = {'institution': institution}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['requirement_id'] = f'{context.getText().strip().upper()}'

  # Look up the block_type and block_value, and build a link to the specified block if possible.
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute(f"""
      select block_type, block_value, period_stop
        from requirement_blocks
       where institution = '{institution}'
         and requirement_id = '{requirement_id}'
      """)
      if cursor.rowcount == 0:
        return_dict['error'] = (f'“Missing {requirement_id}” for {institution}')
      else:
        row = cursor.fetchone()  # There cannot be mnore than one requrement block per requirement id
        block_type = row.block_type
        block_value = row.block_value
        if row.period_stop.startswith('9'):
          return_dict['block_type'] = block_type
          return_dict['block_value'] = block_value
        else:
          return_dict['error'] = (f'{requirement_id} {block_type} {block_block} not current for '
                                  f'{institution}')

  return {'copy_rules': return_dict}


# course_list_rule()
# -------------------------------------------------------------------------------------------------
def course_list_rule(ctx: Any, institution: str, requirement_id: str) -> dict:
  """
    In the body, a bare course list (presumably followed by a label) can serve as a requirement,
    with the implicit assumption that all courses in the list are required.

    CSI01 RA 000544 is the only block observed to use this feature at the top level of the body.

    course_list_body  : course_list (qualifier tag? | proxy_advice | remark)*;
    course_list_rule  : course_list_body label?;
    course_list     : course_item (and_list | or_list)? (except_list | include_list)* proxy_advice?;
  """

  return_dict = {'label': get_label(ctx)}

  course_list_body_ctx = ctx.course_list_body()
  return_dict.update(build_course_list(course_list_body_ctx.course_list(),
                                       institution, requirement_id))
  if course_list_body_ctx.qualifier():
    return_dict.update(get_qualifiers(course_list_body_ctx.qualifier(),
                                      institution, requirement_id))

  if course_list_body_ctx.remark():
    return_dict['remark'] = ' '.join([s.getText().strip(' "')
                                     for c in course_list_body_ctx.remark()
                                     for s in c.string()])

  return {'course_list_rule': return_dict}


# group_requirement()
# -------------------------------------------------------------------------------------------------
def group_requirement(ctx: Any, institution: str, requirement_id: str) -> dict:
  """
        group_requirement : NUMBER GROUP groups (qualifier tag? | proxy_advice | remark)* label? ;
        groups            : group (logical_op group)*; // But only OR should occur
        group             : LP
                           ( block
                           | blocktype
                           | body_class_credit
                           | course_list_rule
                           | group_requirement
                           | noncourse
                           | rule_complete ) (qualifier tag? | proxy_advice | remark)* label?
                           RP ;

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
    requirement_list_dict = {'label': get_label(group_requirement_ctx)}
    requirement_list_dict.update(get_qualifiers(group_requirement_ctx.qualifier(),
                                                institution, requirement_id))

    requirement_list_dict['number'] = group_requirement_ctx.NUMBER().getText()

    requirement_list_dict['group_list'] = get_groups(group_requirement_ctx.groups(),
                                                     institution, requirement_id)

    requirement_list.append({'group_requirement': requirement_list_dict})

  return {'group_requirements': requirement_list}


# header_tag()
# -------------------------------------------------------------------------------------------------
def header_tag(ctx, institution, requirement_id):
  """ header_tag  : (HEADER_TAG nv_pair)+;
      Unused function.
      Header tags are currently ignored, but this method will handle them if that ever changes!
  """
  if DEBUG:
    print(f'*** header_tag({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return {'header_tag': get_nv_pairs(ctx)}


# rule_tag()
# -------------------------------------------------------------------------------------------------
def rule_tag(ctx, institution, requirement_id):
  """ rule_tag  : (RULE_TAG nv_pair)+;
      nv_pair   : nv_lhs '=' nv_rhs;

      Rule tags are currently ignored, but this method will handle them if that ever changes!
  """
  if DEBUG:
    print(f'*** rule_tag({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return {'rule_tag': get_nv_pairs(ctx)}


# lastres()
# -------------------------------------------------------------------------------------------------
def lastres(ctx, institution, requirement_id):
  """
      lastres         : LASTRES NUMBER (OF NUMBER)?
                        class_or_credit
                        course_list? tag? display* proxy_advice?;
  """
  if DEBUG:
    print(f'*** lastres({class_name(ctx)}, {institution}, {requirement_id})',
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


# header_lastres()
# -------------------------------------------------------------------------------------------------
def header_lastres(ctx, institution, requirement_id):
  """
      header_lastres    : lastres label?;
  """
  if DEBUG:
    print(f'*** header_lastres({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  lastres_ctx = ctx.lastres()
  return_dict.update(lastres(lastres_ctx, institution, requirement_id))

  return {'header_lastres': return_dict}


# maxclass()
# --------------------------------------------------------------------------------------------------
def maxclass(ctx, institution, requirement_id):
  """
      maxclass        : MAXCLASS NUMBER course_list? tag?;

      This is actually only a header production
  """
  if DEBUG:
    print(f'*** maxclass({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText().strip()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxclass': return_dict}


# header_maxclass()
# --------------------------------------------------------------------------------------------------
def header_maxclass(ctx, institution, requirement_id):
  """
      header_maxclass   : maxclass label?;
  """
  if DEBUG:
    print(f'*** header_maxclass({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  maxclass_ctx = ctx.maxclass()

  return_dict.update(maxclass(maxclass_ctx, institution, requirement_id))

  return {'header_maxclass': return_dict}


# maxcredit()
# --------------------------------------------------------------------------------------------------
def maxcredit(ctx, institution, requirement_id):
  """
      header_maxcredit  : maxcredit label?;
      maxcredit       : MAXCREDIT NUMBER course_list? tag?;

      This is actually only a header production
  """
  if DEBUG:
    print(f'*** maxcredit({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText().strip()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxcredit': return_dict}


# header_maxcredit()
# --------------------------------------------------------------------------------------------------
def header_maxcredit(ctx, institution, requirement_id):
  """
      header_maxcredit  : maxcredit label?;
  """
  if DEBUG:
    print(f'*** header_maxcredit({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  maxcredit_ctx = ctx.maxcredit()

  return_dict.update(maxcredit(maxcredit_ctx, institution, requirement_id))

  return {'header_maxcredit': return_dict}


# maxpassfail()
# --------------------------------------------------------------------------------------------------
def maxpassfail(ctx, institution, requirement_id):
  """
      maxpassfail      : MAXPASSFAIL NUMBER class_or_credit tag?;
  """
  if DEBUG:
    print(f'*** maxpassfail({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}

  return {'maxpassfail': return_dict}


# header_maxpassfail()
# --------------------------------------------------------------------------------------------------
def header_maxpassfail(ctx, institution, requirement_id):
  """
      header_maxpassfail : maxpassfail label?;
  """
  if DEBUG:
    print(f'*** header_maxpassfail({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  maxpassfail_ctx = ctx.maxpassfail()

  return_dict.update(maxpassfail(maxpassfail_ctx, institution, requirement_id))

  return {'header_maxpassfail': return_dict}


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


# header_maxperdisc()
# -------------------------------------------------------------------------------------------------
def header_maxperdisc(ctx, institution, requirement_id):
  """
      header_maxperdisc : maxperdisc label? ;
  """
  if DEBUG:
    print(f'*** header_maxperdisc({class_name(ctx)=}, {institution=}, {requirement_id=}',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  maxperdisc_ctx = ctx.maxperdisc()
  return_dict.update(maxperdisc(maxperdisc_ctx, institution, requirement_id))

  return {'header_maxperdisc': return_dict}


# maxterm()
# -------------------------------------------------------------------------------------------------
def maxterm(ctx, institution, requirement_id):
  """ maxterm         : MAXTERM NUMBER class_or_credit course_list tag?;
      But the course_list is optional in the body.
  """
  if DEBUG:
    print(f'*** maxterm({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxterm': return_dict}


# header_maxterm()
# -------------------------------------------------------------------------------------------------
def header_maxterm(ctx, institution, requirement_id):
  """ header_maxterm    : maxterm label?;
  """
  if DEBUG:
    print(f'*** maxterm({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  maxterm_ctx = ctx.maxterm()

  return_dict.update(maxterm(maxterm_ctx, institution, requirement_id))

  return {'header_maxterm': return_dict}


# maxtransfer()
# -------------------------------------------------------------------------------------------------
def maxtransfer(ctx, institution, requirement_id):
  """ maxtransfer      : MAXTRANSFER NUMBER class_or_credit (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
  """
  if DEBUG:
    print(f'*** maxtransfer({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  if ctx.SYMBOL():
    symbol_contexts = ctx.SYMBOL()
    return_dict['transfer_types'] = [symbol.getText() for symbol in symbol_contexts]

  return {'maxtransfer': return_dict}


# header_maxtransfer()
# -------------------------------------------------------------------------------------------------
def header_maxtransfer(ctx, institution, requirement_id):
  """
      header_maxtransfer : maxtransfer label?;
  """
  if DEBUG:
    print(f'*** header_maxtransfer({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  maxtransfer_ctx = ctx.maxtransfer()

  return_dict.update(maxtransfer(maxtransfer_ctx, institution, requirement_id))

  return {'header_maxtransfer': return_dict}


# minclass()
# --------------------------------------------------------------------------------------------------
def minclass(ctx, institution, requirement_id):
  """
      minclass        : MINCLASS NUMBER course_list tag? display* label?;
  """
  if DEBUG:
    print(f'*** minclass({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'minclass': return_dict}


# header_minclass()
# --------------------------------------------------------------------------------------------------
def header_minclass(ctx, institution, requirement_id):
  """
      header_minclass     : minclass label?;
  """
  if DEBUG:
    print(f'*** header_minclass({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  minclass_ctx = ctx.minclass()

  return_dict.update(minclass(minclass_ctx, institution, requirement_id))

  return {'header_minclass': return_dict}


# mincredit()
# --------------------------------------------------------------------------------------------------
def mincredit(ctx, institution, requirement_id):
  """
      mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
  """
  if DEBUG:
    print(f'*** mincredit({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'mincredit': return_dict}


# header_mincredit()
# --------------------------------------------------------------------------------------------------
def header_mincredit(ctx, institution, requirement_id):
  """
      header_mincredit     : mincredit label?;
  """
  if DEBUG:
    print(f'*** header_mincredit({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  mincredit_ctx = ctx.mincredit()

  return_dict.update(mincredit(mincredit_ctx, institution, requirement_id))

  return {'header_mincredit': return_dict}


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


# header_mingpa()
# --------------------------------------------------------------------------------------------------
def header_mingpa(ctx, institution, requirement_id):
  """
      header_mingpa     : mingpa label?;
  """
  if DEBUG:
    print(f'*** header_mingpa({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  mingpa_ctx = ctx.mingpa()

  return_dict.update(mingpa(mingpa_ctx, institution, requirement_id))

  return {'header_mingpa': return_dict}


# mingrade()
# -------------------------------------------------------------------------------------------------
def mingrade(ctx, institution, requirement_id):
  """
      mingrade        : MINGRADE NUMBER;
  """
  if DEBUG:
    print(f'*** mingrade({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText()}

  return {'mingrade': return_dict}


# header_mingrade()
# -------------------------------------------------------------------------------------------------
def header_mingrade(ctx, institution, requirement_id):
  """
      header_mingrade   : mingrade label?;
  """
  if DEBUG:
    print(f'*** header_mingrade({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  mingrade_ctx = ctx.mingrade()
  return_dict.update(mingrade(mingrade_ctx, institution, requirement_id))

  return {'header_mingrade': return_dict}


# minperdisc()
# -------------------------------------------------------------------------------------------------
def minperdisc(ctx, institution, requirement_id):
  """
      minperdisc  : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
  """
  if DEBUG:
    print(f'*** minperdisc({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['discipline'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return {'minperdisc': return_dict}


# header_minperdisc()
# -------------------------------------------------------------------------------------------------
def header_minperdisc(ctx, institution, requirement_id):
  """
      header_minperdisc   : minperdisc label?;
  """
  if DEBUG:
    print(f'*** header_minperdisc({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  minperdisc_ctx = ctx.minperdisc()

  return_dict.update(minperdisc(minperdisc_ctx, institution, requirement_id))

  return {'header_minperdisc': return_dict}


# minres()
# -------------------------------------------------------------------------------------------------
def minres(ctx, institution, requirement_id):
  """
      minres      : MINRES (num_classes | num_credits) display* tag?;

      This is actually only a header production
  """
  if DEBUG:
    print(f'*** minres({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = num_class_or_num_credit(ctx)

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'minres': return_dict}


# header_minres()
# -------------------------------------------------------------------------------------------------
def header_minres(ctx, institution, requirement_id):
  """
      header_minres : minres label?;
  """
  if DEBUG:
    print(f'*** header_minres({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  minres_ctx = ctx.minres()

  return_dict = {'label': get_label(ctx)}

  return_dict.update(minres(minres_ctx, institution, requirement_id))

  return {'header_minres': return_dict}


# minterm()
# -------------------------------------------------------------------------------------------------
def minterm(ctx, institution, requirement_id):
  """
      minterm         : MINTERM NUMBER class_or_credit course_list? tag? display*;
  """
  if DEBUG:
    print(f'*** minterm({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'minterm': return_dict}


# header_minterm()
# -------------------------------------------------------------------------------------------------
def header_minterm(ctx, institution, requirement_id):
  """
      header_minterm  : minterm label?;
  """
  if DEBUG:
    print(f'*** header_minterm({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  minterm_ctx = ctx.minterm()

  return_dict.update(minterm(minterm_ctx, institution, requirement_id))

  return {'header_minterm': return_dict}


# noncourse()
# -------------------------------------------------------------------------------------------------
def noncourse(ctx, institution, requirement_id):
  """
      noncourse       : NUMBER NONCOURSE (LP expression RP)? label?;
  """
  if DEBUG:
    print(f'*** noncourse({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx),
                 'number': ctx.NUMBER().getText()}

  try:
    return_dict['expression'] = ctx.expression().getText()
  except AttributeError:
    return_dict['expression'] = None

  return {'noncourse': return_dict}


# optional()
# -------------------------------------------------------------------------------------------------
def optional(ctx, institution, requirement_id):
  """ If present, the block’s requirements are optional.
  """
  if DEBUG:
    print(f'*** optional({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return {'optional': 'This requirement block is not required.'}


# proxy_advice()
# -------------------------------------------------------------------------------------------------
def proxy_advice(proxy_ctx, institution, requirement_id):
  """ proxy_advice    : (PROXY_ADVICE STRING)+;
  """
  if DEBUG:
    print(f'*** proxy_advice({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  proxy_contexts = proxy_ctx if isinstance(proxy_ctx, list) else [proxy_ctx]
  proxy_str = ''
  for proxy_context in proxy_contexts:
    proxy_str += ' '.join([c.getText().strip(' "') for c in proxy_context.STRING()])
  proxy_str = proxy_str.replace('  ', ' ')
  proxy_args = re.findall(r'<.*?>', proxy_str)

  return_dict = {'proxy_advice': {'proxy_str': proxy_str,
                                  'proxy_args': [arg.strip('><') for arg in proxy_args]}}
  # print(return_dict)
  return return_dict


# remark()
# -------------------------------------------------------------------------------------------------
def remark(ctx, institution, requirement_id):
  """ remark          : (REMARK string SEMICOLON?)+;
  """
  if DEBUG:
    print(f'*** remark({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  if not isinstance(remark_contexts := ctx, list):
    remark_contexts = [remark_contexts]
  remark_str = ''
  for remark_context in remark_contexts:
    remark_str += ' '.join([c.getText().strip(' "') for c in remark_context.string()])
  if remark_str:
    return {'remark': remark_str}
  else:
    return {}


# rule_complete()
# -------------------------------------------------------------------------------------------------
def rule_complete(ctx, institution, requirement_id):
  """ rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) (proxy_advice | rule_tag | label)*;
  """
  if DEBUG:
    print(f'*** rule_complete({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  return_dict['is_complete'] = True if ctx.RULE_COMPLETE() else False

  if ctx.rule_tag():
    return_dict['rule_tag'] = get_nv_pairs(ctx.rule_tag())

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


# header_share()
# -------------------------------------------------------------------------------------------------
def header_share(ctx, institution, requirement_id):
  """
      header_share        : share label?;
  """
  if DEBUG:
    print(f'*** header_share({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  share_ctx = ctx.share()

  return_dict.update(share(share_ctx, institution, requirement_id))

  return {'header_share': return_dict}


# standalone()
# -------------------------------------------------------------------------------------------------
def standalone(ctx, institution, requirement_id):
  """
      standalone      : STANDALONE;
  """
  if DEBUG:
    print(f'*** standalone({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return{'standalone': 'This is a standalone requirement block.'}


# subset()
# -------------------------------------------------------------------------------------------------
def subset(ctx, institution, requirement_id):
  """
      subset            : BEGINSUB
                        ( body_conditional
                          | block
                          | blocktype
                          | body_class_credit
                          | copy_rules
                          | course_list_rule
                          | group_requirement
                          | noncourse
                          | rule_complete
                        )+
                        ENDSUB qualifier* (remark | label)*;

  """
  if DEBUG:
    print(f'*** subset({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx)}

  if ctx.body_conditional():
    return_dict['conditional'] = [body_conditional(context, institution, requirement_id)
                                  for context in ctx.body_conditional()]

  if ctx.block():
    return_dict['block'] = [block(context, institution, requirement_id) for context in ctx.block()]

  if ctx.blocktype():
    return_dict['blocktype'] = [blocktype(context, institution, requirement_id)
                                for context in ctx.blocktype()]

  if ctx.body_class_credit():
    # Return a list of class_credit dicts
    return_dict['class_credit_list'] = [body_class_credit(context, institution, requirement_id)
                                        for context in ctx.body_class_credit()]

  if ctx.copy_rules():
    assert len(ctx.copy_rules()) == 1, (f'Assertion Error: {len(ctx.copy_rules())} '
                                        f'is not unity in subset')
    return_dict.update(copy_rules(ctx.copy_rules()[0], institution, requirement_id))

  if ctx.course_list_rule():
    return_dict['course_lists'] = [build_course_list(context.course_list_body().course_list(),
                                                     institution, requirement_id)
                                   for context in ctx.course_list_rule()]

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
    print(f'*** under({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  return_dict = {'label': get_label(ctx),
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return {'under': return_dict}


# Dispatch Tables
# =================================================================================================
""" There are two in case conditional and Share need to be handled differently in Head and Body.
"""
dispatch_header = {'header_class_credit': header_class_credit,
                   'header_conditional': header_conditional,
                   'header_lastres': header_lastres,
                   'header_maxclass': header_maxclass,
                   'header_maxcredit': header_maxcredit,
                   'header_maxpassfail': header_maxpassfail,
                   'header_maxperdisc': header_maxperdisc,
                   'header_maxterm': header_maxterm,
                   'header_maxtransfer': header_maxtransfer,
                   'header_mingpa': header_mingpa,
                   'header_mingrade': header_mingrade,
                   'header_minclass': header_minclass,
                   'header_mincredit': header_mincredit,
                   'header_minperdisc': header_minperdisc,
                   'header_minres': header_minres,
                   'header_minterm': header_minterm,
                   'header_share': header_share,
                   'header_tag': header_tag,
                   'optional': optional,
                   'proxy_advice': proxy_advice,
                   'remark': remark,
                   'standalone': standalone,
                   'under': under
                   }

dispatch_body = {'block': block,
                 'blocktype': blocktype,
                 'body_class_credit': body_class_credit,
                 'body_conditional': body_conditional,
                 'copy_rules': copy_rules,
                 'course_list_rule': course_list_rule,
                 'group_requirement': group_requirement,
                 'noncourse': noncourse,
                 'proxy_advice': proxy_advice,
                 'remark': remark,
                 'rule_complete': rule_complete,
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
      if key == 'header_rule':
        children = ctx.children
        assert len(children) == 1, (f'header_rule with {len(children)} children')
        child = children[0]
        key = class_name(child).lower()
        return dispatch_header[key](child, institution, requirement_id)
      else:
        return dispatch_header[key](ctx, institution, requirement_id)
    else:
      if key == 'body_rule':
        children = ctx.children
        assert len(children) == 1, (f'body_rule with {len(children)} children')
        child = children[0]
        key = class_name(child).lower()
        return dispatch_body[key](child, institution, requirement_id)
      else:
        return dispatch_body[key](ctx, institution, requirement_id)
  except KeyError as key_error:
    key_error = str(key_error).strip('\'')
    nested = f' while processing “{key}”' if key != key_error else ''
    # Missing handler: report it and recover ever so gracefully
    print(f' KEY ERROR “{key_error}”{nested}: '
          f'{institution=}; {requirement_id=}; {which_part=}', file=sys.stderr)
    print_stack()
    return {'Dispatch_Error':
            {'method': f'“{key_error}”{nested}',
             'institution': institution,
             'requirement_id': requirement_id,
             'part': which_part}}
