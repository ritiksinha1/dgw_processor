grammar ReqBlock;

/*
 *  The words reserved by the python antlr runtime are as follows:
 *
 *  python3Keywords = {
 *     "abs", "all", "any", "apply", "as", "assert",
 *     "bin", "bool", "buffer", "bytearray",
 *     "callable", "chr", "classmethod", "coerce", "compile", "complex",
 *     "del", "delattr", "dict", "dir", "divmod",
 *     "enumerate", "eval", "execfile",
 *     "file", "filter", "float", "format", "frozenset",
 *     "getattr", "globals",
 *     "hasattr", "hash", "help", "hex",
 *     "id", "input", "int", "intern", "isinstance", "issubclass", "iter",
 *     "len", "list", "locals",
 *     "map", "max", "min", "next",
 *     "memoryview",
 *     "object", "oct", "open", "ord",
 *     "pow", "print", "property",
 *     "range", "raw_input", "reduce", "reload", "repr", "return", "reversed", "round",
 *     "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super",
 *     "tuple", "type",
 *     "unichr", "unicode",
 *     "vars",
 *     "with",
 *     "zip",
 *     "__import__",
 *     "True", "False", "None"
 *  };
 *
 *  All these raise an error. If they don’t, it’s a bug.
 *
 */

/* Grammar
 * ------------------------------------------------------------------------------------------------
 */

req_block   : BEGIN head ';' body ENDDOT <EOF>;
head        :
            ( lastres
            | maxclass
            | maxcredit
            | maxpassfail
            | mingrade
            | mincredit
            | mingpa
            | minres
            | class_credit
            | proxy_advice
            | remark
            | share
            | under
            )*
            ;
body        :
            ( subset
            | group
            | block_type
            | label
            | remark
            | class_credit
            | maxperdisc
            )*
            ;

/* Parser
 * ------------------------------------------------------------------------------------------------
 */

/* Groups
 * 1. Group must be followed by a list of one or more rules. The list of rules following the Group
   keyword is referred to as the group list. Each rule in the group list is a group item. Each group
   item is enclosed in parentheses and does not end with a semicolon.
 * 2. Each rule in the Group list is one of the following types of rules: Course, Block, BlockType,
   Group, RuleComplete, RuleIncomplete or NonCourse. A group item cannot be an If rule or a subset
   rule.
 * 3. Each rule in the list is connected to the next rule by “or”.
 * 4. A Group statement can be nested within another Group statement. There is no limit to the
   number of times you can embed a Group within a Group. However, the worksheet display of a
   requirement with many depths may be difficult to understand.
 * 5. Qualifiers that must be applied to all rules in the group list must occur after the last right
   parenthesis and before the label at the end of the Group statement. Qualifiers that apply only to
   a specific rule in the group list must appear inside the parentheses for that group item rule.
 * 6. Allowable rule qualifiers: DontShare, Hide, HideRule, HighPriority, LowPriority,
   LowestPriority, MaxPassFail, MaxPerDisc, MaxTransfer, MinGrade, MinPerDisc, NotGPA, ProxyAdvice,
   SameDisc, ShareWith, MinClass, MinCredit, RuleTag.
 * 7. Do not mix course rules with Block rules in a group. Although this will parse, the auditor may
   not handle this as expected. Putting Block rules into Groups is not a best practice.
 */
