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
req_block   : .*? BEGIN head (SEMICOLON body)? ENDOT .*? EOF;
head        :
            ( class_credit_head
            | if_then_head
            | lastres
            | maxclass
            | maxcredit
            | maxpassfail
            | maxperdisc
            | maxterm
            | maxtransfer
            | mingrade
            | minclass
            | mincredit
            | mingpa
            | minperdisc
            | minres
            | optional
            | remark
            | share
            | standalone
            | subset
            | under
            )*
            ;
body        :
            ( block
            | blocktype
            | class_credit_body
            | copy_rules
            | group
            | if_then_body
            | label
            | noncourse
            | remark
            | rule_complete
            | subset
            )*
            ;

/*  When Major is used in ShareWith it refers to the Major block in the audit. When used in an If-
 *  statement it refers to the major on the student’s curriculum.
 */

// Course Lists
// ------------------------------------------------------------------------------------------------
/* Differentiate between lists in the head versus lists in the body because some course list
 * qualifiers can be standalone rules in the Head.
 *
 * Course lists can be divided into “areas” using square brackets, for use with the MinArea
 * qualifier. But (a) just because a list is divided into areas doesn’t mean there has to be a
 * MinArea qualifier present, and (b) the Ellucian parser doesn't check whether the square brackets
 * are balanced; it’s okay to have stray brackets floating around, which are ignored, presumably
 * unless there is a MinArea check done during audit time.
 *
 * The trick is to determine where each type of bracket might appear or not, and that will have to
 * be done in dgw_processor.
 */
course_list               : L_SQB?
                              course_item R_SQB? (and_list | or_list)?
                            R_SQB?
                            (except_list | include_list)? label?;

// The following list was intended to differentiate course list qualifiers from separate statements
// in the head, where these qualifiers can be used in course lists in the body. But it looks like
// they are not needed: course lists in the head seem never to be qualified. There remains a bit of
// confusion here on my part. 2020-10-05
course_list_head_qualifier : maxspread
                           | mingpa
                           | mingrade
                           | minspread
                           | header_tag
                           | samedisc
                           | share
                           ;

course_list_body           : course_list (course_list_body_qualifier tag?)* label? ;
course_list_body_qualifier : maxpassfail
                           | maxperdisc
                           | maxspread
                           | maxtransfer
                           | minarea
                           | minclass
                           | mincredit
                           | mingpa
                           | mingrade
                           | minperdisc
                           | minspread
                           | rule_tag
                           | samedisc
                           | share
                           ;

full_course           : discipline catalog_number with_clause*;
course_item           : L_SQB? discipline? catalog_number with_clause* R_SQB?;
and_list              : (list_and R_SQB? course_item)+;
or_list               : (list_or R_SQB? course_item)+;
catalog_number        : symbol | NUMBER | CATALOG_NUMBER | WILD;
discipline            : symbol
                      | string // For "SPEC." at BKL
                      | WILD
                      // Include keywords that appear as discipline names
                      | BLOCK
                      | IS;

//  if-then
//  -----------------------------------------------------------------------------------------------
begin_if        : BEGINIF | BEGINELSE;
end_if          : ENDIF | ENDELSE;

if_then_head    : IF expression THEN (head_rule | head_rule_group) label? else_head?;
else_head       : ELSE (head_rule | head_rule_group) label?;
head_rule_group : (begin_if head_rule+ end_if);
head_rule       : if_then_body
                | block
                | blocktype
                | class_credit_head
                | copy_rules
                | lastres
                | maxcredit
                | maxpassfail
                | maxterm
                | maxtransfer
                | minclass
                | mincredit
                | mingpa
                | mingrade
                | minperdisc
                | minres
                | minterm
                | noncourse
                | remark
                | rule_complete
                | share
                | subset
                ;


if_then_body    : IF expression THEN (body_rule | body_rule_group) requirement* label? else_body?;
else_body       : ELSE (body_rule | body_rule_group) requirement* label?;
body_rule_group : (begin_if body_rule+ end_if);


body_rule       : if_then_body
                | block
                | blocktype
                | class_credit_body
                | copy_rules
                | group
                | lastres
                | maxcredit
                | maxtransfer
                | minclass
                | mincredit
                | mingrade
                | minres
                | noncourse
                | remark
                | rule_complete
                | share
                | subset
                ;

requirement       : maxpassfail
                  | maxperdisc
                  | maxtransfer
                  | minclass
                  | mincredit
                  | mingpa
                  | mingrade
                  | minperdisc
                  | samedisc
                  | rule_tag
                  | share
                  ;

