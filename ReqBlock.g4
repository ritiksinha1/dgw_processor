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

//  Scribe Requirements Block Structure (the start rule)
//  ===============================================================================================
/*  Cruft before BEGIN and after ENDDOT can generate syntax errors. One solution is to filter it
 *  out before parsing the block. I haven't managed to filter it out within the grammar.
 */
req_block   : BEGIN head ';' body ENDDOT ;
head        :
            ( if_then
            | class_credit
            | lastres
            | maxclass
            | maxcredit
            | maxpassfail
            | mingrade
            | mincredit
            | mingpa
            | minres
            | remark
            | share
            | under
            )*
            ;
body        :
            ( if_then
            | block_type
            | class_credit
            | label
            | maxperdisc
            | group
            | remark
            | subset
            )*
            ;

/* Parser
 * ================================================================================================
 */

//  if-then
//  -----------------------------------------------------------------------------------------------
/*  When Major is used in ShareWith it refers to the Major block in the audit. When used in an If-
 *  statement it refers to the major on the student’s curriculum.
 */
if_then      : IF expression THEN (stmt | stmt_group) group_qualifier* label? else_clause? ;
else_clause  : ELSE (stmt | stmt_group) group_qualifier* label? ;
stmt_group   : (begin_if stmt+ end_if) ;
stmt         : subset | group | block | class_credit | rule_complete | remark;
begin_if     : BEGINIF | BEGINELSE ;
end_if       : ENDIF | ENDELSE ;


//  Groups
//  -----------------------------------------------------------------------------------------------
group           : NUMBER GROUP INFROM? group_list group_qualifier* label ;
group_item      : LP
                    (class_credit | block | block_type | group | rule_complete | noncourse )
                    group_qualifier*
                    label
                  RP
                  group_qualifier* label;
group_list      : group_item (OP group_item)* ;
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

//  Rule Subset
//  -----------------------------------------------------------------------------------------------
subset            : BEGINSUB (class_credit | group)+ ENDSUB subset_qualifier* label ;
subset_qualifier  : mingpa | mingrade | maxtransfer;

// Blocks
// ------------------------------------------------------------------------------------------------
block       : NUMBER BLOCK expression label;
block_type  : NUMBER BLOCKTYPE expression label ;

// Course Lists
// ------------------------------------------------------------------------------------------------
course_list     : INFROM? full_course (and_list | or_list)? with_clause? except_clause? ;
full_course     : discipline catalog_number with_clause? ;
course_item     : discipline? catalog_number with_clause? ;
and_list        : (LIST_AND course_item )+ ;
or_list         : (LIST_OR course_item)+ ;
discipline      : SYMBOL | WILDSYMBOL | HIDE;
catalog_number  : (NUMBER | CATALOG_NUMBER | RANGE | WILDNUMBER) RB? ;

/* Other Rules and Rule Components
 * ------------------------------------------------------------------------------------------------
 */
label           : LABEL (SYMBOL|NUMBER)? STRING ';'? label* ;
lastres         : LASTRES NUMBER (OF NUMBER CREDIT | CLASS)? ;
maxclass        : MAXCLASS NUMBER course_list TAG? ;
maxcredit       : MAXCREDIT NUMBER course_list TAG? ;
minclass        : MINCLASS NUMBER course_list TAG? ;
mincredit       : MINCREDIT NUMBER course_list TAG? ;
maxpassfail     : MAXPASSFAIL NUMBER (CREDIT | CLASS) course_list? TAG? ;
maxperdisc      : MAXPERDISC NUMBER (CREDIT | CLASS)
                  INFROM? LP SYMBOL (LIST_OR SYMBOL)* RP TAG? ;
maxtransfer     : MAXTRANSFER NUMBER (CREDIT | CLASS)
                  (INFROM? LP SYMBOL (LIST_OR SYMBOL)* RP)? TAG? ;
mingpa          : MINGPA NUMBER course_list? ;
mingrade        : MINGRADE NUMBER ;
minperdisc      : MINPERDISC NUMBER (CREDIT | CLASS) INFROM? LP SYMBOL (',' SYMBOL)* TAG? ;
minres          : MINRES NUMBER (CREDIT | CLASS) ;
minspread       : MINSPREAD NUMBER TAG? ;
class_credit    : (NUMBER | RANGE) (CLASS | CREDIT) expression? PSEUDO?
                  INFROM? course_list? share? TAG? label? ;
except_clause   : EXCEPT course_list ;
noncourse       : NUMBER NONCOURSE LP SYMBOL (',' SYMBOL)* RP ;
remark          : REMARK STRING SEMICOLON? remark* ;
rule_complete   : RULE_COMPLETE | RULE_INCOMPLETE ;
ruletag         : RULE_TAG SYMBOL EQ STRING ;
samedisc        : SAME_DISC LP SYMBOL OP SYMBOL (LIST_OR SYMBOL OP SYMBOL)* RP TAG? ;
under           : UNDER NUMBER (CREDIT | CLASS) INFROM? full_course or_list? label ;

