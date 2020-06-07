#! /usr/local/bin/python3

import os
import sys

from antlr4 import *

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener

from closeable_objects import dict2html, items2html
from dgw_utils import catalog_years, colleges, ScribeSection, get_number, class_or_credit

DEBUG = os.getenv('DEBUG_INTERPRETER')


# Class ReqBlockInterpreter(ReqBlockListener)
# =================================================================================================
class ReqBlockInterpreter(ReqBlockListener):
  def __init__(self, institution, block_type, block_value, title, period_start, period_stop,
               requirement_text):
    """ Lists of Requirements, ShareLists, and possibly other named tuples for the Head and Body
        setions of a Requirement Block are populated as the parse tree is walked for a particular
        Block. Each named tuple starts with a keyword
    """

    if DEBUG:
      print(f'*** ReqBlockInterpreter({institution}, {block_type}, {block_value})', file=sys.stderr)
    self.institution = institution
    self.block_type = block_type
    self.block_type_str = (block_type.lower()
                           .replace('conc', 'concentration')
                           .replace('other', 'other requirement'))
    self.block_value = block_value
    self.title = title
    self.catalog_years = catalog_years(period_start, period_stop)
    self.period_stop = period_stop
    self.institution_name = colleges[institution]
    self.requirement_text = requirement_text
    self.scribe_section = ScribeSection.NONE
    self.sections = [None, [], []]  # NONE, HEAD, BODY

  @property
  def html(self):
    # Add line numbers to requirements text for development purposes.
    num_lines = self.requirement_text.count('\n')
    lines_pre = '<pre class="line-numbers">'
    for line in range(num_lines):
      lines_pre += f'{line + 1:03d}  \n'
    lines_pre += '</pre>'

    html_body = f"""
<h1>{self.institution_name} {self.title}</h1>
<p>Requirements for Catalog Years
{self.catalog_years.text}
</p>
<section>
  <h1 class="closer">Degreeworks Code</h1>
  <div>
    <hr>
    <section class=with-numbers>
      {lines_pre}
      <pre>{self.requirement_text.replace('<','&lt;')}</pre>
    </section
  </div>
</section>
<section>
  <h1 class="closer">Extracted Requirements</h1>
  <div>
    <hr>
    {items2html(self.sections[ScribeSection.HEAD.value], 'Head Item')}
    {items2html(self.sections[ScribeSection.BODY.value], 'Body Item')}
  </div>
</section
"""

    return html_body

  # ReqBlockListener Overrides
  # ===============================================================================================

  # enterHead()
  # -----------------------------------------------------------------------------------------------
  def enterHead(self, ctx):
    if DEBUG:
      print('*** enterHead()', file=sys.stderr)
    self.scribe_section = ScribeSection.HEAD

  # enterBody()
  # # ---------------------------------------------------------------------------------------------
  def enterBody(self, ctx):
    if DEBUG:
      print('*** enterBody()', file=sys.stderr)

    self.scribe_section = ScribeSection.BODY

  # enterMinres
  # -----------------------------------------------------------------------------------------------
  def enterMinres(self, ctx):
    """ MINRES NUMBER (CREDIT | CLASS)
    """
    if DEBUG:
      print('*** enterMinres()', file=sys.stderr)
    number = get_number(ctx)
    which = class_or_credit(ctx, number)
    self.sections[self.scribe_section.value].append(
        Requirement('minres',
                    f'{number} {which}',
                    f'At least {number} {which.lower()} '
                    f'must be completed in residency.',
                    None))

  # enterMinCredit()
  # -----------------------------------------------------------------------------------------------
  def enterMincredit(self, ctx):
    """ mincredit   :MINCREDIT NUMBER course_list TAG? ;
    """
    if DEBUG:
      print('*** enterMincredit()', file=sys.stderr)
    num_credits = float(str(ctx.NUMBER()))
    course_list = build_course_list(self, ctx.course_list())
    print(course_list)

  # enterNumcredit()
  # -----------------------------------------------------------------------------------------------
  def enterNumcredit(self, ctx):
    """ (NUMBER | RANGE) CREDIT PSEUDO? INFROM? course_list? TAG? ;
    """
    if DEBUG:
      print('*** enterNumcredit()', file=sys.stderr)
    self.sections[self.scribe_section.value].append(numcredit(self.institution,
                                                              self.block_type_str,
                                                              ctx))

  # enterMaxcredit()
  # -----------------------------------------------------------------------------------------------
  def enterMaxcredit(self, ctx):
    """ MAXCREDIT NUMBER course_list TAG? ;

        UNRESOLVED: the WITH clause applies only to the last course in the course list unless it's a
        range, in which cass it applies to all. Not clear what a wildcard catalog number means yet.
    """
    if DEBUG:
      print(f'*** enterMaxcredit()', file=sys.stderr)
    limit = f'a maximum of {ctx.NUMBER()}'
    if ctx.NUMBER() == 0:
      limit = 'zero'
    text = f'This {self.block_type_str} allows {limit} credits'
    course_list = None
    # There can be two course lists, the main one, and an EXCEPT one
    course_lists = ctx.course_list()
    if len(course_lists) > 0:
      course_list = build_course_list(self.institution, course_lists[0])
    if len(course_lists) > 1:
      except_list = build_course_list(self.institution, course_lists[1])

    if course_list is None:  # Weird: no credits allowed, but no course list provided.
      raise ValueError(f'MaxCredit rule with no courses specified.')

    else:
      list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
      attributes, html_list = course_list2html(course_list['courses'])
      len_list = len(html_list)
      if len_list == 1:
        preamble = f' in '
        courses = html_list[0]
      else:
        preamble = f' in {list_quantifier} of these {len_list} courses:'
        courses = html_list
      # Need to report what attributes all the found courses share and need to process any WITH
      # and EXCEPT clauses. YOU ARE HERE******************************************************
      text += f' {preamble} '
    self.sections[self.scribe_section.value].append(
        Requirement('maxcredits',
                    f'{ctx.NUMBER()} credits',
                    f'{text}',
                    courses))

  # enterMaxclass()
  # -----------------------------------------------------------------------------------------------
  def enterMaxclass(self, ctx):
    """ MAXCLASS NUMBER course_list TAG? ;
    """
    if DEBUG:
      print('*** enterMaxclass()', file=sys.stderr)
    num_classes = int(str(ctx.NUMBER()))
    suffix = '' if num_classes == 1 else 'es'
    limit = f'no more than {num_classes} class{suffix}'
    if num_classes == 0:
      limit = 'no classes'
    text = f'This {self.block_type_str} allows {limit}'
    course_list = None
    # There can be two course lists, the main one, and an EXCEPT one
    course_lists = ctx.course_list()
    if len(course_lists) > 0:
      course_list = build_course_list(self.institution, course_lists[0])
    if len(course_lists) > 1:
      except_list = build_course_list(self.institution, course_lists[1])

    if course_list is None:  # Weird: no classes allowed, but no course list provided.
      raise ValueError('MaxClass with no list of courses.')
    # else:
    #   attributes, html_list = course_list2html(course_list['courses'])
    #   len_list = len(html_list)
    #   if len_list == 1:
    #     preamble = f' in '
    #     courses = html_list[0]
    #   else:
    #     if len_list == 2:
    #       list_quantifier = 'either' if course_list['list_type'] == 'or' else 'both'
    #     else:
    #       list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
    #     preamble = f' in {list_quantifier} of these {len_list} {" and ".join(attributes)} courses:'
    #     courses = html_list
    #   text += f' {preamble} '
    # self.sections[self.scribe_section.value].append(
    #     Requirement('maxlasses',
    #                 f'{num_classes} class{suffix}',
    #                 f'{text}',
    #                 courses))

  # enterMaxpassfail()
  # -----------------------------------------------------------------------------------------------
  def enterMaxpassfail(self, ctx):
    """ MAXPASSFAIL NUMBER (CREDIT | CLASS) (TAG '=' SYMBOL)?
    """
    if DEBUG:
      print('*** enterMaxpassfail()', file=sys.stderr)
    num = int(str(ctx.NUMBER()))
    limit = f'no more than {ctx.NUMBER()}'
    if num == 0:
      limit = 'no'
    which = class_or_credit(ctx)
    if num == 1:
      which = which[0:-1].strip('e')
    text = f'This {self.block_type_str} allows {limit} {which} to be taken Pass/Fail.'
    self.sections[self.scribe_section.value].append(
        Requirement('maxpassfail',
                    f'{num} {which}',
                    f'{text}',
                    None))

  def enterNumclass(self, ctx):
    """ (NUMBER | RANGE) CLASS INFROM? course_list? TAG? label* ;
    """
    if DEBUG:
      print('*** enterNumClass', file=sys.stderr)
    # Sometimes this is part of a rule subset (but not necessarily?)
    if hasattr(ctx, 'visited'):
      return
    else:
      return numclass(ctx)

  # enterGroup()
  # -----------------------------------------------------------------------------------------------
  def enterGroup(self, ctx):
    """ group       : NUMBER GROUP INFROM? group_list group_qualifier* label ;
        group_list  : group_item (OR group_item)* ;
        group_item  : LP
                    (course
                    | block
                    | block_type
                    | group
                    | rule_complete
                    | noncourse
                    ) RP label? ;
        group_qualifier : maxpassfail
                        | maxperdisc
                        | maxtransfer
                        | mingrade
                        | minperdisc
                        | samedisc
                        | share
                        | minclass
                        | mincredit
                        | ruletag ;
    """
    if DEBUG:
      print('*** enterGroup', file=sys.stderr)
    num_required = str(ctx.NUMBER())
    group_list = ctx.group_list()
    print('group_list.children:', group_list.children)
    label_ctx = ctx.label()
    label_str = label_ctx.STRING()
    label_ctx.visited = True
    if DEBUG:
      print('    ', label_str)
      print(f'    Require {num_required} of num_provided groups.')

  # enterRule_subset()
  # -----------------------------------------------------------------------------------------------
  def enterRule_subset(self, ctx):
    """ BEGINSUB (class_credit | group)+ ENDSUB qualifier* label ;
        class_credit    : (NUMBER | RANGE) (CLASS | CREDIT)
                          (ANDOR (NUMBER | RANGE) (CLASS | CREDIT))? PSEUDO?
                          INFROM? course_list? TAG? label? ;
        qualifier       : mingpa | mingrade ;
        mingpa          : MINGPA NUMBER ;
        mingrade        : MINGRADE NUMBER ;
    """
    if DEBUG:
      print('*** enterRule_subset', file=sys.stderr)
    for class_credit_ctx in ctx.class_credit():
      print(str(class_credit_ctx.NUMBER()[0]))

    classes_list = []

    label_ctx = ctx.label()
    label_str = label_ctx.STRING()
    print(label_str)
    label_ctx.visited = True

    # self.sections[self.scribe_section.value].append(
    #     Requirement('subset',
    #                 f'{len(classes_list)} classes or {len(credits_list)}',
    #                 label_str,
    #                 classes_list))

  def enterBlocktype(self, ctx):
    """ NUMBER BLOCKTYPE LP DEGREE|CONC|MAJOR|MINOR RP label
    """
    if DEBUG:
      print('*** enterBlocktype', file=sys.stderr)
      print(ctx.SHARE_LIST())
    pass

  # These two are in the superclass, but should be covered by enterRule_subset() above
  # def enterBeginsub(self, ctx):
  #   if DEBUG:
  #     print('*** enterBeginSub', file=sys.stderr)
  #   pass

  # def enterEndsub(self, ctx):
  #   if DEBUG:
  #     print('*** enterEndSub', file=sys.stderr)
  #   pass

  # enterRemark()
  # -----------------------------------------------------------------------------------------------
  def enterRemark(self, ctx):
    """ REMARK STRING remark* ;
    """
    if DEBUG:
      print('*** enterRemark()', file=sys.stderr)
      print(ctx.STRING(), file=sys.stderr)
    pass

  # enterLabel()
  # -----------------------------------------------------------------------------------------------
  def enterLabel(self, ctx):
    """ REMARK STRING ';' remark* ;
    """
    if DEBUG:
      print('*** enterLabel()', file=sys.stderr)
      try:
        if ctx.visited:
          return None
      except AttributeError:
        # All labels should be processed as part of a rule
        print(ctx.STRING(), file=sys.stderr)

  # enterShare()
  # -----------------------------------------------------------------------------------------------
  def enterShare(self, ctx):
    """ share           : (SHARE | DONT_SHARE) (NUMBER (CREDIT | CLASS))? SHARE_LIST ;
        SHARE_LIST      : LP SHARE_ITEM (COMMA SHARE_ITEM)* RP ;
        SHARE_ITEM      : DEGREE | CONC | MAJOR | MINOR | (OTHER (EQ SYMBOL)?) | THIS_BLOCK;
    """
    if DEBUG:
      print('*** enterShare()', file=sys.stderr)
    token = str(ctx.SHARE())
    if token.lower() in ['share', 'sharewith', 'nonexclusive']:
      share_type = 'share'
      neg = ''
    else:
      share_type = 'exclusive'
      neg = ' not'
    text = (f'Courses used to satisfy this requirement may{neg} also be used to satisfy'
            f' the following requirements:')

    # There are separate share and exclusive SHARE_ITEM lists for the head and body.
    this_section = self.sections[self.scribe_section.value]
    for i, item in enumerate(this_section):
      if item.keyword == share_type:
        break
    else:   # This really is for the for loop: add the appropriate type of share list to the section
      this_section.append(ShareList(share_type, text, []))
      i = len(this_section) - 1

    this_section[i].share_list.append(str(ctx.SHARE_LIST()).strip('()'))
