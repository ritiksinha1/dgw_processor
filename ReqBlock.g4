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

/* Parser
 * ================================================================================================
 */
req_block   : .*? BEGIN head SEMICOLON body ENDOT .*? EOF;
head        :
            ( class_credit
            | if_then
            | lastres
            | maxclass
            | maxcredit
            | maxpassfail
            | maxperdisc
            | maxtransfer
            | mingrade
            | minclass
            | mincredit
            | mingpa
            | minperdisc
            | minres
            | remark
            | share
            | under
            )*
            ;
body        :
            ( block
            | blocktype
            | class_credit
            | copy_rules
            | group
            | if_then
            | label
            | maxperdisc
            | minclass
            | minperdisc
            | noncourse
            | remark
            | subset
            )*
            ;

/*  When Major is used in ShareWith it refers to the Major block in the audit. When used in an If-
 *  statement it refers to the major on the student’s curriculum.
 */

// Course List
// ------------------------------------------------------------------------------------------------
/* NOT IMPLEMENTED: parts of a course list can be enclosed in square brackets, defining "areas"
 * to which the minarea qualifier can apply. Currently, square brackets are skipped (ignored).
 */
course_list     : course_item (and_list | or_list)? course_qualifier* label?;
full_course     : discipline catalog_number course_qualifier*;
course_item     : discipline? catalog_number course_qualifier*;
and_list        : (list_and course_item )+;
or_list         : (list_or course_item)+;
discipline      : SYMBOL | WILD | IS; // The IS keyword can be a discipline name. (others?)
catalog_number  : SYMBOL | NUMBER | CATALOG_NUMBER | RANGE | WILD;
course_qualifier: with_clause
                | except_clause
                | including_clause
                | maxpassfail
                | maxperdisc
                | maxspread
                | maxtransfer
                | minarea
                | mincredit
                | mingpa
                | mingrade
                | minspread
                | ruletag
                | samedisc
                | share
                | with_clause
                ;

//  if-then
//  -----------------------------------------------------------------------------------------------
if_then      : IF expression THEN (stmt | stmt_group) group_qualifier* label? else_clause?;
else_clause  : ELSE (stmt | stmt_group) group_qualifier* label?;
stmt_group   : (begin_if stmt+ end_if);
stmt         : block
             | blocktype
             | class_credit
             | group
             | if_then
             | maxcredit
             | maxtransfer
             | minclass
             | minres
             | noncourse
             | remark
             | rule_complete
             | share
             | subset
             ;
begin_if     : BEGINIF | BEGINELSE;
end_if       : ENDIF | ENDELSE;

//  Groups
//  -----------------------------------------------------------------------------------------------
group           : NUMBER GROUP group_list
                  group_qualifier*
                  label?
                ;
group_list      : group_item (logical_op group_item)*; // But only OR should occur
group_item      : LP
                    (block | blocktype | class_credit | group | noncourse | rule_complete)
                    group_qualifier*
                    label?
                  RP
                  group_qualifier*
                  label?
                ;
group_qualifier : maxpassfail
                | maxtransfer
                | mingrade
                | mingpa
                | minperdisc
                | samedisc
                | share
                | minclass
                | mincredit
                | ruletag
                ;

//  Rule Subset
//  -----------------------------------------------------------------------------------------------
subset            : BEGINSUB
                  ( if_then
                  | class_credit
                  | copy_rules
                  | group)+
                  ENDSUB subset_qualifier* label?;
subset_qualifier  : mingpa | mingrade | maxtransfer | minperdisc | maxperdisc | ruletag | share;

// Blocks
// ------------------------------------------------------------------------------------------------
block           : NUMBER BLOCK expression label;
blocktype       : NUMBER BLOCKTYPE expression label;

/* Other Rules and Rule Components
 * ------------------------------------------------------------------------------------------------
 */
allow_clause    : LP ALLOW (NUMBER|RANGE) RP;
class_credit    : (NUMBER | RANGE) (CLASS | CREDIT)
                  allow_clause?
                  (logical_op NUMBER (CLASS | CREDIT) ruletag? allow_clause?)?
                  (course_list | expression | PSEUDO | share | tag)* label?;
copy_rules      : COPY_RULES expression SEMICOLON?;
except_clause   : EXCEPT course_list;
including_clause: INCLUDING course_list;
label           : LABEL label_tag? STRING SEMICOLON? label*;
label_tag       : .+?;

lastres         : LASTRES NUMBER (OF NUMBER )? (CLASS | CREDIT) course_list? tag?;

maxclass        : MAXCLASS NUMBER course_list? tag?;
maxcredit       : MAXCREDIT NUMBER course_list? tag?;

maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT) course_list? tag?;
maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP tag?;
maxspread       : MAXSPREAD NUMBER tag?;
maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
minarea         : MINAREA NUMBER tag?;
minclass        : MINCLASS NUMBER course_list tag?;
mincredit       : MINCREDIT NUMBER course_list tag?;

mingpa          : MINGPA NUMBER (course_list | expression)? tag? label?;
mingrade        : MINGRADE NUMBER;
minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP tag?;
minres          : MINRES NUMBER (CLASS | CREDIT) label?;
minspread       : MINSPREAD NUMBER tag?;