with_clause     : LP WITH HIDE? expression RP ;

share           : (SHARE | DONT_SHARE) (NUMBER (CREDIT | CLASS))? LP share_list RP ;
share_item      : SYMBOL (OP (SYMBOL | NUMBER | STRING))? ;
share_list      : share_item (LIST_OR share_item)* ;

expression      : expression OP expression
                | NUMBER
                | SYMBOL
                | LP expression RP
                ;

// Lexer
// ================================================================================================

//  Keywords
//  -----------------------------------------------------------------------------------------------
BEGIN           : [Bb][Ee][Gg][Ii][Nn] ;
BEGINSUB        : BEGIN [Ss][Uu][Bb] ;
BLOCK           : [Bb][Ll][Oo][Cc][Kk] ;
BLOCKTYPE       : BLOCK [Tt][Yy][Pp][Ee][Ss]? ;
CLASS           : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])? ;
CREDIT          : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]? ;

/*  These symbols appear in SHARE expressions, but they get in the way of recognizing other
 *  expressions, so recognizing them is left to dgw_processor to recognize on an as-needed basis.
  CONC            : [Cc][Oo][Nn][Cc] ;
  DEGREE          : [Dd][Ee][Gg][Rr][Ee][Ee] ;
  MAJOR           : [Mm][Aa][Jj][Oo][Rr] ;
  MINOR           : [Mm][Ii][Nn][Oo][Rr] ;
  OTHER           : [Oo][Tt][Hh][Ee][Rr] ;
  THIS_BLOCK      : [Tt][Hh][Ii][Ss][Bb][Ll][Oo][Cc][Kk] ;
 */

ENDDOT          : [Ee][Nn][Dd]DOT ;
ENDSUB          : [Ee][Nn][Dd][Ss][Uu][Bb] ;
EXCEPT          : [Ee][Xx][Cc][Ee][Pp][Tt] ;
GROUP           : [Gg][Rr][Oo][Uu][Pp][Ss]? ;

LABEL           : [Ll][Aa][Bb][Ee][Ll] ;
LASTRES         : [Ll][Aa][Ss][Tt][Rr][Ee][Ss] ;
MAXCLASS        : [Mm][Aa][Xx] CLASS ;
MAXCREDIT       : [Mm][Aa][Xx] CREDIT ;
MINGPA          : [Mm][Ii][Nn][Gg][Pp][Aa] ;
MINGRADE        : [Mm][Ii][Nn][Gg][Rr][Aa][Dd][Ee] ;
MAXPASSFAIL     : [Mm][Aa][Xx][Pp][Aa][Ss][Ss][Ff][Aa][Ii][Ll] ;
MAXPERDISC      : [Mm][Aa][Xx][Pp][Ee][Rr][Dd][Ii][Ss][Cc] ;
MINPERDISC      : [Mm][Ii][Nn][Pp][Ee][Rr][Dd][Ii][Ss][Cc] ;
MAXTRANSFER     : [Mm][Aa][Xx][Tt][Rr][Aa][Nn][Ss][Ff][Ee][Rr] ;
MINCLASS        : [Mm][Ii][Nn] CLASS ;
MINCREDIT       : [Mm][Ii][Nn] CREDIT ;
MINRES          : [Mm][Ii][Nn][Rr][Ee][Ss] ;
MINSPREAD       : [Mm][Ii][Nn][Ss][Pp][Rr][Ee][Aa][Dd] ;
NONCOURSE       : [Nn][Oo][Nn][Cc][Oo][Uu][Rr][Ss][Ee][Ss]? ;
PSEUDO          : [Pp][Ss][Ee][Uu][Dd][Oo] ;
REMARK          : [Rr][Ee][Mm][Aa][Rr][Kk] ;
RULE_COMPLETE   : [Rr][Uu][Ll][Ee][\-]?[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee] ;
RULE_INCOMPLETE : [Rr][Uu][Ll][Ee][\-]?[Ii][Nn][Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee] ;
RULE_TAG        : [Rr][Uu][Ll][Ee][Tt][Aa][Gg] ;
SHARE           : [Ss][Hh][Aa][Rr][Ee]([Ww][Ii][Tt][Hh])?
                | [Nn][Oo][Nn][Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee] ;
DONT_SHARE      : [Dd][Oo][Nn][Tt][Ss][Ss][Hh][Aa][Rr][Ee]
                | [Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee] ;

SAME_DISC       : [Ss][Aa][Mm][Ee][Dd][Ii][Ss][Cc] ;
UNDER           : [Uu][Nn][Dd][Ee][Rr] ;
WITH            : LP [Ww][Ii][Tt][Hh] ;

