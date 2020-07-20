#! /usr/local/bin/python3
""" This is the module that converts a parsed requirement block into a serializable data structure.
"""
import os
import sys

from enum import IntEnum

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener

# from closeable_objects import dict2html, items2html

from dgw_utils import build_course_list,\
    catalog_years,\
    class_or_credit,\
    colleges,\
    context_path,\
    expression_terminals,\
    get_number

LOG_DGW_CONTEXT_PATH = os.getenv('LOG_DGW_CONTEXT_PATH')
DEBUG = os.getenv('DEBUG_PROCESSOR')

# class ScribeSection(IntEnum)
# -------------------------------------------------------------------------------------------------
class ScribeSection(IntEnum):
  """ Keep track of which section of a Scribe Block is being processed.
  """
  NONE = 0
  HEAD = 1
  BODY = 2


# Class DGW_Processor(ReqBlockListener)
# =================================================================================================
# The ReqBlockListener module is generated by Antlr4 from the grammar in ReqBlock.g4. This class
# provides the method overrides for the stubs provided in ReqBlockListener.
class DGW_Processor(ReqBlockListener):
  def __init__(self,
               institution,
               requirement_id,
               block_type,
               block_value,
               title,
               period_start,
               period_stop,
               requirement_text):
    """ Constructor, given metadata and text for a requirement block.
    """

    if LOG_DGW_CONTEXT_PATH:
      print(f'*** DGW_Processor: {institution} {requirement_id} {block_type} “{title}”',
            file=sys.stderr)
    self.institution = institution
    self.requirement_id = requirement_id
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

  # @property
  def html(self, with_line_nums=False):
    lines_pre = ''
    if with_line_nums:
      # Add line numbers to requirements text for development purposes.
      num_lines = self.requirement_text.count('\n')
      lines_pre = '<pre class="line-numbers">'
      for line in range(num_lines):
        lines_pre += f'{line + 1:03d}  \n'
      lines_pre += '</pre>'

    html_scribe_block = f"""
<h1>{self.institution_name} {self.requirement_id}: <em>{self.title}</em></h1>
<p>Requirements for {self.catalog_years.catalog_type} Catalog Years
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
"""

    return html_scribe_block

  # ==============================================================================================#
  # ReqBlockListener Overrides                                                                    #
  # ==============================================================================================#

  # enterReq_block(self, ctx: ReqBlockParser.Req_blockContext)
  # -----------------------------------------------------------------------------------------------
  def enterReq_block(self, ctx: ReqBlockParser.Req_blockContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterHead(self, ctx: ReqBlockParser.HeadContext)
  # -----------------------------------------------------------------------------------------------
  def enterHead(self, ctx: ReqBlockParser.HeadContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)
    self.scribe_section = ScribeSection.HEAD

  # enterBody(self, ctx: ReqBlockParser.BodyContext)
  # -----------------------------------------------------------------------------------------------
  def enterBody(self, ctx: ReqBlockParser.BodyContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)
    self.scribe_section = ScribeSection.BODY

  # enterCourse_list(self, ctx: ReqBlockParser.Course_listContext)
  # -----------------------------------------------------------------------------------------------
  def enterCourse_list(self, ctx: ReqBlockParser.Course_listContext):
    """ course_list     : course_item (and_list | or_list)? course_qualifier* label?;
        course_item     : discipline? catalog_number course_qualifier*;
        and_list        : (list_and course_item )+;
        or_list         : (list_or course_item)+;
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)
    course_list = build_course_list(self.institution, ctx)
    self.sections[self.scribe_section].append(course_list)
    if DEBUG:
      print(f'\n               Context: {course_list["context_path"]}')
      print(f'   Num Scribed Courses: {len(course_list["scribed_courses"]):>4}')
      if len(course_list["scribed_courses"]) > 1:
        print(f'             List Type: {course_list["list_type"]:>4}')
      print(f'    Num Active Courses: {len(course_list["active_courses"]):>4}')
      if len(course_list["list_qualifiers"]) > 0:
        print(f'       List Qualifiers: {", ".join(course_list["list_qualifiers"])}')
      print(f'                 Label: {course_list["label"]}')
      if len(course_list["attributes"]) > 0:
        print(f'  Attributes in Common: {", ".join(course_list["attributes"])}')

  # enterFull_course(self, ctx: ReqBlockParser.Full_courseContext)
  # -----------------------------------------------------------------------------------------------
  def enterFull_course(self, ctx: ReqBlockParser.Full_courseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterCourse_item(self, ctx: ReqBlockParser.Course_itemContext)
  # -----------------------------------------------------------------------------------------------
  def enterCourse_item(self, ctx: ReqBlockParser.Course_itemContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterAnd_list(self, ctx: ReqBlockParser.And_listContext)
  # -----------------------------------------------------------------------------------------------
  def enterAnd_list(self, ctx: ReqBlockParser.And_listContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterOr_list(self, ctx: ReqBlockParser.Or_listContext)
  # -----------------------------------------------------------------------------------------------
  def enterOr_list(self, ctx: ReqBlockParser.Or_listContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterDiscipline(self, ctx: ReqBlockParser.DisciplineContext)
  # -----------------------------------------------------------------------------------------------
  def enterDiscipline(self, ctx: ReqBlockParser.DisciplineContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterCatalog_number(self, ctx: ReqBlockParser.Catalog_numberContext)
  # -----------------------------------------------------------------------------------------------
  def enterCatalog_number(self, ctx: ReqBlockParser.Catalog_numberContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterCourse_qualifier(self, ctx: ReqBlockParser.Course_list_qualifierContext)
  # -----------------------------------------------------------------------------------------------
  def enterCourse_qualifier(self, ctx: ReqBlockParser.Course_list_qualifierContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterIf_then(self, ctx: ReqBlockParser.If_thenContext)
  # -----------------------------------------------------------------------------------------------
  def enterIf_then(self, ctx: ReqBlockParser.If_thenContext):
    """ IF expression THEN (stmt | stmt_group) group_qualifier* label? else_clause?;
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)
    # Capture the conditional expression's terminals
    expr = ctx.expression()
    print(expr.getText())
    terminals = []
    expression_terminals(expr, terminals)
    print(terminals)

  # enterElse_clause(self, ctx: ReqBlockParser.Else_clauseContext)
  # -----------------------------------------------------------------------------------------------
  def enterElse_clause(self, ctx: ReqBlockParser.Else_clauseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterStmt_group(self, ctx: ReqBlockParser.Stmt_groupContext)
  # -----------------------------------------------------------------------------------------------
  def enterStmt_group(self, ctx: ReqBlockParser.Stmt_groupContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterStmt(self, ctx: ReqBlockParser.StmtContext)
  # -----------------------------------------------------------------------------------------------
  def enterStmt(self, ctx: ReqBlockParser.StmtContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterBegin_if(self, ctx: ReqBlockParser.Begin_ifContext)
  # -----------------------------------------------------------------------------------------------
  def enterBegin_if(self, ctx: ReqBlockParser.Begin_ifContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterEnd_if(self, ctx: ReqBlockParser.End_ifContext)
  # -----------------------------------------------------------------------------------------------
  def enterEnd_if(self, ctx: ReqBlockParser.End_ifContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterGroup(self, ctx: ReqBlockParser.GroupContext)
  # -----------------------------------------------------------------------------------------------
  def enterGroup(self, ctx: ReqBlockParser.GroupContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterGroup_list(self, ctx: ReqBlockParser.Group_listContext)
  # -----------------------------------------------------------------------------------------------
  def enterGroup_list(self, ctx: ReqBlockParser.Group_listContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterGroup_item(self, ctx: ReqBlockParser.Group_itemContext)
  # -----------------------------------------------------------------------------------------------
  def enterGroup_item(self, ctx: ReqBlockParser.Group_itemContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterGroup_qualifier(self, ctx: ReqBlockParser.Group_qualifierContext)
  # -----------------------------------------------------------------------------------------------
  def enterGroup_qualifier(self, ctx: ReqBlockParser.Group_qualifierContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterSubset(self, ctx: ReqBlockParser.SubsetContext)
  # -----------------------------------------------------------------------------------------------
  def enterSubset(self, ctx: ReqBlockParser.SubsetContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterSubset_qualifier(self, ctx: ReqBlockParser.Subset_qualifierContext)
  # -----------------------------------------------------------------------------------------------
  def enterSubset_qualifier(self, ctx: ReqBlockParser.Subset_qualifierContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterBlock(self, ctx: ReqBlockParser.BlockContext)
  # -----------------------------------------------------------------------------------------------
  def enterBlock(self, ctx: ReqBlockParser.BlockContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterBlocktype(self, ctx: ReqBlockParser.BlocktypeContext)
  # -----------------------------------------------------------------------------------------------
  def enterBlocktype(self, ctx: ReqBlockParser.BlocktypeContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterAllow_clause(self, ctx: ReqBlockParser.Allow_clauseContext)
  # -----------------------------------------------------------------------------------------------
  def enterAllow_clause(self, ctx: ReqBlockParser.Allow_clauseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterArea_list(self, ctx: ReqBlockParser.Area_listContext)
  # -----------------------------------------------------------------------------------------------
  def enterArea_list(self, ctx: ReqBlockParser.Area_listContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterArea_element(self, ctx: ReqBlockParser.Area_elementContext)
  # -----------------------------------------------------------------------------------------------
  def enterArea_element(self, ctx: ReqBlockParser.Area_elementContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterClass_credit(self, ctx: ReqBlockParser.Class_creditContext)
  # -----------------------------------------------------------------------------------------------
  def enterClass_credit(self, ctx: ReqBlockParser.Class_creditContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterCopy_rules(self, ctx: ReqBlockParser.Copy_rulesContext)
  # -----------------------------------------------------------------------------------------------
  def enterCopy_rules(self, ctx: ReqBlockParser.Copy_rulesContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterExcept_clause(self, ctx: ReqBlockParser.Except_clauseContext)
  # -----------------------------------------------------------------------------------------------
  def enterExcept_clause(self, ctx: ReqBlockParser.Except_clauseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterIncluding_clause(self, ctx: ReqBlockParser.Including_clauseContext)
  # -----------------------------------------------------------------------------------------------
  def enterIncluding_clause(self, ctx: ReqBlockParser.Including_clauseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterLabel(self, ctx: ReqBlockParser.LabelContext)
  # -----------------------------------------------------------------------------------------------
  def enterLabel(self, ctx: ReqBlockParser.LabelContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterLabel_tag(self, ctx: ReqBlockParser.Label_tagContext)
  # -----------------------------------------------------------------------------------------------
  def enterLabel_tag(self, ctx: ReqBlockParser.Label_tagContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterLastres(self, ctx: ReqBlockParser.LastresContext)
  # -----------------------------------------------------------------------------------------------
  def enterLastres(self, ctx: ReqBlockParser.LastresContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxclass(self, ctx: ReqBlockParser.MaxclassContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxclass(self, ctx: ReqBlockParser.MaxclassContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxcredit(self, ctx: ReqBlockParser.MaxcreditContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxcredit(self, ctx: ReqBlockParser.MaxcreditContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxpassfail(self, ctx: ReqBlockParser.MaxpassfailContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxpassfail(self, ctx: ReqBlockParser.MaxpassfailContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxperdisc(self, ctx: ReqBlockParser.MaxperdiscContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxperdisc(self, ctx: ReqBlockParser.MaxperdiscContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxspread(self, ctx: ReqBlockParser.MaxspreadContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxspread(self, ctx: ReqBlockParser.MaxspreadContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxterm(self, ctx: ReqBlockParser.MaxtermContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxterm(self, ctx: ReqBlockParser.MaxtermContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMaxtransfer(self, ctx: ReqBlockParser.MaxtransferContext)
  # -----------------------------------------------------------------------------------------------
  def enterMaxtransfer(self, ctx: ReqBlockParser.MaxtransferContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMinarea(self, ctx: ReqBlockParser.MinareaContext)
  # -----------------------------------------------------------------------------------------------
  def enterMinarea(self, ctx: ReqBlockParser.MinareaContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMinclass(self, ctx: ReqBlockParser.MinclassContext)
  # -----------------------------------------------------------------------------------------------
  def enterMinclass(self, ctx: ReqBlockParser.MinclassContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMincredit(self, ctx: ReqBlockParser.MincreditContext)
  # -----------------------------------------------------------------------------------------------
  def enterMincredit(self, ctx: ReqBlockParser.MincreditContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMingpa(self, ctx: ReqBlockParser.MingpaContext)
  # -----------------------------------------------------------------------------------------------
  def enterMingpa(self, ctx: ReqBlockParser.MingpaContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMingrade(self, ctx: ReqBlockParser.MingradeContext)
  # -----------------------------------------------------------------------------------------------
  def enterMingrade(self, ctx: ReqBlockParser.MingradeContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMinperdisc(self, ctx: ReqBlockParser.MinperdiscContext)
  # -----------------------------------------------------------------------------------------------
  def enterMinperdisc(self, ctx: ReqBlockParser.MinperdiscContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMinres(self, ctx: ReqBlockParser.MinresContext)
  # -----------------------------------------------------------------------------------------------
  def enterMinres(self, ctx: ReqBlockParser.MinresContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterMinspread(self, ctx: ReqBlockParser.MinspreadContext)
  # -----------------------------------------------------------------------------------------------
  def enterMinspread(self, ctx: ReqBlockParser.MinspreadContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterNoncourse(self, ctx: ReqBlockParser.NoncourseContext)
  # -----------------------------------------------------------------------------------------------
  def enterNoncourse(self, ctx: ReqBlockParser.NoncourseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterOptional(self, ctx: ReqBlockParser.OptionalContext)
  # -----------------------------------------------------------------------------------------------
  def enterOptional(self, ctx: ReqBlockParser.OptionalContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterRemark(self, ctx: ReqBlockParser.RemarkContext)
  # -----------------------------------------------------------------------------------------------
  def enterRemark(self, ctx: ReqBlockParser.RemarkContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterRule_complete(self, ctx: ReqBlockParser.Rule_completeContext)
  # -----------------------------------------------------------------------------------------------
  def enterRule_complete(self, ctx: ReqBlockParser.Rule_completeContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterRuletag(self, ctx: ReqBlockParser.RuletagContext)
  # -----------------------------------------------------------------------------------------------
  def enterRuletag(self, ctx: ReqBlockParser.RuletagContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterSamedisc(self, ctx: ReqBlockParser.SamediscContext)
  # -----------------------------------------------------------------------------------------------
  def enterSamedisc(self, ctx: ReqBlockParser.SamediscContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterShare(self, ctx: ReqBlockParser.ShareContext)
  # -----------------------------------------------------------------------------------------------
  def enterShare(self, ctx: ReqBlockParser.ShareContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterStandalone(self, ctx: ReqBlockParser.StandaloneContext)
  # -----------------------------------------------------------------------------------------------
  def enterStandalone(self, ctx: ReqBlockParser.StandaloneContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterTag(self, ctx: ReqBlockParser.TagContext)
  # -----------------------------------------------------------------------------------------------
  def enterTag(self, ctx: ReqBlockParser.TagContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterUnder(self, ctx: ReqBlockParser.UnderContext)
  # -----------------------------------------------------------------------------------------------
  def enterUnder(self, ctx: ReqBlockParser.UnderContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterWith_clause(self, ctx: ReqBlockParser.With_clauseContext)
  # -----------------------------------------------------------------------------------------------
  def enterWith_clause(self, ctx: ReqBlockParser.With_clauseContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterExpression(self, ctx: ReqBlockParser.ExpressionContext)
  # -----------------------------------------------------------------------------------------------
  def enterExpression(self, ctx: ReqBlockParser.ExpressionContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterLogical_op(self, ctx: ReqBlockParser.Logical_opContext)
  # -----------------------------------------------------------------------------------------------
  def enterLogical_op(self, ctx: ReqBlockParser.Logical_opContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterRelational_op(self, ctx: ReqBlockParser.Relational_opContext)
  # -----------------------------------------------------------------------------------------------
  def enterRelational_op(self, ctx: ReqBlockParser.Relational_opContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterList_or(self, ctx: ReqBlockParser.List_orContext)
  # -----------------------------------------------------------------------------------------------
  def enterList_or(self, ctx: ReqBlockParser.List_orContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)

  # enterList_and(self, ctx: ReqBlockParser.List_andContext)
  # -----------------------------------------------------------------------------------------------
  def enterList_and(self, ctx: ReqBlockParser.List_andContext):
    """
    """
    if LOG_DGW_CONTEXT_PATH:
      print(context_path(ctx), file=sys.stderr)