noncourse       : NUMBER NONCOURSE expression label?;
remark          : REMARK STRING SEMICOLON? remark*;
rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) label?;
ruletag         : RULE_TAG expression;
samedisc        : SAME_DISC LP SYMBOL logical_op SYMBOL (list_or SYMBOL logical_op SYMBOL)* RP tag?;
share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? (LP share_list RP)? tag?;
share_item      : SYMBOL (logical_op (SYMBOL | NUMBER | STRING | WILD))?;
share_list      : share_item (list_or share_item)*;
tag             : TAG (EQ (NUMBER|SYMBOL|CATALOG_NUMBER))?;
under           : UNDER NUMBER (CLASS | CREDIT)  full_course or_list? label;
with_clause     : LP WITH expression RP;

expression      : expression logical_op expression
                | full_course
                | NUMBER
                | SYMBOL
                | STRING
                | CATALOG_NUMBER
                | LP expression RP
                ;

// Operators and Separators
logical_op  : (AND | OR | EQ | GE | GT | IS | ISNT | LE | LT | NE);
list_or     : (COMMA | OR);
list_and    : (PLUS | AND);

// Lexer
// ================================================================================================

//  Skips
//  -----------------------------------------------------------------------------------------------
// Comments and auditor directives, not requirements.
CHECKELECTIVES  : [Cc][Hh][Ee][Cc][Kk]
                 [Ee][Ll][Ee][Cc][Tt][Ii][Vv][Ee]
                 [Cc][Rr][Ee][Dd][Ii][Tt][Ss]
                 [Aa][Ll][Ll][Oo][Ww][Ee][Dd] -> skip;
COMMENT         : '#' .*? '\n' -> skip;
CURLY_BRACES    : [}{] -> skip;
DECIDE          : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip;
DISPLAY         : [Dd][Ii][Ss][Pp][Ll][Aa][Yy] .*? '\n' -> skip;
FROM            : [Ff][Rr][Oo][Mm] -> skip;
FROM_ADVICE     : '-'?[Ff][Rr][Oo][Mm]'-'?[Aa][Dd][Vv][Ii][Cc][Ee] -> skip;
//HIDE            : ([Hh][Ii][Dd][Ee])?
//                  ('-'?[Ff][Rr][Oo][Mm]'-'?[Aa][Dd][Vv][Ii][Cc][Ee])? -> skip;
HIDE_RULE       : [Hh][Ii][Dd][Ee] '-'? [Rr][Uu][Ll][Ee] -> skip;
HIGH_PRIORITY   : [Hh][Ii][Gg][Hh]([Ee][Ss][Tt])? [ -]? [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip;
IN              : [Ii][Nn] -> skip;
LOW_PRIORITY    : [Ll][Oo][Ww]([Ee][Ss][Tt])? [ -]? [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip;
NOTGPA          : [Nn][Oo][Tt][Gg][Pp][Aa] -> skip;
PROXYADVICE     : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] .*? '\n' -> skip;

// Before BEGIN and fter ENDOT, the lexer does token recognition.
// To avoid errors from text that can't be tokenized, skip Log lines and otherwise-illegal chars.
LOGS            : [Ll][Oo][Gg] .*? '\n' -> skip;
CRUFT           : [:/'*\\]+ -> skip;

SB              : [[\]] ->skip; // Used for MinAreas; not implemented
WHITESPACE      : [ \t\n\r]+ -> skip;

//  Keywords
//  -----------------------------------------------------------------------------------------------
/*  These symbols appear in SHARE expressions, but they get in the way of recognizing other
 *  expressions, so recognizing them is left to dgw_processor to recognize on an as-needed basis.
  CONC            : [Cc][Oo][Nn][Cc];
  DEGREE          : [Dd][Ee][Gg][Rr][Ee][Ee];
  MAJOR           : [Mm][Aa][Jj][Oo][Rr];
  MINOR           : [Mm][Ii][Nn][Oo][Rr];
  OTHER           : [Oo][Tt][Hh][Ee][Rr];
  THIS_BLOCK      : [Tt][Hh][Ii][Ss][Bb][Ll][Oo][Cc][Kk];
 */
ALLOW           : [Aa][Ll][Ll][Oo][Ww];
BEGIN           : [Bb][Ee][Gg][Ii][Nn];
BEGINSUB        : BEGIN [Ss][Uu][Bb];
BLOCK           : [Bb][Ll][Oo][Cc][Kk];
BLOCKTYPE       : BLOCK [Tt][Yy][Pp][Ee][Ss]?;
CLASS           : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])?
                | [Cc][Oo][Uu][Rr][Ss][Ee][Ss]?;
COPY_RULES      : [Cc][Oo][Pp][Yy]'-'?[Rr][Uu][Ll][Ee][Ss]?'-'?[Ff][Rr][Oo][Mm];
CREDIT          : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]?;
DONT_SHARE      : [Dd][Oo][Nn][Tt]'-'?[Ss][Hh][Aa][Rr][Ee]([Ww][Ii][Tt][Hh])?
                | [Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee];