// If-Else keywords
BEGINELSE       : BEGIN ELSE ;
BEGINIF         : BEGIN IF ;
ELSE            : [Ee][Ll][Ss][Ee] ;
ENDELSE         : [Ee][Nn][Dd]ELSE ;
ENDIF           : [Ee][Nn][Dd] IF ;
IF              : [Ii][Ff] ;
IS              : ([Ii][Ss])|([Ww][Aa][Ss]) ;
ISNT            : ([Ii][Ss][Nn][Tt])|([Ww][Aa][Ss][Nn][Tt]) ;
THEN            : [Tt][Hh][Ee][Nn] ;

OP          : AND | OR | EQ | GE | GT | LE | LT | NE ;

LIST_OR     : COMMA | OR ;
LIST_AND    : PLUS | AND ;
AND         : [Aa][Nn][Dd] ;
OR          : [Oo][Rr] ;

INFROM      : IN | FROM ;
FROM        : [Ff][Rr][Oo][Mm] ;
IN          : [Ii][Nn] ;

OF          : [Oo][Ff] ;
TAG         : [Tt][Aa][Gg] (EQ SYMBOL)? ;



/* There are three overlapping classes of tokens used as identifiers.
 * The overlap is in what characters are allowed for each. Since the Scribe parser ensures that
 * the "allowed character set" is correct, this grammar lumps everthing together as a SYMBOL.
 *   Discipline names
 *   With clause names
 *   Named values
 * Keeping expanded defs here, for reference:
 *   ALPHA_NUM   : (LETTER | DIGIT | DOT | '_')+ ;
 *   DISCIPLINE  : ALPHA_NUM | ((LETTER | AT) (DIGIT | DOT | HYPHEN | LETTER)*) ;
 *   SYMBOL      : ALPHA_NUM | (LETTER (LETTER | DIGIT | '_' | '-' | '&')*) ;
 */

NUMBER          : DIGIT+ (DOT DIGIT*)? ;
RANGE           : NUMBER ':' NUMBER ;

CATALOG_NUMBER  : DIGIT+ LETTER+ ;
WILDNUMBER      : NUMBER* AT NUMBER* ;
WILDSYMBOL      : LETTER* AT (LETTER|DIGIT)* ;

SYMBOL          : (LETTER | DIGIT | DOT | HYPHEN | UNDERSCORE | AMPERSAND)+ ;

STRING      : '"' .*? '"' ;

//  Punctuation and operator tokens
//  -----------------------------------------------------------------------------------------------
AMPERSAND   : '&' ;
AT          : '@' ;
COMMA       : ',' ;
EQ          : '=' ;
GE          : '>=' ;
GT          : '>' ;
HYPHEN      : '-' ;
LE          : '<=' ;
LP          : '(' ;
LT          : '<' ;
NE          : '<>' ;
PLUS        : '+' ;
RP          : ')' ;
SEMICOLON   : ';' ;
UNDERSCORE  : '_' ;

//  Fragments
//  -----------------------------------------------------------------------------------------------
/*  By prefixing the rule with fragment, we let ANTLR know that the rule will be used only by other
 *  lexical rules. It is not a token in and of itself.
 */
fragment DOT         : '.' ;
fragment DIGIT       : [0-9] ;
fragment LETTER      : [a-zA-Z] ;

//  Skips
//  -----------------------------------------------------------------------------------------------
// Directives to the auditor, not requirements.
CHECKELECTIVES : [Cc][Hh][Ee][Cc][Kk]
                 [Ee][Ll][Ee][Cc][Tt][Ii][Vv][Ee]
                 [Cc][Rr][Ee][Dd][Ii][Tt][Ss]
                 [Aa][Ll][Ll][Oo][Ww][Ee][Dd] -> skip ;
COMMENT        : '#' .*? '\n' -> skip ;
/* DWResident, DW... etc. are DWIDs
 * (Decide=DWID) is a phrase used for tie-breaking by the auditor. */
DECIDE         : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip ;

PROXYADVICE    : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] .*? '\n' -> skip;
NOTGPA         : [Nn][Oo][Tt][Gg][Pp][Aa] -> skip ;
PRIORITY       : ([Ll][Oo][Ww]([Ee][Ss][Tt])?)?([Hh][Ii][Gg][Hh])?
                 [Pp][Rr][Ii][Oo][Rr][Ii][Tt][Yy] -> skip ;
HIDE_RULE      : [Hh][Ii][Dd][Ee] HYPHEN? [Rr][Uu][Ll][Ee] -> skip ;

// Hide (=== HideFromAdvice)
HIDE        : '{' ' '* [Hh][Ii][Dd][Ee] (HYPHEN? [Ff][Rr][Oo][Mm] HYPHEN? [Aa][Dd][Vv][Ii][Cc][Ee])?;
// Things outside the BEGIN...ENDDOT that cause unnecessary grief
LOG            : [Ll][Oo][Gg] .*? '\n' -> skip ;
// Including '/' as whitespace is a hack to reduce token recognition errors: I can't figure out how
// to ignore text following ENDDOT.
WHITESPACE  : [ \t\n\r/]+ -> skip ;
