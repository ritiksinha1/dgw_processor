# Generated from ReqBlock.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .ReqBlockParser import ReqBlockParser
else:
    from ReqBlockParser import ReqBlockParser

# This class defines a complete listener for a parse tree produced by ReqBlockParser.
class ReqBlockListener(ParseTreeListener):

    # Enter a parse tree produced by ReqBlockParser#req_block.
    def enterReq_block(self, ctx:ReqBlockParser.Req_blockContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#req_block.
    def exitReq_block(self, ctx:ReqBlockParser.Req_blockContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#head.
    def enterHead(self, ctx:ReqBlockParser.HeadContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#head.
    def exitHead(self, ctx:ReqBlockParser.HeadContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#body.
    def enterBody(self, ctx:ReqBlockParser.BodyContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#body.
    def exitBody(self, ctx:ReqBlockParser.BodyContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#course_list.
    def enterCourse_list(self, ctx:ReqBlockParser.Course_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#course_list.
    def exitCourse_list(self, ctx:ReqBlockParser.Course_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#full_course.
    def enterFull_course(self, ctx:ReqBlockParser.Full_courseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#full_course.
    def exitFull_course(self, ctx:ReqBlockParser.Full_courseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#course_item.
    def enterCourse_item(self, ctx:ReqBlockParser.Course_itemContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#course_item.
    def exitCourse_item(self, ctx:ReqBlockParser.Course_itemContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#and_list.
    def enterAnd_list(self, ctx:ReqBlockParser.And_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#and_list.
    def exitAnd_list(self, ctx:ReqBlockParser.And_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#or_list.
    def enterOr_list(self, ctx:ReqBlockParser.Or_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#or_list.
    def exitOr_list(self, ctx:ReqBlockParser.Or_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#except_list.
    def enterExcept_list(self, ctx:ReqBlockParser.Except_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#except_list.
    def exitExcept_list(self, ctx:ReqBlockParser.Except_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#include_list.
    def enterInclude_list(self, ctx:ReqBlockParser.Include_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#include_list.
    def exitInclude_list(self, ctx:ReqBlockParser.Include_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#catalog_number.
    def enterCatalog_number(self, ctx:ReqBlockParser.Catalog_numberContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#catalog_number.
    def exitCatalog_number(self, ctx:ReqBlockParser.Catalog_numberContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#discipline.
    def enterDiscipline(self, ctx:ReqBlockParser.DisciplineContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#discipline.
    def exitDiscipline(self, ctx:ReqBlockParser.DisciplineContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#course_list_head_qualifier.
    def enterCourse_list_head_qualifier(self, ctx:ReqBlockParser.Course_list_head_qualifierContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#course_list_head_qualifier.
    def exitCourse_list_head_qualifier(self, ctx:ReqBlockParser.Course_list_head_qualifierContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#course_list_body.
    def enterCourse_list_body(self, ctx:ReqBlockParser.Course_list_bodyContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#course_list_body.
    def exitCourse_list_body(self, ctx:ReqBlockParser.Course_list_bodyContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#qualifier.
    def enterQualifier(self, ctx:ReqBlockParser.QualifierContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#qualifier.
    def exitQualifier(self, ctx:ReqBlockParser.QualifierContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#begin_if.
    def enterBegin_if(self, ctx:ReqBlockParser.Begin_ifContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#begin_if.
    def exitBegin_if(self, ctx:ReqBlockParser.Begin_ifContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#end_if.
    def enterEnd_if(self, ctx:ReqBlockParser.End_ifContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#end_if.
    def exitEnd_if(self, ctx:ReqBlockParser.End_ifContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#conditional_head.
    def enterConditional_head(self, ctx:ReqBlockParser.Conditional_headContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#conditional_head.
    def exitConditional_head(self, ctx:ReqBlockParser.Conditional_headContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#else_head.
    def enterElse_head(self, ctx:ReqBlockParser.Else_headContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#else_head.
    def exitElse_head(self, ctx:ReqBlockParser.Else_headContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#head_rule_group.
    def enterHead_rule_group(self, ctx:ReqBlockParser.Head_rule_groupContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#head_rule_group.
    def exitHead_rule_group(self, ctx:ReqBlockParser.Head_rule_groupContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#head_rule.
    def enterHead_rule(self, ctx:ReqBlockParser.Head_ruleContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#head_rule.
    def exitHead_rule(self, ctx:ReqBlockParser.Head_ruleContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#conditional_body.
    def enterConditional_body(self, ctx:ReqBlockParser.Conditional_bodyContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#conditional_body.
    def exitConditional_body(self, ctx:ReqBlockParser.Conditional_bodyContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#else_body.
    def enterElse_body(self, ctx:ReqBlockParser.Else_bodyContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#else_body.
    def exitElse_body(self, ctx:ReqBlockParser.Else_bodyContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#body_rule_group.
    def enterBody_rule_group(self, ctx:ReqBlockParser.Body_rule_groupContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#body_rule_group.
    def exitBody_rule_group(self, ctx:ReqBlockParser.Body_rule_groupContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#body_rule.
    def enterBody_rule(self, ctx:ReqBlockParser.Body_ruleContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#body_rule.
    def exitBody_rule(self, ctx:ReqBlockParser.Body_ruleContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#group.
    def enterGroup(self, ctx:ReqBlockParser.GroupContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#group.
    def exitGroup(self, ctx:ReqBlockParser.GroupContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#group_list.
    def enterGroup_list(self, ctx:ReqBlockParser.Group_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#group_list.
    def exitGroup_list(self, ctx:ReqBlockParser.Group_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#group_item.
    def enterGroup_item(self, ctx:ReqBlockParser.Group_itemContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#group_item.
    def exitGroup_item(self, ctx:ReqBlockParser.Group_itemContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#subset.
    def enterSubset(self, ctx:ReqBlockParser.SubsetContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#subset.
    def exitSubset(self, ctx:ReqBlockParser.SubsetContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#block.
    def enterBlock(self, ctx:ReqBlockParser.BlockContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#block.
    def exitBlock(self, ctx:ReqBlockParser.BlockContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#blocktype.
    def enterBlocktype(self, ctx:ReqBlockParser.BlocktypeContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#blocktype.
    def exitBlocktype(self, ctx:ReqBlockParser.BlocktypeContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#allow_clause.
    def enterAllow_clause(self, ctx:ReqBlockParser.Allow_clauseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#allow_clause.
    def exitAllow_clause(self, ctx:ReqBlockParser.Allow_clauseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#class_credit_head.
    def enterClass_credit_head(self, ctx:ReqBlockParser.Class_credit_headContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#class_credit_head.
    def exitClass_credit_head(self, ctx:ReqBlockParser.Class_credit_headContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#class_credit_body.
    def enterClass_credit_body(self, ctx:ReqBlockParser.Class_credit_bodyContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#class_credit_body.
    def exitClass_credit_body(self, ctx:ReqBlockParser.Class_credit_bodyContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#allow.
    def enterAllow(self, ctx:ReqBlockParser.AllowContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#allow.
    def exitAllow(self, ctx:ReqBlockParser.AllowContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#area_end.
    def enterArea_end(self, ctx:ReqBlockParser.Area_endContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#area_end.
    def exitArea_end(self, ctx:ReqBlockParser.Area_endContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#area_start.
    def enterArea_start(self, ctx:ReqBlockParser.Area_startContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#area_start.
    def exitArea_start(self, ctx:ReqBlockParser.Area_startContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#class_or_credit.
    def enterClass_or_credit(self, ctx:ReqBlockParser.Class_or_creditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#class_or_credit.
    def exitClass_or_credit(self, ctx:ReqBlockParser.Class_or_creditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#copy_rules.
    def enterCopy_rules(self, ctx:ReqBlockParser.Copy_rulesContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#copy_rules.
    def exitCopy_rules(self, ctx:ReqBlockParser.Copy_rulesContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#display.
    def enterDisplay(self, ctx:ReqBlockParser.DisplayContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#display.
    def exitDisplay(self, ctx:ReqBlockParser.DisplayContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_tag.
    def enterHeader_tag(self, ctx:ReqBlockParser.Header_tagContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_tag.
    def exitHeader_tag(self, ctx:ReqBlockParser.Header_tagContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#label.
    def enterLabel(self, ctx:ReqBlockParser.LabelContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#label.
    def exitLabel(self, ctx:ReqBlockParser.LabelContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#lastres.
    def enterLastres(self, ctx:ReqBlockParser.LastresContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#lastres.
    def exitLastres(self, ctx:ReqBlockParser.LastresContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxclass.
    def enterMaxclass(self, ctx:ReqBlockParser.MaxclassContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxclass.
    def exitMaxclass(self, ctx:ReqBlockParser.MaxclassContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxcredit.
    def enterMaxcredit(self, ctx:ReqBlockParser.MaxcreditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxcredit.
    def exitMaxcredit(self, ctx:ReqBlockParser.MaxcreditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxpassfail.
    def enterMaxpassfail(self, ctx:ReqBlockParser.MaxpassfailContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxpassfail.
    def exitMaxpassfail(self, ctx:ReqBlockParser.MaxpassfailContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxperdisc.
    def enterMaxperdisc(self, ctx:ReqBlockParser.MaxperdiscContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxperdisc.
    def exitMaxperdisc(self, ctx:ReqBlockParser.MaxperdiscContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxspread.
    def enterMaxspread(self, ctx:ReqBlockParser.MaxspreadContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxspread.
    def exitMaxspread(self, ctx:ReqBlockParser.MaxspreadContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxterm.
    def enterMaxterm(self, ctx:ReqBlockParser.MaxtermContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxterm.
    def exitMaxterm(self, ctx:ReqBlockParser.MaxtermContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#maxtransfer.
    def enterMaxtransfer(self, ctx:ReqBlockParser.MaxtransferContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#maxtransfer.
    def exitMaxtransfer(self, ctx:ReqBlockParser.MaxtransferContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#minarea.
    def enterMinarea(self, ctx:ReqBlockParser.MinareaContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#minarea.
    def exitMinarea(self, ctx:ReqBlockParser.MinareaContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#minclass.
    def enterMinclass(self, ctx:ReqBlockParser.MinclassContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#minclass.
    def exitMinclass(self, ctx:ReqBlockParser.MinclassContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#mincredit.
    def enterMincredit(self, ctx:ReqBlockParser.MincreditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#mincredit.
    def exitMincredit(self, ctx:ReqBlockParser.MincreditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#mingpa.
    def enterMingpa(self, ctx:ReqBlockParser.MingpaContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#mingpa.
    def exitMingpa(self, ctx:ReqBlockParser.MingpaContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#mingrade.
    def enterMingrade(self, ctx:ReqBlockParser.MingradeContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#mingrade.
    def exitMingrade(self, ctx:ReqBlockParser.MingradeContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#minperdisc.
    def enterMinperdisc(self, ctx:ReqBlockParser.MinperdiscContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#minperdisc.
    def exitMinperdisc(self, ctx:ReqBlockParser.MinperdiscContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#minres.
    def enterMinres(self, ctx:ReqBlockParser.MinresContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#minres.
    def exitMinres(self, ctx:ReqBlockParser.MinresContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#minspread.
    def enterMinspread(self, ctx:ReqBlockParser.MinspreadContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#minspread.
    def exitMinspread(self, ctx:ReqBlockParser.MinspreadContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#minterm.
    def enterMinterm(self, ctx:ReqBlockParser.MintermContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#minterm.
    def exitMinterm(self, ctx:ReqBlockParser.MintermContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#noncourse.
    def enterNoncourse(self, ctx:ReqBlockParser.NoncourseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#noncourse.
    def exitNoncourse(self, ctx:ReqBlockParser.NoncourseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#num_classes.
    def enterNum_classes(self, ctx:ReqBlockParser.Num_classesContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#num_classes.
    def exitNum_classes(self, ctx:ReqBlockParser.Num_classesContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#num_credits.
    def enterNum_credits(self, ctx:ReqBlockParser.Num_creditsContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#num_credits.
    def exitNum_credits(self, ctx:ReqBlockParser.Num_creditsContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#nv_pair.
    def enterNv_pair(self, ctx:ReqBlockParser.Nv_pairContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#nv_pair.
    def exitNv_pair(self, ctx:ReqBlockParser.Nv_pairContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#optional.
    def enterOptional(self, ctx:ReqBlockParser.OptionalContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#optional.
    def exitOptional(self, ctx:ReqBlockParser.OptionalContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#proxy_advice.
    def enterProxy_advice(self, ctx:ReqBlockParser.Proxy_adviceContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#proxy_advice.
    def exitProxy_advice(self, ctx:ReqBlockParser.Proxy_adviceContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#pseudo.
    def enterPseudo(self, ctx:ReqBlockParser.PseudoContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#pseudo.
    def exitPseudo(self, ctx:ReqBlockParser.PseudoContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#remark.
    def enterRemark(self, ctx:ReqBlockParser.RemarkContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#remark.
    def exitRemark(self, ctx:ReqBlockParser.RemarkContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#rule_complete.
    def enterRule_complete(self, ctx:ReqBlockParser.Rule_completeContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#rule_complete.
    def exitRule_complete(self, ctx:ReqBlockParser.Rule_completeContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#rule_tag.
    def enterRule_tag(self, ctx:ReqBlockParser.Rule_tagContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#rule_tag.
    def exitRule_tag(self, ctx:ReqBlockParser.Rule_tagContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#samedisc.
    def enterSamedisc(self, ctx:ReqBlockParser.SamediscContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#samedisc.
    def exitSamedisc(self, ctx:ReqBlockParser.SamediscContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#share.
    def enterShare(self, ctx:ReqBlockParser.ShareContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#share.
    def exitShare(self, ctx:ReqBlockParser.ShareContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#standalone.
    def enterStandalone(self, ctx:ReqBlockParser.StandaloneContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#standalone.
    def exitStandalone(self, ctx:ReqBlockParser.StandaloneContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#string.
    def enterString(self, ctx:ReqBlockParser.StringContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#string.
    def exitString(self, ctx:ReqBlockParser.StringContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#symbol.
    def enterSymbol(self, ctx:ReqBlockParser.SymbolContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#symbol.
    def exitSymbol(self, ctx:ReqBlockParser.SymbolContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#tag.
    def enterTag(self, ctx:ReqBlockParser.TagContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#tag.
    def exitTag(self, ctx:ReqBlockParser.TagContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#under.
    def enterUnder(self, ctx:ReqBlockParser.UnderContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#under.
    def exitUnder(self, ctx:ReqBlockParser.UnderContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#with_clause.
    def enterWith_clause(self, ctx:ReqBlockParser.With_clauseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#with_clause.
    def exitWith_clause(self, ctx:ReqBlockParser.With_clauseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#expression.
    def enterExpression(self, ctx:ReqBlockParser.ExpressionContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#expression.
    def exitExpression(self, ctx:ReqBlockParser.ExpressionContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#logical_op.
    def enterLogical_op(self, ctx:ReqBlockParser.Logical_opContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#logical_op.
    def exitLogical_op(self, ctx:ReqBlockParser.Logical_opContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#relational_op.
    def enterRelational_op(self, ctx:ReqBlockParser.Relational_opContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#relational_op.
    def exitRelational_op(self, ctx:ReqBlockParser.Relational_opContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#list_or.
    def enterList_or(self, ctx:ReqBlockParser.List_orContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#list_or.
    def exitList_or(self, ctx:ReqBlockParser.List_orContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#list_and.
    def enterList_and(self, ctx:ReqBlockParser.List_andContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#list_and.
    def exitList_and(self, ctx:ReqBlockParser.List_andContext):
        pass



del ReqBlockParser