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
  assert isinstance(symbols, list) and len(symbols) == 2, (f'Invalid block expression: '
                                                           f'{ctx.expression().getText()}')
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

  assert 'block_type' in return_dict.keys(), f'Invalid blocktype {ctx.expression().getText()}'

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

      Note: header_tag is used only for audit presentation, and is ignored here.
"""
  return_dict = num_class_or_num_credit(ctx)

  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return return_dict


# class_credit_body()
# -------------------------------------------------------------------------------------------------
def class_credit_body(ctx, institution, requirement_id):
  """
      class_credit_body   : (num_classes | num_credits)
                            (logical_op (num_classes | num_credits))? course_list_body?
                            (IS? pseudo
                             | display
                             | proxy_advice
                             | remark
                             | rule_tag
                             | share
                             | tag
                            )*
                            label?;

      num_classes         : NUMBER CLASS allow_clause?;
      num_credits         : NUMBER CREDIT allow_clause?;

      course_list_body           : course_list (qualifier tag?
                                                | proxy_advice
                                                | label
                                                )*;

    Ignore rule_tag and tag.
  """
  if DEBUG:
    print(f'*** class_credit_body({class_name(ctx)=}, {institution=}, {requirement_id=})',
          file=sys.stderr)
  return_dict = num_class_or_num_credit(ctx)

  if ctx.course_list_body():
    if qualifiers := get_qualifiers(ctx.course_list_body().qualifier(),
                                    institution, requirement_id):
      if DEBUG:
        print(f'{qualifiers=}', file=sys.stderr)
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
    return_dict['share'] = '; '.join([share(ctx.share(), institution, requirement_id)
                                     for ctx in share_contexts])

  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  if DEBUG:
    pprint(return_dict, stream=sys.stderr)

  return return_dict


# conditional_head()
# -------------------------------------------------------------------------------------------------
def conditional_head(ctx, institution, requirement_id):
  """
      conditional_head    : IF expression THEN (head_rule | head_rule_group)
                        (proxy_advice | label)* else_head?;
      else_head       : ELSE (head_rule | head_rule_group)
                        (proxy_advice | label)*;
      head_rule_group : (begin_if head_rule+ end_if);
      head_rule       : conditional_head
                      | block
                      | blocktype
                      | class_credit_head
                      | copy_rules
                      | lastres
                      | maxcredit
                      | maxpassfail
                      | maxterm
                      | maxtransfer
                      | minclass
                      | mincredit
                      | mingpa
                      | mingrade
                      | minperdisc
                      | minres
                      | minterm
                      | noncourse
                      | proxy_advice
                      | remark
                      | rule_complete
                      | share
                      | subset
                      ;
  """

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
                      | group
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
  return_dict = dict()
  condition = expression_to_str(ctx.expression())
  return_dict['condition'] = condition

  # Concentrations not implemented yet
  # if 'conc' in condition.lower():
  #   return_dict['concentrations'] = concentration_list(condition,
  #                                                      institution,
  #                                                      requirement_id)

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
  return_dict = {'institution': institution}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['requirement_id'] = f'{context.getText().strip().upper()}'

  assert 'requirement_id' in return_dict.keys(), f'Invalid CopyRules {ctx.expression().getText()}'

  return {'copy_rules': return_dict}


# group_requirement()
# -------------------------------------------------------------------------------------------------
def group_requirement(ctx, institution, requirement_id):
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
  return_dict = {'number': ctx.NUMBER().getText()}

  return_dict['groups'] = get_groups(ctx.groups(), institution, requirement_id)

  if ctx.label():
    return_dict['label'] = get_label(ctx)

  if ctx.qualifier():
    return_dict.update(get_qualifiers(ctx.qualifier(), institution, requirement_id))

  return return_dict


# header_tag()
# -------------------------------------------------------------------------------------------------
def header_tag(ctx, institution, requirement_id):
  """ header_tag  : (HEADER_TAG nv_pair)+;
  """
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
                        course_list? tag? display* label?;
  """
  return_dict = {'class_or_credit': class_or_credit(ctx.class_or_credit())}

  numbers = ctx.NUMBER()
  return_dict['number'] = numbers.pop().getText().strip()
  if len(numbers) > 0:
    return_dict['of_number'] = numbers.pop().getText().strip()

  assert len(numbers) == 0

  if ctx.course_list():
    return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return {'lastres': return_dict}