ENDOT           : [Ee][Nn][Dd]DOT;
ENDSUB          : [Ee][Nn][Dd][Ss][Uu][Bb];
EXCEPT          : [Ee][Xx][Cc][Ee][Pp][Tt];
GROUP           : [Gg][Rr][Oo][Uu][Pp][Ss]?;
INCLUDING       : [Ii][Nn][Cc][Ll][Uu][Dd][Ii][Nn][Gg];
LABEL           : [Ll][Aa][Bb][Ee][Ll];
LASTRES         : [Ll][Aa][Ss][Tt][Rr][Ee][Ss];
MAXCLASS        : [Mm][Aa][Xx] CLASS;
MAXCREDIT       : [Mm][Aa][Xx] CREDIT;
MINAREA         : [Mm][Ii][Nn][Aa][Rr][Ee][Aa][Ss]?;
MINGPA          : [Mm][Ii][Nn][Gg][Pp][Aa];
MINGRADE        : [Mm][Ii][Nn][Gg][Rr][Aa][Dd][Ee];
MAXPASSFAIL     : [Mm][Aa][Xx][Pp][Aa][Ss][Ss][Ff][Aa][Ii][Ll];
MAXPERDISC      : [Mm][Aa][Xx][Pp][Ee][Rr][Dd][Ii][Ss][Cc];
MINPERDISC      : [Mm][Ii][Nn][Pp][Ee][Rr][Dd][Ii][Ss][Cc];
MAXSPREAD       : [Mm][Aa][Xx][Ss][Pp][Rr][Ee][Aa][Dd];
MAXTRANSFER     : [Mm][Aa][Xx][Tt][Rr][Aa][Nn][Ss][Ff][Ee][Rr];
MINCLASS        : [Mm][Ii][Nn] CLASS;
MINCREDIT       : [Mm][Ii][Nn] CREDIT;
MINRES          : [Mm][Ii][Nn][Rr][Ee][Ss];
MINSPREAD       : [Mm][Ii][Nn][Ss][Pp][Rr][Ee][Aa][Dd];
NONCOURSE       : [Nn][Oo][Nn][Cc][Oo][Uu][Rr][Ss][Ee][Ss]?;
OF              : [Oo][Ff];
PSEUDO          : [Pp][Ss][Ee][Uu][Dd][Oo];
REMARK          : [Rr][Ee][Mm][Aa][Rr][Kk];
RULE_COMPLETE   : [Rr][Uu][Ll][Ee]'-'?[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee];
RULE_INCOMPLETE : [Rr][Uu][Ll][Ee]'-'?[Ii][Nn][Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee];
RULE_TAG        : [Rr][Uu][Ll][Ee]'-'?[Tt][Aa][Gg];
SHARE           : [Ss][Hh][Aa][Rr][Ee]([Ww][Ii][Tt][Hh])?
                | [Nn][Oo][Nn][Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee];
TAG             : [Tt][Aa][Gg];
SAME_DISC       : [Ss][Aa][Mm][Ee][Dd][Ii][Ss][Cc];
UNDER           : [Uu][Nn][Dd][Ee][Rr];
WITH            : [Ww][Ii][Tt][Hh];

// If-Else keywords
BEGINELSE       : BEGIN ELSE;
BEGINIF         : BEGIN IF;
ELSE            : [Ee][Ll][Ss][Ee];
ENDELSE         : [Ee][Nn][Dd]ELSE;
ENDIF           : [Ee][Nn][Dd] IF;
IF              : [Ii][Ff];
IS              : ([Ii][Ss])|([Ww][Aa][Ss]);
ISNT            : ([Ii][Ss][Nn][Tt])|([Ww][Aa][Ss][Nn][Tt]);
THEN            : [Tt][Hh][Ee][Nn];

// List separator aliases
AND         : [Aa][Nn][Dd];
OR          : [Oo][Rr];

// Scribe "tokens"
NUMBER          : DIGIT+ (DOT DIGIT*)?;
RANGE           : NUMBER ':' NUMBER;
CATALOG_NUMBER  : DIGIT+ LETTER+;
WILD            : (SYMBOL)* AT (SYMBOL)*;
SYMBOL          : (LETTER | DIGIT | DOT | HYPHEN | UNDERSCORE | AMPERSAND)+;
STRING      : '"' .*? '"';

//  Character and operator names
//  -----------------------------------------------------------------------------------------------
AMPERSAND   : '&';
AT          : '@';
COMMA       : ',';
EQ          : '=';
GE          : '>=';
GT          : '>';
HYPHEN      : '-';
LE          : '<=';
LP          : '(';
LT          : '<';
NE          : '<>';
PLUS        : '+';
RP          : ')';
SEMICOLON   : ';';
UNDERSCORE  : '_';

//  Fragments
//  -----------------------------------------------------------------------------------------------
/*  By prefixing the rule with fragment, we let ANTLR know that the rule will be used only by other
 *  lexical rules. It is not a token in and of itself.
 */
fragment DOT         : '.';
fragment DIGIT       : [0-9];
fragment LETTER      : [a-zA-Z];

