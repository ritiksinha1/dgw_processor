#! /usr/local/bin/python3
""" These are the handlers for all the head and body rule types defined in ReqBlock.g4
"""

import os
import sys


from dgw_utils import class_name,\
    build_course_list,\
    class_or_credit,\
    context_path,\
    expression_to_str,\
    get_group_list,\
    get_rules,\
    get_qualifiers,\
    get_requirements,\
    num_class_or_num_credit

from traceback import print_stack

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
  return_dict = {'tag': 'block', 'num_blocks': ctx.NUMBER().getText()}

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
def blocktype(ctx, institution, requirement_id):
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
  return_dict = {'tag': 'class_credit'}
  return_dict.update(num_class_or_num_credit(ctx))

  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

    if ctx.label():
      if isinstance(ctx.label(), list):
        return_dict['label'] = ''
        for context in ctx.label():
          return_dict['label'] += ' '.join([context.string().getText().strip(' "')])
      else:
        return_dict['label'] = ctx.label().string().getText().strip(' "')
    else:
      return_dict['label'] = None

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
      allow_clause        : LP allow NUMBER RP;

      course_list_body           : course_list (course_list_body_qualifier tag?
                                               | proxy_advice
                                               | label
                                               )*;
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

      "Allowable rule qualifiers: DontShare, Exclusive, Hide, HideRule, HighPriority, LowPriority,
      LowestPriority, MaxPassFail, MaxPerDisc, MaxSpread, MaxTerm, MaxTransfer, MinAreas, MinGrade,
      MinPerDisc, MinSpread, MinTerm, NotGPA, ProxyAdvice, RuleTag, SameDisc, ShareWith, With."
  """
  # Labels can appear in different contexts
  course_list_label = course_list_body_label = class_credit_label = None

  return_dict = {'tag': 'class_credit'}
  return_dict.update(num_class_or_num_credit(ctx))
  if ctx.course_list_body():
    return_dict['courses'] = build_course_list(ctx.course_list_body().course_list(),
                                               institution, requirement_id)
    if 'label' in return_dict['courses'].keys():
      course_list_label = return_dict['courses']['label']

    if context := ctx.course_list_body().course_list_body_qualifier():
      return_dict['qualifiers'] = get_qualifiers(context, institution, requirement_id)

  return_dict['is_pseudo'] = True if ctx.pseudo() else False

  if ctx.share():
    return_dict['share'] = share(ctx.share(), institution, requirement_id)

  if ctx.remark():
    return_dict.update(remark(ctx.remark(), institution, requirement_id))

  if ctx.display():
    display_text = ''
    for item in ctx.display():
      display_text += item.string().getText().strip(' "') + ' '
    return_dict['display'] = display_text.strip()

  if ctx.course_list_body() and ctx.course_list_body().label():
    if isinstance(ctx.course_list_body().label(), list):
      course_list_body_label = ''
      for context in ctx.course_list_body().label():
        course_list_body_label += ' '.join([context.string().getText().strip(' "')])
    else:
      course_list_body_label = ctx.course_list_body().label().string().getText().strip(' "')

  if ctx.label():
    if isinstance(ctx.label(), list):
      class_credit_label = ''
      for context in ctx.label():
        class_credit_label += ' '.join([context.string().getText().strip(' "')])
    else:
      class_credit_label = ctx.label().string().getText().strip(' "')

  # How many labels are there?
  labels = [course_list_label, course_list_body_label, class_credit_label]
  if (len(labels) - labels.count(None)) > 2:
    print(f'Ambiguous label situation: {course_list_label=} {course_list_body_label=} '
          f'{class_credit_label=}')
  if course_list_body_label:
    return_dict['label'] = course_list_body_label
  if class_credit_label:
    return_dict['label'] = class_credit_label

  return return_dict


# copy_rules()
# -------------------------------------------------------------------------------------------------
def copy_rules(ctx, institution, requirement_id):
  """
      copy_rules      : COPY_RULES expression SEMICOLON?;

      The expression is a requirement_id enclosed in parentheses (RA######).
  """
  return_dict = {'tag': 'copy_rules', 'institution': institution}
  for context in ctx.expression().getChildren():
    if class_name(context) == 'Expression':
      return_dict['requirement_id'] = f'{institution} {context.getText().strip().upper()}'

  assert 'requirement_id' in return_dict.keys(), f'Invalid CopyRules {ctx.expression().getText()}'

  return return_dict


# group()
# -------------------------------------------------------------------------------------------------
def group(ctx, institution, requirement_id):
  """
group           : NUMBER GROUP group_list requirement* label? ;
group_list      : group_item (logical_op group_item)*; // But only OR should occur
group_item      : LP
                  (block
                   | blocktype
                   | course_list
                   | class_credit_body
                   | group
                   | noncourse
                   | rule_complete)
                  requirement* label?
                  RP
                ;

requirement           : maxpassfail
                      | maxperdisc
                      | maxtransfer
                      | minclass
                      | mincredit
                      | mingpa
                      | mingrade
                      | minperdisc
                      | proxy_advice
                      | samedisc
                      | rule_tag
                      | share
                      ;

  “Qualifiers that must be applied to all rules in the group list must occur after the last right
  parenthesis and before the label at the end of the Group statement. Qualifiers that apply only to
  a specific rule in the group list must appear inside the parentheses for that group item rule.”

  Allowable rule qualifiers: DontShare, Hide, HideRule, HighPriority, LowPriority, LowestPriority,
  MaxPassFail, MaxPerDisc, MaxTransfer, MinGrade, MinPerDisc, NotGPA, ProxyAdvice, SameDisc,
  ShareWith, MinClass, MinCredit, RuleTag.
  """
  return_dict = {'tag': 'groups', 'num_groups_required': ctx.NUMBER().getText()}

  if len(ctx.requirement()) > 0:
    return_dict['requirements'] = get_requirements(ctx.requirement(), institution, requirement_id)

  return_dict['group'] = get_group_list(ctx.group_list(), institution, requirement_id)

  # return_dict['develoment_status'] = 'Under development: incomplete'
  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# header_tag()
# -------------------------------------------------------------------------------------------------
def header_tag(ctx, institution, requirement_id):
  """ header_tag  : (HEADER_TAG nv_pair)+;
  """
  return_dict = {'tag': 'header_tag'}
  return return_dict


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

  return_dict = {'tag': 'rule_tag_list'}
  tag_list = []
  for rule_tag in rule_tags:
    for pair in rule_tag.nv_pair():
      name = pair.SYMBOL()[0].getText()
      value = pair.STRING().getText() if len(pair.SYMBOL()) == 1 else pair.SYMBOL()[1].getText()
      tag_list.append({'tag': 'rule_tag', 'name': name, 'value': value})
    return_dict['name_value'] = tag_list
  return return_dict


# if_then_head()
# -------------------------------------------------------------------------------------------------
def if_then_head(ctx, institution, requirement_id):
  """
      if_then_head    : IF expression THEN (head_rule | head_rule_group )
                        (proxy_advice | label)* else_head?;
      else_head       : ELSE (head_rule | head_rule_group)
                        (proxy_advice | label)*;
      head_rule_group : (begin_if head_rule+ end_if);
      head_rule       : if_then_head
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

  return_dict = {'tag': 'if-then', 'condition': expression_to_str(ctx.expression())}

  if ctx.label():
    assert isinstance(ctx.label(), list)
    label_str = ' '.join([label.string() for label in ctx.label()])
    if label_str != '':
      return_dict['label'] = label_str

  if ctx.head_rule():
    return_dict['if_true'] = get_rules(ctx.head_rule(), institution, requirement_id)
  elif ctx.head_rule_group():
    return_dict['if_true'] = get_rules(ctx.head_rule_group(), institution, requirement_id)
  else:
    return_dict['if_true'] = 'Missing True Part'

  if ctx.else_head():
    if ctx.else_head().head_rule():
      return_dict['if_false'] = get_rules(ctx.else_head().head_rule(),
                                          institution, requirement_id)
    elif ctx.else_head().head_rule_group():
      return_dict['if_false'] = get_rules(ctx.else_head().head_rule_group(),
                                          institution, requirement_id)
    else:
      return_dict['if_false'] = 'Missing False Part'

  return return_dict


# if_then_body()
# -------------------------------------------------------------------------------------------------
def if_then_body(ctx, institution, requirement_id):
  """ Just like if_then_head, except the rule or rule_group can be followed by requirements that
      apply to the rule or rule group.

      if_then_body    : IF expression THEN (body_rule | body_rule_group)
                        requirement* label? else_body?;
      else_body       : ELSE (body_rule | body_rule_group)
                        requirement* label?;
      body_rule_group : (begin_if body_rule+ end_if);

      body_rule       : if_then_body
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

      requirement     : maxpassfail
                      | maxperdisc
                      | maxtransfer
                      | minclass
                      | mincredit
                      | mingpa
                      | mingrade
                      | minperdisc
                      | proxy_advice
                      | samedisc
                      | rule_tag
                      | share
                      ;
  """
  return_dict = {'tag': 'if-then', 'condition': expression_to_str(ctx.expression())}

  if ctx.label():
    label_str = ''
    if isinstance(ctx.label(), list):
      label_str = ' '.join([label.string() for label in ctx.label()])
    else:
      label_str = ctx.label().string().getText()
    if label_str != '':
      return_dict['label'] = label_str

  if ctx.requirement():
    return_dict['requirements'] = [get_rules(context, institution, requirement_id)
                                   for context in ctx.requirement()]

  if ctx.body_rule():
    return_dict['if_true'] = get_rules(ctx.body_rule(), institution, requirement_id)
  elif ctx.body_rule_group():
    return_dict['if_true'] = get_rules(ctx.body_rule_group(), institution, requirement_id)
  else:
    return_dict['if_true'] = 'Missing True Part'

  if ctx.else_body():
    if ctx.else_body().body_rule():
      return_dict['if_false'] = get_rules(ctx.else_body().body_rule(),
                                          institution, requirement_id)
    elif ctx.else_body().body_rule_group():
      return_dict['if_false'] = get_rules(ctx.else_body().body_rule_group(),
                                          institution, requirement_id)
    else:
      return_dict['if_false'] = 'Missing False Part'

  return return_dict


# lastres()
# -------------------------------------------------------------------------------------------------
def lastres(ctx, institution, requirement_id):
  """
      lastres         : LASTRES NUMBER (OF NUMBER)?
                        class_or_credit
                        course_list? tag? display* label?;
  """
  return_dict = {'tag': 'lastres', 'class_or_credit': class_or_credit(ctx.class_or_credit())}

  numbers = ctx.NUMBER()
  return_dict['min_number'] = numbers.pop().getText().strip()
  if len(numbers) > 0:
    return_dict['of_number'] = numbers.pop().getText().strip()

  assert len(numbers) == 0

  if ctx.course_list():
    return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)

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
def maxclass(ctx, institution, requirement_id):
  """
      maxclass        : MAXCLASS NUMBER course_list? tag?;
  """
  return_dict = {'tag': 'max_class',
                 'max_classes_allowed': ctx.NUMBER().getText().strip()}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)
  return return_dict