//  Groups
//  -----------------------------------------------------------------------------------------------
/*  Body Only
 */
group           : NUMBER GROUP group_list
                  requirement*
                  label?
                ;
group_list      : group_item (logical_op group_item)*; // But only OR should occur
group_item      : LP
                  (block
                   | blocktype
                   | course_list
                   | class_credit_body
                   | group
                   | noncourse
                   | rule_complete)
                  requirement*
                  label?
                  RP
                  requirement*
                  label?
                ;

//  Rule Subset
//  -----------------------------------------------------------------------------------------------
/*  Body Only
 */
subset            : BEGINSUB
                  ( if_then_body
                    | block
                    | blocktype
                    | class_credit_body
                    | copy_rules
                    | course_list
                    | group
                    | noncourse
                    | rule_complete
                  )+
                  ENDSUB subset_qualifier* label?;

/*  Allowable rule (subset) qualifiers:
 *  DontShare, HighPriority, LowPriority, LowestPriority, MaxPerDisc, MaxPassFail, MaxTransfer,
 *  MaxSpread, MinGrade, MinPerDisc, MinSpread, ShareWith, NotGPA, ProxyAdvice, SameDisc
 */
subset_qualifier  : maxpassfail
                  | maxperdisc
                  | maxspread
                  | maxtransfer
                  | mingpa
                  | mingrade
                  | minperdisc
                  | minspread
                  | rule_tag
                  | share
                  ;

// Blocks
// ------------------------------------------------------------------------------------------------
block           : NUMBER BLOCK expression rule_tag? label;
blocktype       : NUMBER BLOCKTYPE expression label;

/* Other Rules and Rule Components
 * ------------------------------------------------------------------------------------------------
 */
allow_clause        : LP allow NUMBER RP;

class_credit_head   : (num_classes | num_credits)
                      (logical_op (num_classes | num_credits))?
                      (IS? pseudo | header_tag | tag)*
                      display* label?;

class_credit_body   : (num_classes | num_credits)
                      (logical_op (num_classes | num_credits))? course_list_body
                      (IS? pseudo | share | rule_tag | tag)*
                      display* label?;

allow           : (ALLOW | ACCEPT);
class_or_credit : (CLASS | CREDIT);
copy_rules      : COPY_RULES expression SEMICOLON?;
// Display can be used on the following block header qualifiers: MinGPA, MinRes, LastRes,
// MinCredits, MinClasses, MinPerDisc, MinTerm, Under, Credits/Classes.
display         : DISPLAY string SEMICOLON?;
except_list     : EXCEPT course_list;
header_tag      : HEADER_TAG nv_pair;
include_list    : INCLUDING course_list;
label           : LABEL string SEMICOLON?;
lastres         : LASTRES NUMBER (OF NUMBER)? class_or_credit course_list? tag? display* label?;

maxclass        : MAXCLASS NUMBER course_list? tag?;
maxcredit       : MAXCREDIT NUMBER course_list? tag?;

maxpassfail     : MAXPASSFAIL NUMBER class_or_credit tag?;
maxperdisc      : MAXPERDISC NUMBER class_or_credit LP SYMBOL (list_or SYMBOL)* RP tag?;
maxspread       : MAXSPREAD NUMBER tag?;
maxterm         : MAXTERM NUMBER class_or_credit course_list tag?;

maxtransfer     : MAXTRANSFER NUMBER class_or_credit (LP SYMBOL (list_or SYMBOL)* RP)? tag?;

minarea         : MINAREA NUMBER tag?;
minclass        : MINCLASS NUMBER course_list tag? display* label?;
mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
mingpa          : MINGPA NUMBER (course_list | expression)? tag? display* label?;
mingrade        : MINGRADE NUMBER;
minperdisc      : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
minres          : MINRES (num_classes | num_credits) display* label? tag?;
minspread       : MINSPREAD NUMBER tag?;
minterm         : MINTERM NUMBER class_or_credit course_list? tag? display*;

