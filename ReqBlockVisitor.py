# Generated from ReqBlock.g4 by ANTLR 4.8
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


    # Visit a parse tree produced by ReqBlockParser#head.
    def visitHead(self, ctx:ReqBlockParser.HeadContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#body.
    def visitBody(self, ctx:ReqBlockParser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list.
    def visitCourse_list(self, ctx:ReqBlockParser.Course_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list_head.
    def visitCourse_list_head(self, ctx:ReqBlockParser.Course_list_headContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list_qualifier_head.
    def visitCourse_list_qualifier_head(self, ctx:ReqBlockParser.Course_list_qualifier_headContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list_body.
    def visitCourse_list_body(self, ctx:ReqBlockParser.Course_list_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#course_list_qualifier_body.
    def visitCourse_list_qualifier_body(self, ctx:ReqBlockParser.Course_list_qualifier_bodyContext):
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


    # Visit a parse tree produced by ReqBlockParser#catalog_number.
    def visitCatalog_number(self, ctx:ReqBlockParser.Catalog_numberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#discipline.
    def visitDiscipline(self, ctx:ReqBlockParser.DisciplineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#if_then.
    def visitIf_then(self, ctx:ReqBlockParser.If_thenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#else_clause.
    def visitElse_clause(self, ctx:ReqBlockParser.Else_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#stmt_group.
    def visitStmt_group(self, ctx:ReqBlockParser.Stmt_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#stmt.
    def visitStmt(self, ctx:ReqBlockParser.StmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#begin_if.
    def visitBegin_if(self, ctx:ReqBlockParser.Begin_ifContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#end_if.
    def visitEnd_if(self, ctx:ReqBlockParser.End_ifContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group.
    def visitGroup(self, ctx:ReqBlockParser.GroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group_list.
    def visitGroup_list(self, ctx:ReqBlockParser.Group_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group_item.
    def visitGroup_item(self, ctx:ReqBlockParser.Group_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#group_qualifier.
    def visitGroup_qualifier(self, ctx:ReqBlockParser.Group_qualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#subset.
    def visitSubset(self, ctx:ReqBlockParser.SubsetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#subset_qualifier.
    def visitSubset_qualifier(self, ctx:ReqBlockParser.Subset_qualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#block.
    def visitBlock(self, ctx:ReqBlockParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#blocktype.
    def visitBlocktype(self, ctx:ReqBlockParser.BlocktypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#allow_clause.
    def visitAllow_clause(self, ctx:ReqBlockParser.Allow_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#class_credit_head.
    def visitClass_credit_head(self, ctx:ReqBlockParser.Class_credit_headContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#class_credit_body.
    def visitClass_credit_body(self, ctx:ReqBlockParser.Class_credit_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#copy_rules.
    def visitCopy_rules(self, ctx:ReqBlockParser.Copy_rulesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#display.
    def visitDisplay(self, ctx:ReqBlockParser.DisplayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#except_list.
    def visitExcept_list(self, ctx:ReqBlockParser.Except_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#including_list.
    def visitIncluding_list(self, ctx:ReqBlockParser.Including_listContext):
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


    # Visit a parse tree produced by ReqBlockParser#noncourse.
    def visitNoncourse(self, ctx:ReqBlockParser.NoncourseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#optional.
    def visitOptional(self, ctx:ReqBlockParser.OptionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#remark.
    def visitRemark(self, ctx:ReqBlockParser.RemarkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#rule_complete.
    def visitRule_complete(self, ctx:ReqBlockParser.Rule_completeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#ruletag.
    def visitRuletag(self, ctx:ReqBlockParser.RuletagContext):
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


    # Visit a parse tree produced by ReqBlockParser#under.
    def visitUnder(self, ctx:ReqBlockParser.UnderContext):
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