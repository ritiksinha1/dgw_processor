# Generated from ReqBlock.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .ReqBlockParser import ReqBlockParser
else:
    from ReqBlockParser import ReqBlockParser

# This class defines a complete generic visitor for a parse tree produced by ReqBlockParser.

class ReqBlockVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ReqBlockParser#req_text.
    def visitReq_text(self, ctx:ReqBlockParser.Req_textContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#req_block.
    def visitReq_block(self, ctx:ReqBlockParser.Req_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#headers.
    def visitHeaders(self, ctx:ReqBlockParser.HeadersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#rules.
    def visitRules(self, ctx:ReqBlockParser.RulesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#or_courses.
    def visitOr_courses(self, ctx:ReqBlockParser.Or_coursesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#and_courses.
    def visitAnd_courses(self, ctx:ReqBlockParser.And_coursesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#mingpa.
    def visitMingpa(self, ctx:ReqBlockParser.MingpaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#minres.
    def visitMinres(self, ctx:ReqBlockParser.MinresContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#mingrade.
    def visitMingrade(self, ctx:ReqBlockParser.MingradeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#numclasses.
    def visitNumclasses(self, ctx:ReqBlockParser.NumclassesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#numcredits.
    def visitNumcredits(self, ctx:ReqBlockParser.NumcreditsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxcredits.
    def visitMaxcredits(self, ctx:ReqBlockParser.MaxcreditsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#proxy_advice.
    def visitProxy_advice(self, ctx:ReqBlockParser.Proxy_adviceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#exclusive.
    def visitExclusive(self, ctx:ReqBlockParser.ExclusiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#maxpassfail.
    def visitMaxpassfail(self, ctx:ReqBlockParser.MaxpassfailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#remark.
    def visitRemark(self, ctx:ReqBlockParser.RemarkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ReqBlockParser#label.
    def visitLabel(self, ctx:ReqBlockParser.LabelContext):
        return self.visitChildren(ctx)



del ReqBlockParser