noncourse       : NUMBER NONCOURSE LP expression RP label?;
num_classes     : NUMBER CLASS allow_clause?;
num_credits     : NUMBER CREDIT allow_clause?;
nv_pair         : SYMBOL '=' (STRING | SYMBOL);
optional        : OPTIONAL;
pseudo          : PSEUDO | PSUEDO;
remark          : (REMARK string SEMICOLON?)+;
rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) label?;
rule_tag        : RULE_TAG nv_pair;
samedisc        : SAME_DISC expression tag?;
share           : (SHARE | DONT_SHARE) (NUMBER class_or_credit)? expression? tag?;
//share_item      : SYMBOL (logical_op (SYMBOL | NUMBER | string | WILD))?;
//share_list      : expression;
standalone      : STANDALONE;
string          : STRING;
symbol          : SYMBOL; // | (QUOTE SYMBOL QUOTE);
tag             : TAG (EQ (NUMBER|SYMBOL|CATALOG_NUMBER))?;
under           : UNDER NUMBER class_or_credit course_list display* label?;
with_clause     : LP WITH expression RP;

expression      : expression relational_op expression
                | expression logical_op expression
                | expression ',' expression
                | full_course
                | discipline
                | NUMBER
                | QUESTION_MARK
                | SYMBOL
                | string
                | CATALOG_NUMBER
                | LP NONCOURSE? expression RP
                ;

// Operators and Separators
logical_op    : (AND | OR);
relational_op : (EQ | GE | GT | IS | ISNT | LE | LT | NE);
list_or       : (COMMA | OR);
list_and      : (PLUS | AND);

// Lexer
// ================================================================================================

STRING          : '"' ~'"'* '"';

//  Skips
//  -----------------------------------------------------------------------------------------------
// Comments and auditor directives, not requirements.
CHECKELECTIVES  : [Cc][Hh][Ee][Cc][Kk]
                  [Ee][Ll][Ee][Cc][Tt][Ii][Vv][Ee]
                  [Cc][Rr][Ee][Dd][Ii][Tt][Ss]
                  [Aa][Ll][Ll][Oo][Ww][Ee][Dd] -> skip;