group       : NUMBER GROUP INFROM? group_list group_qualifier* label ;
group_list  : group_item (OR group_item)* ;
group_item  : LP
            (class_credit
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

subset            : BEGINSUB (class_credit | group)+ ENDSUB subset_qualifier* label ;
subset_qualifier  : mingpa | mingrade | maxtransfer;

/* Blocks
 */
block       : NUMBER BLOCK LP SHARE_LIST RP ;
block_type  : NUMBER BLOCKTYPE SHARE_LIST label ;

/* Course Lists
 */
course_list     : INFROM? course (and_list | or_list)? with_clause? except_clause? HIDE? ;
course          : (SYMBOL | WILDSYMBOL) (NUMBER | RANGE | SYMBOL | WILDSYMBOL) ;
course_item     : SYMBOL? (NUMBER | SYMBOL) with_clause?;
and_list        : ( AND course_item )+ ;
or_list         : ( OR (course_item|hide_item) )+ ;
hide_item       : LB HIDE course_item (OR course_item)* OR? RB ;

/* Other Rules
 */
label           : LABEL (SYMBOL|NUMBER)? STRING ';'? label* ;
lastres         : LASTRES NUMBER (OF NUMBER CREDIT | CLASS)? ;
maxclass        : MAXCLASS NUMBER course_list TAG? ;
maxcredit       : MAXCREDIT NUMBER course_list TAG? ;
minclass        : MINCLASS NUMBER course_list TAG? ;
mincredit       : MINCREDIT NUMBER course_list TAG? ;
maxpassfail     : MAXPASSFAIL NUMBER (CREDIT | CLASS) course_list? TAG? ;
maxperdisc      : MAXPERDISC NUMBER (CREDIT | CLASS) INFROM? LP SYMBOL (',' SYMBOL)* RP TAG? ;
maxtransfer     : MAXTRANSFER NUMBER (CREDIT | CLASS) (INFROM? LP SYMBOL (',' SYMBOL)* RP)? TAG? ;
mingpa          : MINGPA NUMBER course_list? ;
mingrade        : MINGRADE NUMBER ;
minperdisc      : MINPERDISC NUMBER (CREDIT | CLASS) INFROM? LP SYMBOL (',' SYMBOL)* TAG? ;
minres          : MINRES NUMBER (CREDIT | CLASS) ;
class_credit    : (NUMBER | RANGE) (CLASS | CREDIT)
                  (LOG_OP (NUMBER | RANGE) (CLASS | CREDIT))? PSEUDO?
                  INFROM? course_list? share? TAG? label? ;
//numcredit       : (NUMBER | RANGE) CREDIT PSEUDO? course_list? TAG? ;
except_clause   : EXCEPT course_list ;
noncourse       : NUMBER NONCOURSE LP SYMBOL (',' SYMBOL)* RP ;
proxy_advice    : PROXYADVICE STRING proxy_advice* ;
remark          : REMARK STRING SEMI? remark* ;
rule_complete   : RULE_COMPLETE | RULE_INCOMPLETE ;
ruletag         : RULE_TAG SYMBOL EQ STRING ;
samedisc        : SAME_DISC LP SYMBOL EQ SYMBOL (COMMA SYMBOL EQ SYMBOL)* RP TAG? ;
share           : (SHARE | DONT_SHARE) (NUMBER (CREDIT | CLASS))? SHARE_LIST ;
under           : UNDER NUMBER (CREDIT | CLASS) INFROM? course or_list? proxy_advice label ;
with_clause     : LP WITH HIDE? with_list RP ;
with_list       : with_expr (LOG_OP with_expr)* ;
with_expr       : SYMBOL REL_OP (STRING | SYMBOL | NUMBER) (OR with_expr)* ;

/* Lexer
 * ------------------------------------------------------------------------------------------------
 */

//  Keywords
BEGIN           : [Bb][Ee][Gg][Ii][Nn] ;
BEGINSUB        : BEGIN [Ss][Uu][Bb] ;
BLOCK           : [Bb][Ll][Oo][Cc][Kk] ;
BLOCKTYPE       : BLOCK [Tt][Yy][Pp][Ee][Ss]? ;
CLASS           : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])? ;
CONC            : [Cc][Oo][Nn][Cc] ;
CREDIT          : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]? ;
DEGREE          : [Dd][Ee][Gg][Rr][Ee][Ee] ;
ENDDOT          : [Ee][Nn][Dd]DOT ;
ENDSUB          : [Ee][Nn][Dd][Ss][Uu][Bb] ;
EXCEPT          : [Ee][Xx][Cc][Ee][Pp][Tt] ;
GROUP           : [Gg][Rr][Oo][Uu][Pp] ;
/* Hide, HideRule, HideFromAdvice */
HIDE            : [Hh][Ii][Dd][Ee]
                    ((HYPHEN?[Ff][Rr][Oo][Mm]HYPHEN?[Aa][Dd][Vv][Ii][Cc][Ee])
                                      | (HYPHEN?[Rr][Uu][Ll][Ee]))? ;
LABEL           : [Ll][Aa][Bb][Ee][Ll] ;
LASTRES         : [Ll][Aa][Ss][Tt][Rr][Ee][Ss] ;
MAJOR           : [Mm][Aa][Jj][Oo][Rr] ;
MAXCLASS        : [Mm][Aa][Xx] CLASS ;
MAXCREDIT       : [Mm][Aa][Xx] CREDIT ;
MINGPA          : [Mm][Ii][Nn][Gg][Pp][Aa] ;
MINGRADE        : [Mm][Ii][Nn][Gg][Rr][Aa][Dd][Ee] ;
MAXPASSFAIL     : [Mm][Aa][Xx][Pp][Aa][Ss][Ss][Ff][Aa][Ii][Ll] ;
MAXPERDISC      : [Mm][Aa][Xx][Pp][Ee][Rr][Dd][Ii][Ss][Cc] ;
MINPERDISC      : [Mm][Ii][Nn][Pp][Ee][Rr][Dd][Ii][Ss][Cc] ;
MAXTRANSFER     : [Mm][Aa][Xx][Tt][Rr][Aa][Nn][Ss][Ff][Ee][Rr] ;
MINOR           : [Mm][Ii][Nn][Oo][Rr] ;
MINCLASS        : [Mm][Ii][Nn] CLASS ;
MINCREDIT       : [Mm][Ii][Nn] CREDIT ;
MINRES          : [Mm][Ii][Nn][Rr][Ee][Ss] ;
NONCOURSE       : [Nn][Oo][Nn][Cc][Oo][Uu][Rr][Ss][Ee][Ss]? ;
OTHER           : [Oo][Tt][Hh][Ee][Rr] ;
PROXYADVICE     : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] ;
PSEUDO          : [Pp][Ss][Ee][Uu][Dd][Oo] ;
REMARK          : [Rr][Ee][Mm][Aa][Rr][Kk] ;
RULE_COMPLETE   : [Rr][Uu][Ll][Ee][Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee] ;
RULE_INCOMPLETE : [Rr][Uu][Ll][Ee][Ii][Nn][Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee] ;
RULE_TAG        : [Rr][Uu][Ll][Ee][Tt][Aa][Gg] ;
SHARE           : [Ss][Hh][Aa][Rr][Ee]([Ww][Ii][Tt][Hh])?
                | [Nn][Oo][Nn][Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee] ;