# maxclass()
# --------------------------------------------------------------------------------------------------
def maxclass(ctx, institution, requirement_id):
  """
      maxclass        : MAXCLASS NUMBER course_list? tag?;
  """
  return_dict = {'number': ctx.NUMBER().getText().strip()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))
  return {'maxclass': return_dict}


# maxcredit()
# --------------------------------------------------------------------------------------------------
def maxcredit(ctx, institution, requirement_id):
  """
      maxcredit       : MAXCREDIT NUMBER course_list? tag?;
  """
  return_dict = {'number': ctx.NUMBER().getText().strip()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxcredit': return_dict}


# maxpassfail()
# --------------------------------------------------------------------------------------------------
def maxpassfail(ctx, institution, requirement_id):
  """
      maxpassfail     : MAXPASSFAIL NUMBER class_or_credit tag?;
  """
  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return {'maxpassfail': return_dict}


# maxperdisc()
# -------------------------------------------------------------------------------------------------
def maxperdisc(ctx, institution, requirement_id):
  """
      maxperdisc      : MAXPERDISC NUMBER class_or_credit LP SYMBOL (list_or SYMBOL)* RP tag?;
  """
  if DEBUG:
    print(f'*** maxperdisc({class_name(ctx)=}, {institution=}, {requirement_id=}', file=sys.stderr)

  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['disciplines'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return {'maxperdisc': return_dict}


# maxterm()
# -------------------------------------------------------------------------------------------------
def maxterm(ctx, institution, requirement_id):
  """
      maxterm         : MAXTERM NUMBER class_or_credit course_list tag?;
  """
  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  return {'maxterm': return_dict}


# maxtransfer()
# -------------------------------------------------------------------------------------------------
def maxtransfer(ctx, institution, requirement_id):
  """
      maxtransfer     : MAXTRANSFER NUMBER class_or_credit (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
  """
  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  if ctx.SYMBOL():
    symbol_contexts = ctx.SYMBOL()
    return_dict['transfer_types'] = [symbol.getText() for symbol in symbol_contexts]

  return {'maxtransfer': return_dict}


# minclass()
# --------------------------------------------------------------------------------------------------
def minclass(ctx, institution, requirement_id):
  """
      minclass        : MINCLASS NUMBER course_list tag? display* label?;
  """
  return_dict = {'number': ctx.NUMBER().getText(),
                 'courses': build_course_list(ctx.course_list(), institution, requirement_id)}

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return {'minclass': return_dict}


# mincredit()
# --------------------------------------------------------------------------------------------------
def mincredit(ctx, institution, requirement_id):
  """
      mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
  """
  return_dict = {'number': ctx.NUMBER().getText()}
  return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return {'mincredit': return_dict}


# mingpa()
# --------------------------------------------------------------------------------------------------
def mingpa(ctx, institution, requirement_id):
  """
      mingpa          : MINGPA NUMBER (course_list | expression)? tag? display* label?;

      MinGPA is a standalone property when it appears in the header, and we think it doesn't include
      anything but the number. In the body, it's a qualifier, and the other parts can appear. The
      returned dict accommodates both scenarios.
  """
  return_dict = {'number': ctx.NUMBER().getText()}

  if ctx.course_list():
    return_dict.update(build_course_list(ctx.course_list(), institution, requirement_id))

  if ctx.expression():
    return_dict['expression'] = ctx.expression().getText()

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  if ctx.label():
    return_dict['label'] = get_label(ctx)

  return {'mingpa': return_dict}


# mingrade()
# -------------------------------------------------------------------------------------------------
def mingrade(ctx, institution, requirement_id):
  """
      mingrade        : MINGRADE NUMBER;
  """
  return {'mingrade': {'number': ctx.NUMBER().getText()}}


# minperdisc()
# -------------------------------------------------------------------------------------------------
def minperdisc(ctx, institution, requirement_id):
  """
      minperdisc  : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
  """
  return_dict = {'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['discipline'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return {'minperdisc': return_dict}


# minres()
# -------------------------------------------------------------------------------------------------
def minres(ctx, institution, requirement_id):
  """ minres          : MINRES (num_classes | num_credits) display* label? tag?;
  """
  return_dict = num_class_or_num_credit(ctx)

  if ctx.display():
    return_dict['display'] = get_display(ctx)

  return_dict['label'] = get_label(ctx)

  return {'minres': return_dict}


# noncourse()
# -------------------------------------------------------------------------------------------------
def noncourse(ctx, institution, requirement_id):
  """
      noncourse       : NUMBER NONCOURSE LP expression RP label?;
  """
  return_dict = {'number': ctx.NUMBER().getText(),
                 'expression': ctx.expression().getText(),
                 'Development status': 'Expression not interpreted yet'}  # Not interpreted (yet)

  return {'noncourse': return_dict}


# optional()
# -------------------------------------------------------------------------------------------------
def optional(ctx, institution, requirement_id):
  """ If present, the block’s requirements are optional.
  """
  return {'optional': 'This requirement block is not required.'}


# proxy_advice()
# -------------------------------------------------------------------------------------------------
def proxy_advice(ctx, institution, requirement_id):
  """ Recognizing this, but no plans to do anything with it.
  """
  return {}


# remark()
# -------------------------------------------------------------------------------------------------
def remark(ctx, institution, requirement_id):
  """ remark          : (REMARK string SEMICOLON?)+;
  """
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
  return_dict = dict()
  return_dict['is_complete?'] = True if ctx.RULE_COMPLETE() else False

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
  return_dict = dict()

  if ctx.SHARE():
    return_dict['share_type'] = 'allow sharing'
  else:
    return_dict['share_type'] = 'exclusive'

  if ctx.NUMBER():
    return_dict['number'] = ctx.NUMBER().getText().strip()
    return_dict['class_or_credit'] = class_or_credit(ctx.class_or_credit())
  if ctx.expression():
    return_dict['expression'] = ctx.expression().getText()

  return {'share': return_dict}


# standalone()
# -------------------------------------------------------------------------------------------------
def standalone(ctx, institution, requirement_id):
  """
      standalone      : STANDALONE;
  """
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
    assert len(ctx.copy_rules()) == 1
    return_dict.update(copy_rules(ctx.copy_rules()[0], institution, requirement_id))

  if ctx.course_list():
    return_dict['course_lists'] = [build_course_list(context, institution, requirement_id)
                                   for context in ctx.course_list()]

  if ctx.group_requirement():
    return_dict['group_requirements'] = [group_requirement(context, institution, requirement_id)
                                         for context in ctx.group_requirement()]

  if ctx.noncourse():
    return_dict['noncourse'] = [noncourse(context, institution, requirement_id)
                                for context in ctx.noncourse()]

  if ctx.rule_complete():
    assert len(ctx.rule_complete()) == 1
    return_dict['rule_complete'] = rule_complete(ctx.rule_complete()[0],
                                                 institution, requirement_id)

  if qualifiers := get_qualifiers(ctx, institution, requirement_id):
    return_dict.update(qualifiers)

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
  """
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
dispatch_header = {
    'class_credit_head': class_credit_head,
    'header_tag': header_tag,
    'conditional_head': conditional_head,
    'lastres': lastres,
    'maxclass': maxclass,
    'maxcredit': maxcredit,
    'maxpassfail': maxpassfail,
    'maxperdisc': maxperdisc,
    'maxterm': maxterm,
    'maxtransfer': maxtransfer,
    'minclass': minclass,
    'mincredit': mincredit,
    'mingpa': mingpa,
    'mingrade': mingrade,
    'minperdisc': minperdisc,
    'minres': minres,
    'optional': optional,
    'proxy_advice': proxy_advice,
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
    # print_stack(file=sys.stderr)
    if DEBUG:
      # Missing handler: report it and recover ever so gracefully
      print(f'No dispatch method for “{key_error}”{nested}: '
            f'{institution=}; {requirement_id=}; {which_part=}', file=sys.stderr)
    return {'Dispatch_Error':
            {'method': f'“{key_error}”{nested}',
             'institution': institution,
             'requirement_id': requirement_id,
             'part': which_part}}