# maxcredit()
# --------------------------------------------------------------------------------------------------
def maxcredit(ctx, institution, requirement_id):
  """
      maxcredit       : MAXCREDIT NUMBER course_list? tag?;
  """
  return_dict = {'tag': 'max_credit',
                 'max_credits_allowed': ctx.NUMBER().getText().strip()}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)

  return return_dict


# maxpassfail()
# --------------------------------------------------------------------------------------------------
def maxpassfail(ctx, institution, requirement_id):
  """
      maxpassfail     : MAXPASSFAIL NUMBER class_or_credit tag?;
  """
  return_dict = {'tag': 'max_pass-fail',
                 'max_passfail_allowed': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return return_dict


# maxperdisc()
# -------------------------------------------------------------------------------------------------
def maxperdisc(ctx, institution, requirement_id):
  """
      maxperdisc      : MAXPERDISC NUMBER class_or_credit LP SYMBOL (list_or SYMBOL)* RP tag?;
  """
  return_dict = {'tag': 'max_per-disc',
                 'max_allowed_per_discipline': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['disciplines'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return return_dict


# maxterm()
# -------------------------------------------------------------------------------------------------
def maxterm(ctx, institution, requirement_id):
  """
      maxterm         : MAXTERM NUMBER class_or_credit course_list tag?;
  """
  return_dict = {'tag': 'max_term',
                 'max_number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)

  return return_dict


# maxtransfer()
# -------------------------------------------------------------------------------------------------
def maxtransfer(ctx, institution, requirement_id):
  """
      maxtransfer     : MAXTRANSFER NUMBER class_or_credit (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
  """
  return_dict = {'tag': 'max_transfer',
                 'max_number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  if ctx.SYMBOL():
    symbol_contexts = ctx.SYMBOL()
    return_dict['transfer_types'] = [symbol.getText() for symbol in symbol_contexts]

  return return_dict


# minclass()
# --------------------------------------------------------------------------------------------------
def minclass(ctx, institution, requirement_id):
  """
      minclass        : MINCLASS NUMBER course_list tag? display* label?;
  """
  return_dict = {'tag': 'min_class',
                 'min_number': ctx.NUMBER().getText(),
                 'courses': build_course_list(ctx.course_list(), institution, requirement_id)}

  if ctx.display():
    return_dict['display'] = ' '.join([item.string().getText().strip(' "')
                                      for item in ctx.display()]).strip()

  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip(' "')

  return return_dict


# mincredit()
# --------------------------------------------------------------------------------------------------
def mincredit(ctx, institution, requirement_id):
  """
      mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
  """
  return_dict = {'tag': 'min_credit',
                 'min_number': ctx.NUMBER().getText()}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)

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
def mingpa(ctx, institution, requirement_id):
  """
      mingpa          : MINGPA NUMBER (course_list | expression)? tag? display* label?;
  """
  return_dict = {'tag': 'min_gpa', 'min_number': ctx.NUMBER().getText()}

  if ctx.course_list():
    return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)

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
def mingrade(ctx, institution, requirement_id):
  """
      mingrade        : MINGRADE NUMBER;
  """
  return {'tag': 'min_grade', 'min_number': ctx.NUMBER().getText()}


# minperdisc()
# -------------------------------------------------------------------------------------------------
def minperdisc(ctx, institution, requirement_id):
  """
      minperdisc  : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
  """
  return_dict = {'tag': 'min_per-disc',
                 'min_number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['discipline'] = [discp.getText().upper() for discp in ctx.SYMBOL()]

  return return_dict


# minres()
# -------------------------------------------------------------------------------------------------
def minres(ctx, institution, requirement_id):
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
def noncourse(ctx, institution, requirement_id):
  """
      noncourse       : NUMBER NONCOURSE LP expression RP label?;
  """
  return_dict = {'tag': 'noncourse',
                 'number': ctx.NUMBER().getText(),
                 'expression': ctx.expression().getText(),
                 'Development status': 'Expression not interpreted yet'}  # Not interpreted (yet)

  return return_dict


# optional()
# -------------------------------------------------------------------------------------------------
def optional(ctx, institution, requirement_id):
  """ If present, the block’s requirements are optional.
  """
  return {'tag': 'optional'}


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
  remark_str = ''
  if isinstance(ctx, list):
    for context in ctx:
      remark_str += ' '.join([s.getText().strip(' "') for s in context.string()])
  else:
    remark_str += ' '.join([s.getText().strip(' "') for s in ctx.string()])
  return_dict = {'tag': 'remark',
                 'text': remark_str}
  return return_dict


# rule_complete()
# -------------------------------------------------------------------------------------------------
def rule_complete(ctx, institution, requirement_id):
  """ rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) (proxy_advice | rule_tag | label)*;
  """
  return_dict = {'tag': 'rule_complete'}
  return_dict['is_complete?'] = True if ctx.RULE_COMPLETE() else False

  if ctx.label():
    return_dict['label'] = ' '.join([context.string().getText().strip(' "')
                                     for context in ctx.label()])

  if ctx.rule_tag():
    return_dict['rule_tag'] = rule_tag(ctx.rule_tag(), institution, requirement_id)

  if ctx.label():
    return_dict['label'] = ' '.join([context.string().getText().strip(' "')
                                     for context in ctx.label()])

  return return_dict


# share()
# -------------------------------------------------------------------------------------------------
def share(ctx, institution, requirement_id):
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
def standalone(ctx, institution, requirement_id):
  """
      standalone      : STANDALONE;
  """
  return{'tag': 'standalone'}


# subset_body()
# -------------------------------------------------------------------------------------------------
def subset(ctx, institution, requirement_id):
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
                        ENDSUB subset_qualifier* (remark | label)*;

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

  if len(ctx.if_then_body()) > 0:
    return_dict['if_then'] = [if_then_body(context, institution, requirement_id)
                              for context in ctx.if_then_body()]

  if len(ctx.block()) > 0:
    return_dict['block'] = [block(context, institution, requirement_id) for context in ctx.block()]

  if len(ctx.blocktype()) > 0:
    return_dict['blocktype'] = [blocktype(context, institution, requirement_id)
                                for context in ctx.blocktype()]

  if len(ctx.class_credit_body()) > 0:
    # Return a list of class_credit dicts
    return_dict['class_credit'] = [class_credit_body(context, institution, requirement_id)
                                   for context
                                   in ctx.class_credit_body()]

  if len(ctx.copy_rules()) > 0:
    assert len(ctx.copy_rules()) == 1
    return_dict['copy_rules'] = copy_rules(ctx.copy_rules()[0], institution, requirement_id)

  if len(ctx.course_list()) > 0:
    return_dict['courses'] = [build_course_list(context, institution, requirement_id)
                              for context in ctx.course_list()]

  if len(ctx.group()) > 0:
    return_dict['group'] = [group(context, institution, requirement_id) for context in ctx.group()]

  if len(ctx.noncourse()) > 0:
    return_dict['noncourse'] = [noncourse(context, institution, requirement_id)
                                for context in ctx.noncourse()]

  if len(ctx.rule_complete()) > 0:
    assert len(ctx.rule_complete()) == 1
    return_dict['rule_complete'] = rule_complete(ctx.rule_complete()[0],
                                                 institution, requirement_id)

  try:
    label_ctx = ctx.label()
    if len(label_ctx) > 1:
      print(f'Multiple ({len(label_ctx)}) labels at {context_path(ctx)}', file=sys.stderr)
    label_ctx = label_ctx.pop()
    return_dict['label'] = label_ctx.string().getText().strip(' "')
  except (KeyError, IndexError):
    # No label: note it
    return_dict['label'] = 'No Label for this subset!'

  try:
    if len(ctx.remark()) > 1:
      print(f'Multiple ({len(ctx.remark())}) remarks at {context_path(ctx)}', file=sys.stderr)
    context = ctx.remark().pop()
    remark_str = ' '.join([s.getText().strip(' "') for s in context.string()])
    return_dict['remark'] = remark_str
  except (KeyError, IndexError):
    pass

  return return_dict


# under()
# -------------------------------------------------------------------------------------------------
def under(ctx, institution, requirement_id):
  """
      under           : UNDER NUMBER class_or_credit course_list display* label;
  """
  return_dict = {'tag': 'under',
                 'number': ctx.NUMBER().getText(),
                 'class_or_credit': class_or_credit(ctx.class_or_credit())}
  return_dict['courses'] = build_course_list(ctx.course_list(), institution, requirement_id)

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
    'header_tag': header_tag,
    'if_then_head': if_then_head,
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
    'group': group,
    'if_then_body': if_then_body,
    'noncourse': noncourse,
    'proxy_advice': proxy_advice,
    'remark': remark,
    'rule_complete': rule_complete,
    'rule_tag': rule_tag,
    'subset': subset
}


# dispatch()
# -------------------------------------------------------------------------------------------------
def dispatch(ctx: any, institution: str, requirement_id: str, which_part: str):
  """ Invoke the appropriate handler given its top-level context.
  """
  key = class_name(ctx).lower()
  try:
    if which_part == 'head':
      return dispatch_head[key](ctx, institution, requirement_id)
    else:
      return dispatch_body[key](ctx, institution, requirement_id)
  except KeyError as key_error:
    key_error = str(key_error).strip('\'')
    nested = f' while processing “{key}”' if key != key_error else ''
    if DEBUG:
      # Missing handler: report it and recover ever so gracefully
      # print_stack(file=sys.stderr)
      print(f'No dispatch method for “{key_error}”{nested}: '
            f'{institution=}; {requirement_id=}; {which_part=}', file=sys.stderr)
    return {'tag': 'Dispatch_Error',
            'method': f'“{key_error}”{nested}',
            'institution': institution,
            'requirement_id': requirement_id,
            'part': which_part}