DONT_SHARE      : [Dd][Oo][Nn][Tt][Ss][Ss][Hh][Aa][Rr][Ee]
                | [Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee] ;
SAME_DISC       : [Ss][Aa][Mm][Ee][Dd][Ii][Ss][Cc] ;
SHARE_LIST      : LP SHARE_ITEM (COMMA SHARE_ITEM)* RP ;
SHARE_ITEM      : DEGREE | CONC | MAJOR | MINOR | (OTHER (EQ SYMBOL)?) | THIS_BLOCK;
THIS_BLOCK      : [Tt][Hh][Ii][Ss][Bb][Ll][Oo][Cc][Kk] ;
UNDER           : [Uu][Nn][Dd][Ee][Rr] ;
WITH            : [Ww][Ii][Tt][Hh] ;


/* DWResident, DW... etc. are DWIDs */
/* (Decide=DWID) is a phrase used for tie-breaking by the auditor.*/

STRING      : '"' .*? '"' ;

INFROM      : IN | FROM ;
OR          : COMMA | [Oo][Rr] ;
AND         : PLUS | [Aa][Nn][Dd] ;

FROM        : [Ff][Rr][Oo][Mm] ;
IN          : [Ii][Nn] ;
OF          : [Oo][Ff] ;
TAG         : [Tt][Aa][Gg] (EQ SYMBOL)? ;

/* There are three overlapping classes of tokens used as identifiers:
 * The overlap is in what characters are allowed for each. Since the Scribe parser ensures that
 * the "allowed character set" is correct, this grammar lumps everthing together as a SYMBOL.
 *   Discipline names
 *   With clause names
 *   Named values
 * Keeping original defs here for back reference:
 *   ALPHA_NUM   : (LETTER | DIGIT | DOT | '_')+ ;
 *   DISCIPLINE  : ALPHA_NUM | ((LETTER | AT) (DIGIT | DOT | HYPHEN | LETTER)*) ;
 *   SYMBOL      : ALPHA_NUM | (LETTER (LETTER | DIGIT | '_' | '-' | '&')*) ;
 */
NUMBER      : DIGIT+ (DOT DIGIT*)? ;
RANGE       : NUMBER ':' NUMBER ;

SYMBOL      : (LETTER | DIGIT | DOT | HYPHEN | USCORE | AMP)+ ;
WILDSYMBOL  : (LETTER|DIGIT)* AT (LETTER|DIGIT)* ;

LOG_OP      : ([Aa][Nn][Dd])|([Oo][Rr]) ;
REL_OP      : EQ | GE | GT | LE | LT | NE ;

AMP         : '&' ;
AT          : '@' ;
COMMA       : ',' ;
EQ          : '=' ;
GE          : '>=' ;
GT          : '>' ;
HYPHEN      : '-' ;
LB          : '{' ;
LE          : '<=' ;
LP          : '(' ;
LT          : '<' ;
NE          : '<>' ;
PLUS        : '+' ;
RB          : '}' ;
RP          : ')' ;
SEMI        : ';' ;
USCORE      : '_' ;

fragment DOT         : '.' ;
fragment DIGIT       : [0-9] ;
fragment LETTER      : [a-zA-Z] ;

// Directives to the auditor, not requirements.
CHECKELECTIVES : [Cc][Hh][Ee][Cc][Kk]
                 [Ee][Ll][Ee][Cc][Tt][Ii][Vv][Ee]
                 [Cc][Rr][Ee][Dd][Ii][Tt][Ss]
                 [Aa][Ll][Ll][Oo][Ww][Ee][Dd] -> skip ;
COMMENT        : '#' .*? '\n' -> skip ;
DECIDE         : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip ;
HIDERULE       : [Hh][Ii][Dd][Ee][Rr][Uu][Ll][Ee] -> skip ;
NOTGPA         : [Nn][Oo][Tt][Gg][Pp][Aa] -> skip ;
PRIORITY       : ([Ll][Oo][Ww]([Ee][Ss][Tt])?)?([Hh][Ii][Gg][Hh])?
                 [Pp][Rr][Ii][Oo][Rr][Ii][Tt][Yy] -> skip ;
LOG            : [Ll][Oo][Gg] .*? '\n' -> skip ;

WHITESPACE  : [ \t\n\r]+ -> skip ;
