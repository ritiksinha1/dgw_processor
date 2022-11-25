# Generated from ReqBlock.g4 by ANTLR 4.11.1
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


    # Enter a parse tree produced by ReqBlockParser#header.
    def enterHeader(self, ctx:ReqBlockParser.HeaderContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header.
    def exitHeader(self, ctx:ReqBlockParser.HeaderContext):
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


    # Enter a parse tree produced by ReqBlockParser#course_list_body.
    def enterCourse_list_body(self, ctx:ReqBlockParser.Course_list_bodyContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#course_list_body.
    def exitCourse_list_body(self, ctx:ReqBlockParser.Course_list_bodyContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#course_list_rule.
    def enterCourse_list_rule(self, ctx:ReqBlockParser.Course_list_ruleContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#course_list_rule.
    def exitCourse_list_rule(self, ctx:ReqBlockParser.Course_list_ruleContext):
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


    # Enter a parse tree produced by ReqBlockParser#header_conditional.
    def enterHeader_conditional(self, ctx:ReqBlockParser.Header_conditionalContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_conditional.
    def exitHeader_conditional(self, ctx:ReqBlockParser.Header_conditionalContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_else.
    def enterHeader_else(self, ctx:ReqBlockParser.Header_elseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_else.
    def exitHeader_else(self, ctx:ReqBlockParser.Header_elseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_rule_group.
    def enterHeader_rule_group(self, ctx:ReqBlockParser.Header_rule_groupContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_rule_group.
    def exitHeader_rule_group(self, ctx:ReqBlockParser.Header_rule_groupContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_rule.
    def enterHeader_rule(self, ctx:ReqBlockParser.Header_ruleContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_rule.
    def exitHeader_rule(self, ctx:ReqBlockParser.Header_ruleContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#body_conditional.
    def enterBody_conditional(self, ctx:ReqBlockParser.Body_conditionalContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#body_conditional.
    def exitBody_conditional(self, ctx:ReqBlockParser.Body_conditionalContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#body_else.
    def enterBody_else(self, ctx:ReqBlockParser.Body_elseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#body_else.
    def exitBody_else(self, ctx:ReqBlockParser.Body_elseContext):
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


    # Enter a parse tree produced by ReqBlockParser#group_requirement.
    def enterGroup_requirement(self, ctx:ReqBlockParser.Group_requirementContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#group_requirement.
    def exitGroup_requirement(self, ctx:ReqBlockParser.Group_requirementContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#group_list.
    def enterGroup_list(self, ctx:ReqBlockParser.Group_listContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#group_list.
    def exitGroup_list(self, ctx:ReqBlockParser.Group_listContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#group.
    def enterGroup(self, ctx:ReqBlockParser.GroupContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#group.
    def exitGroup(self, ctx:ReqBlockParser.GroupContext):
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


    # Enter a parse tree produced by ReqBlockParser#noncourse.
    def enterNoncourse(self, ctx:ReqBlockParser.NoncourseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#noncourse.
    def exitNoncourse(self, ctx:ReqBlockParser.NoncourseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#rule_complete.
    def enterRule_complete(self, ctx:ReqBlockParser.Rule_completeContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#rule_complete.
    def exitRule_complete(self, ctx:ReqBlockParser.Rule_completeContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#under.
    def enterUnder(self, ctx:ReqBlockParser.UnderContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#under.
    def exitUnder(self, ctx:ReqBlockParser.UnderContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#allow_clause.
    def enterAllow_clause(self, ctx:ReqBlockParser.Allow_clauseContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#allow_clause.
    def exitAllow_clause(self, ctx:ReqBlockParser.Allow_clauseContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_class_credit.
    def enterHeader_class_credit(self, ctx:ReqBlockParser.Header_class_creditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_class_credit.
    def exitHeader_class_credit(self, ctx:ReqBlockParser.Header_class_creditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#body_class_credit.
    def enterBody_class_credit(self, ctx:ReqBlockParser.Body_class_creditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#body_class_credit.
    def exitBody_class_credit(self, ctx:ReqBlockParser.Body_class_creditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_maxclass.
    def enterHeader_maxclass(self, ctx:ReqBlockParser.Header_maxclassContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_maxclass.
    def exitHeader_maxclass(self, ctx:ReqBlockParser.Header_maxclassContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_maxcredit.
    def enterHeader_maxcredit(self, ctx:ReqBlockParser.Header_maxcreditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_maxcredit.
    def exitHeader_maxcredit(self, ctx:ReqBlockParser.Header_maxcreditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_maxpassfail.
    def enterHeader_maxpassfail(self, ctx:ReqBlockParser.Header_maxpassfailContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_maxpassfail.
    def exitHeader_maxpassfail(self, ctx:ReqBlockParser.Header_maxpassfailContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_maxperdisc.
    def enterHeader_maxperdisc(self, ctx:ReqBlockParser.Header_maxperdiscContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_maxperdisc.
    def exitHeader_maxperdisc(self, ctx:ReqBlockParser.Header_maxperdiscContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_maxterm.
    def enterHeader_maxterm(self, ctx:ReqBlockParser.Header_maxtermContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_maxterm.
    def exitHeader_maxterm(self, ctx:ReqBlockParser.Header_maxtermContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_maxtransfer.
    def enterHeader_maxtransfer(self, ctx:ReqBlockParser.Header_maxtransferContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_maxtransfer.
    def exitHeader_maxtransfer(self, ctx:ReqBlockParser.Header_maxtransferContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_minclass.
    def enterHeader_minclass(self, ctx:ReqBlockParser.Header_minclassContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_minclass.
    def exitHeader_minclass(self, ctx:ReqBlockParser.Header_minclassContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_mincredit.
    def enterHeader_mincredit(self, ctx:ReqBlockParser.Header_mincreditContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_mincredit.
    def exitHeader_mincredit(self, ctx:ReqBlockParser.Header_mincreditContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_mingpa.
    def enterHeader_mingpa(self, ctx:ReqBlockParser.Header_mingpaContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_mingpa.
    def exitHeader_mingpa(self, ctx:ReqBlockParser.Header_mingpaContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_mingrade.
    def enterHeader_mingrade(self, ctx:ReqBlockParser.Header_mingradeContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_mingrade.
    def exitHeader_mingrade(self, ctx:ReqBlockParser.Header_mingradeContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_minperdisc.
    def enterHeader_minperdisc(self, ctx:ReqBlockParser.Header_minperdiscContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_minperdisc.
    def exitHeader_minperdisc(self, ctx:ReqBlockParser.Header_minperdiscContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_minres.
    def enterHeader_minres(self, ctx:ReqBlockParser.Header_minresContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_minres.
    def exitHeader_minres(self, ctx:ReqBlockParser.Header_minresContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_minterm.
    def enterHeader_minterm(self, ctx:ReqBlockParser.Header_mintermContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_minterm.
    def exitHeader_minterm(self, ctx:ReqBlockParser.Header_mintermContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_share.
    def enterHeader_share(self, ctx:ReqBlockParser.Header_shareContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_share.
    def exitHeader_share(self, ctx:ReqBlockParser.Header_shareContext):
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


    # Enter a parse tree produced by ReqBlockParser#copy_header.
    def enterCopy_header(self, ctx:ReqBlockParser.Copy_headerContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#copy_header.
    def exitCopy_header(self, ctx:ReqBlockParser.Copy_headerContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#copy_rules.
    def enterCopy_rules(self, ctx:ReqBlockParser.Copy_rulesContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#copy_rules.
    def exitCopy_rules(self, ctx:ReqBlockParser.Copy_rulesContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#advice.
    def enterAdvice(self, ctx:ReqBlockParser.AdviceContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#advice.
    def exitAdvice(self, ctx:ReqBlockParser.AdviceContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#display.
    def enterDisplay(self, ctx:ReqBlockParser.DisplayContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#display.
    def exitDisplay(self, ctx:ReqBlockParser.DisplayContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#proxy_advice.
    def enterProxy_advice(self, ctx:ReqBlockParser.Proxy_adviceContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#proxy_advice.
    def exitProxy_advice(self, ctx:ReqBlockParser.Proxy_adviceContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_tag.
    def enterHeader_tag(self, ctx:ReqBlockParser.Header_tagContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_tag.
    def exitHeader_tag(self, ctx:ReqBlockParser.Header_tagContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#header_label.
    def enterHeader_label(self, ctx:ReqBlockParser.Header_labelContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#header_label.
    def exitHeader_label(self, ctx:ReqBlockParser.Header_labelContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#hide_rule.
    def enterHide_rule(self, ctx:ReqBlockParser.Hide_ruleContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#hide_rule.
    def exitHide_rule(self, ctx:ReqBlockParser.Hide_ruleContext):
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


    # Enter a parse tree produced by ReqBlockParser#nv_lhs.
    def enterNv_lhs(self, ctx:ReqBlockParser.Nv_lhsContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#nv_lhs.
    def exitNv_lhs(self, ctx:ReqBlockParser.Nv_lhsContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#nv_rhs.
    def enterNv_rhs(self, ctx:ReqBlockParser.Nv_rhsContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#nv_rhs.
    def exitNv_rhs(self, ctx:ReqBlockParser.Nv_rhsContext):
        pass


    # Enter a parse tree produced by ReqBlockParser#optional.
    def enterOptional(self, ctx:ReqBlockParser.OptionalContext):
        pass

    # Exit a parse tree produced by ReqBlockParser#optional.
    def exitOptional(self, ctx:ReqBlockParser.OptionalContext):
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