COMMENT         : HASH .*? '\n' -> skip;
CURLY_BRACES    : [}{] -> skip;
DECIDE          : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip;
DISPLAY         : [Dd][Ii][Ss][Pp][Ll][Aa][Yy];
FROM            : [Ff][Rr][Oo][Mm] -> skip;
FROM_ADVICE     : '-'?[Ff][Rr][Oo][Mm]'-'?[Aa][Dd][Vv][Ii][Cc][Ee] -> skip;
// Preprocessor (dgw_filter.py) Now strips these
// HIDE            : ([Hh][Ii][Dd][Ee])?
//                  ('-'?[Ff][Rr][Oo][Mm]'-'?[Aa][Dd][Vv][Ii][Cc][Ee])? -> skip;
HIDE_RULE       : [Hh][Ii][Dd][Ee] '-'? [Rr][Uu][Ll][Ee] -> skip;
HIGH_PRIORITY   : [Hh][Ii][Gg][Hh]([Ee][Ss][Tt])? [ -]? [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip;
IN              : [Ii][Nn] -> skip;
LOW_PRIORITY    : [Ll][Oo][Ww]([Ee][Ss][Tt])? [ -]? [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip;
NOTGPA          : [Nn][Oo][Tt][Gg][Pp][Aa] -> skip;
PROXYADVICE     : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] .*? '\n' -> skip;

// Before BEGIN and after ENDOT, the lexer does token recognition.
// To avoid errors from text that can't be tokenized, skip Log lines and otherwise-illegal chars.
// Preprocessor (dgw_filter.py) Now strips these
// LOGS            : [Ll][Oo][Gg] .*? '\n' -> skip;
// CRUFT           : [:/'*\\]+ -> skip;

WHITESPACE      : [ \t\n\r']+ -> skip;

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
ACCEPT          : [Aa[Cc][Cc][Ee][Pp][Tt];
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
HEADER_TAG      : [Hh][Ee][Aa][Dd][Ee][Rr]'-'?[Tt][Aa][Gg];
INCLUDING       : [Ii][Nn][Cc][Ll][Uu][Dd][Ii][Nn][Gg];
LABEL           : [Ll][Aa][Bb][Ee][Ll]~'"'*;
LASTRES         : [Ll][Aa][Ss][Tt][Rr][Ee][Ss];

MAXCLASS        : [Mm][Aa][Xx] CLASS;
MAXCREDIT       : ([Ss][Pp])?[Mm][Aa][Xx] CREDIT;
MAXPASSFAIL     : [Mm][Aa][Xx][Pp][Aa][Ss][Ss][Ff][Aa][Ii][Ll];
MAXPERDISC      : [Mm][Aa][Xx][Pp][Ee][Rr][Dd][Ii][Ss][Cc];
MAXSPREAD       : [Mm][Aa][Xx][Ss][Pp][Rr][Ee][Aa][Dd];
MAXTERM         : ([Ss][Pp])?[Mm][Aa][Xx][Tt][Ee][Rr][Mm];
MAXTRANSFER     : [Mm][Aa][Xx][Tt][Rr][Aa][Nn][Ss][Ff][Ee][Rr];

MINAREA         : [Mm][Ii][Nn][Aa][Rr][Ee][Aa][Ss]?;
MINGPA          : [Mm][Ii][Nn][Gg][Pp][Aa];
MINGRADE        : [Mm][Ii][Nn][Gg][Rr][Aa][Dd][Ee];
MINCLASS        : [Mm][Ii][Nn] CLASS;
MINCREDIT       : [Mm][Ii][Nn] CREDIT;
MINPERDISC      : [Mm][Ii][Nn][Pp][Ee][Rr][Dd][Ii][Ss][Cc];
MINRES          : [Mm][Ii][Nn][Rr][Ee][Ss];
MINSPREAD       : [Mm][Ii][Nn][Ss][Pp][Rr][Ee][Aa][Dd];
MINTERM         : [Mm][Ii][Nn][Tt][Ee][Rr][Mm];

NONCOURSE       : [Nn][Oo][Nn][Cc][Oo][Uu][Rr][Ss][Ee][Ss]?;
OPTIONAL        : [Oo][Pp][Tt][Ii][Oo][Nn][Aa][Ll];
OF              : [Oo][Ff];
PSEUDO          : [Pp][Ss][Ee][Uu][Dd][Oo];
PSUEDO          : [Pp][Ss][Uu][Ee][Dd][Oo]; // Scribe allows it, so we do too
REMARK          : [Rr][Ee][Mm][Aa][Rr][Kk];
RULE_COMPLETE   : [Rr][Uu][Ll][Ee]'-'?[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee];
RULE_INCOMPLETE : [Rr][Uu][Ll][Ee]'-'?[Ii][Nn][Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee];
RULE_TAG        : [Rr][Uu][Ll][Ee]'-'?[Tt][Aa][Gg];
STANDALONE      : [Ss][Tt][Aa][Nn][Dd][Aa][Ll][Oo][Nn][Ee]([Bb][Ll][Oo][Cc][Kk])?;
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
ISNT            : ([Ii][Ss][Nn][Oo]?[Tt])|([Ww][Aa][Ss][Nn][Oo]?[Tt]);
THEN            : [Tt][Hh][Ee][Nn];

// List separator aliases
AND         : [Aa][Nn][Dd];
OR          : [Oo][Rr];

// Scribe "tokens"
//NUMBER          : DIGIT+ (DOT DIGIT*)?;
NUMBER          : DIGIT+ (DOT DIGIT*)? ' '* ([:\-] ' '* DIGIT+ (DOT DIGIT*)?)?;
CATALOG_NUMBER  : DIGIT+ LETTER+;
WILD            : (SYMBOL)* AT (SYMBOL)*;
SYMBOL          : (LETTER | DIGIT | DOT | HYPHEN | UNDERSCORE | AMPERSAND | '/')+;

//  Character and operator names
//  -----------------------------------------------------------------------------------------------
AMPERSAND     : '&';
ASTERISK      : '*';
AT            : '@'+;
BANG          : '!';
BACKQUOTE     : '`';
BACKSLASH     : '\\';
COLON         : ':';
COMMA         : ',';
DBL_QUOTE     : '"';
EQ            : '=';
GE            : '>=';
GT            : '>';
HASH          : '#';
HYPHEN        : '-';
LE            : '<=';
LT            : '<';
LP            : '(';
L_SQB         : '[';
NE            : '<>';
PERCENT       : '%';
PLUS          : '+';
// QUOTE         : '\'' ;
QUESTION_MARK : '?';
RP            : ')';
R_SQB         : ']';
SEMICOLON     : ';';
SLASH         : '/';
UNDERSCORE    : '_';

//  Fragments
//  -----------------------------------------------------------------------------------------------
/*  By prefixing the rule with fragment, we let ANTLR know that the rule will be used only by other
 *  lexical rules. It is not a token in and of itself.
 */
fragment DOT         : '.';
fragment DIGIT       : [0-9];
fragment LETTER      : [a-zA-Z];

