# Generated from ReqBlock.g4 by ANTLR 4.12.0
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .ReqBlockParser import ReqBlockParser
else:
    from ReqBlockParser import ReqBlockParser

# This class defines a complete generic visitor for a parse tree produced by ReqBlockParser.

class ReqBlockVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ReqBlockParser#req_block.
    def visitReq_block(self, ctx:ReqBlockParser.Req_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header.
    def visitHeader(self, ctx:ReqBlockParser.HeaderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body.
    def visitBody(self, ctx:ReqBlockParser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list.
    def visitCourse_list(self, ctx:ReqBlockParser.Course_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#full_course.
    def visitFull_course(self, ctx:ReqBlockParser.Full_courseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_item.
    def visitCourse_item(self, ctx:ReqBlockParser.Course_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#and_list.
    def visitAnd_list(self, ctx:ReqBlockParser.And_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#or_list.
    def visitOr_list(self, ctx:ReqBlockParser.Or_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#except_list.
    def visitExcept_list(self, ctx:ReqBlockParser.Except_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#include_list.
    def visitInclude_list(self, ctx:ReqBlockParser.Include_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#catalog_number.
    def visitCatalog_number(self, ctx:ReqBlockParser.Catalog_numberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#discipline.
    def visitDiscipline(self, ctx:ReqBlockParser.DisciplineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list_body.
    def visitCourse_list_body(self, ctx:ReqBlockParser.Course_list_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list_rule.
    def visitCourse_list_rule(self, ctx:ReqBlockParser.Course_list_ruleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#qualifier.
    def visitQualifier(self, ctx:ReqBlockParser.QualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#begin_if.
    def visitBegin_if(self, ctx:ReqBlockParser.Begin_ifContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#end_if.
    def visitEnd_if(self, ctx:ReqBlockParser.End_ifContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_conditional.
    def visitHeader_conditional(self, ctx:ReqBlockParser.Header_conditionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_else.
    def visitHeader_else(self, ctx:ReqBlockParser.Header_elseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_rule_group.
    def visitHeader_rule_group(self, ctx:ReqBlockParser.Header_rule_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_rule.
    def visitHeader_rule(self, ctx:ReqBlockParser.Header_ruleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body_conditional.
    def visitBody_conditional(self, ctx:ReqBlockParser.Body_conditionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body_else.
    def visitBody_else(self, ctx:ReqBlockParser.Body_elseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body_rule_group.
    def visitBody_rule_group(self, ctx:ReqBlockParser.Body_rule_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body_rule.
    def visitBody_rule(self, ctx:ReqBlockParser.Body_ruleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group_requirement.
    def visitGroup_requirement(self, ctx:ReqBlockParser.Group_requirementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group_list.
    def visitGroup_list(self, ctx:ReqBlockParser.Group_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group.
    def visitGroup(self, ctx:ReqBlockParser.GroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#subset.
    def visitSubset(self, ctx:ReqBlockParser.SubsetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#block.
    def visitBlock(self, ctx:ReqBlockParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#blocktype.
    def visitBlocktype(self, ctx:ReqBlockParser.BlocktypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#noncourse.
    def visitNoncourse(self, ctx:ReqBlockParser.NoncourseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#rule_complete.
    def visitRule_complete(self, ctx:ReqBlockParser.Rule_completeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#under.
    def visitUnder(self, ctx:ReqBlockParser.UnderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#allow_clause.
    def visitAllow_clause(self, ctx:ReqBlockParser.Allow_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_class_credit.
    def visitHeader_class_credit(self, ctx:ReqBlockParser.Header_class_creditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body_class_credit.
    def visitBody_class_credit(self, ctx:ReqBlockParser.Body_class_creditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_maxclass.
    def visitHeader_maxclass(self, ctx:ReqBlockParser.Header_maxclassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_maxcredit.
    def visitHeader_maxcredit(self, ctx:ReqBlockParser.Header_maxcreditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_maxpassfail.
    def visitHeader_maxpassfail(self, ctx:ReqBlockParser.Header_maxpassfailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_maxperdisc.
    def visitHeader_maxperdisc(self, ctx:ReqBlockParser.Header_maxperdiscContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_maxterm.
    def visitHeader_maxterm(self, ctx:ReqBlockParser.Header_maxtermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_maxtransfer.
    def visitHeader_maxtransfer(self, ctx:ReqBlockParser.Header_maxtransferContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_minclass.
    def visitHeader_minclass(self, ctx:ReqBlockParser.Header_minclassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_mincredit.
    def visitHeader_mincredit(self, ctx:ReqBlockParser.Header_mincreditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_mingpa.
    def visitHeader_mingpa(self, ctx:ReqBlockParser.Header_mingpaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_mingrade.
    def visitHeader_mingrade(self, ctx:ReqBlockParser.Header_mingradeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_minperdisc.
    def visitHeader_minperdisc(self, ctx:ReqBlockParser.Header_minperdiscContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_minres.
    def visitHeader_minres(self, ctx:ReqBlockParser.Header_minresContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_minterm.
    def visitHeader_minterm(self, ctx:ReqBlockParser.Header_mintermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_share.
    def visitHeader_share(self, ctx:ReqBlockParser.Header_shareContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#allow.
    def visitAllow(self, ctx:ReqBlockParser.AllowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#area_end.
    def visitArea_end(self, ctx:ReqBlockParser.Area_endContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#area_start.
    def visitArea_start(self, ctx:ReqBlockParser.Area_startContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#class_or_credit.
    def visitClass_or_credit(self, ctx:ReqBlockParser.Class_or_creditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#copy_header.
    def visitCopy_header(self, ctx:ReqBlockParser.Copy_headerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#copy_rules.
    def visitCopy_rules(self, ctx:ReqBlockParser.Copy_rulesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#advice.
    def visitAdvice(self, ctx:ReqBlockParser.AdviceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#display.
    def visitDisplay(self, ctx:ReqBlockParser.DisplayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#proxy_advice.
    def visitProxy_advice(self, ctx:ReqBlockParser.Proxy_adviceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_tag.
    def visitHeader_tag(self, ctx:ReqBlockParser.Header_tagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#header_label.
    def visitHeader_label(self, ctx:ReqBlockParser.Header_labelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#hide_rule.
    def visitHide_rule(self, ctx:ReqBlockParser.Hide_ruleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#label.
    def visitLabel(self, ctx:ReqBlockParser.LabelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#lastres.
    def visitLastres(self, ctx:ReqBlockParser.LastresContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxclass.
    def visitMaxclass(self, ctx:ReqBlockParser.MaxclassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxcredit.
    def visitMaxcredit(self, ctx:ReqBlockParser.MaxcreditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxpassfail.
    def visitMaxpassfail(self, ctx:ReqBlockParser.MaxpassfailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxperdisc.
    def visitMaxperdisc(self, ctx:ReqBlockParser.MaxperdiscContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxspread.
    def visitMaxspread(self, ctx:ReqBlockParser.MaxspreadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxterm.
    def visitMaxterm(self, ctx:ReqBlockParser.MaxtermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxtransfer.
    def visitMaxtransfer(self, ctx:ReqBlockParser.MaxtransferContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minarea.
    def visitMinarea(self, ctx:ReqBlockParser.MinareaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minclass.
    def visitMinclass(self, ctx:ReqBlockParser.MinclassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#mincredit.
    def visitMincredit(self, ctx:ReqBlockParser.MincreditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#mingpa.
    def visitMingpa(self, ctx:ReqBlockParser.MingpaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#mingrade.
    def visitMingrade(self, ctx:ReqBlockParser.MingradeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minperdisc.
    def visitMinperdisc(self, ctx:ReqBlockParser.MinperdiscContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minres.
    def visitMinres(self, ctx:ReqBlockParser.MinresContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minspread.
    def visitMinspread(self, ctx:ReqBlockParser.MinspreadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minterm.
    def visitMinterm(self, ctx:ReqBlockParser.MintermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#num_classes.
    def visitNum_classes(self, ctx:ReqBlockParser.Num_classesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#num_credits.
    def visitNum_credits(self, ctx:ReqBlockParser.Num_creditsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#nv_pair.
    def visitNv_pair(self, ctx:ReqBlockParser.Nv_pairContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#nv_lhs.
    def visitNv_lhs(self, ctx:ReqBlockParser.Nv_lhsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#nv_rhs.
    def visitNv_rhs(self, ctx:ReqBlockParser.Nv_rhsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#optional.
    def visitOptional(self, ctx:ReqBlockParser.OptionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#pseudo.
    def visitPseudo(self, ctx:ReqBlockParser.PseudoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#remark.
    def visitRemark(self, ctx:ReqBlockParser.RemarkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#rule_tag.
    def visitRule_tag(self, ctx:ReqBlockParser.Rule_tagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#samedisc.
    def visitSamedisc(self, ctx:ReqBlockParser.SamediscContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#share.
    def visitShare(self, ctx:ReqBlockParser.ShareContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#standalone.
    def visitStandalone(self, ctx:ReqBlockParser.StandaloneContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#string.
    def visitString(self, ctx:ReqBlockParser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#symbol.
    def visitSymbol(self, ctx:ReqBlockParser.SymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#tag.
    def visitTag(self, ctx:ReqBlockParser.TagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#with_clause.
    def visitWith_clause(self, ctx:ReqBlockParser.With_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#expression.
    def visitExpression(self, ctx:ReqBlockParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#logical_op.
    def visitLogical_op(self, ctx:ReqBlockParser.Logical_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#relational_op.
    def visitRelational_op(self, ctx:ReqBlockParser.Relational_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#list_or.
    def visitList_or(self, ctx:ReqBlockParser.List_orContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#list_and.
    def visitList_and(self, ctx:ReqBlockParser.List_andContext):
        return self.visitChildren(ctx)



del ReqBlockParser