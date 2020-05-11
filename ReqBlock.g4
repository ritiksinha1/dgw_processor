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
            ( if_then
            | class_credit
            | lastres
            | maxclass
            | maxcredit
            | maxpassfail
            | maxtransfer
            | mingrade
            | minclass
            | mincredit
            | mingpa
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
and_list        : (LIST_AND course_item )+;
or_list         : (LIST_OR course_item)+;
discipline      : SYMBOL | WILD;
catalog_number  : SYMBOL | NUMBER | CATALOG_NUMBER | RANGE | WILD;
course_qualifier: with_clause
                | except_clause
                | including_clause
                | maxperdisc
                | minarea
                | mingpa
                | mingrade
                | minspread
                | share
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
             | noncourse
             | remark
             | rule_complete
             | subset
             ;
begin_if     : BEGINIF | BEGINELSE;
end_if       : ENDIF | ENDELSE;


//  Groups
//  -----------------------------------------------------------------------------------------------
/*
  Notes
  1. Group must be followed by a list of one or more rules. The list of rules following the Group
     keyword is referred to as the group list. Each rule in the group list is a group item. Each
     group item is enclosed in parentheses and does not end with a semicolon.

  2. Each rule in the Group list is one of the following types of rules: Course, Block, BlockType,
     Group, RuleComplete, RuleIncomplete or NonCourse. A group item cannot be an If rule or a subset
     rule.

  3. Each rule in the list is connected to the next rule by “or”.

  4. A Group statement can be nested within another Group statement. There is no limit to the number
     of times you can embed a Group within a Group. However, the worksheet display of a requirement
     with many depths may be difficult to understand.

  5. Qualifiers that must be applied to all rules in the group list must occur after the last right
     parenthesis and before the label at the end of the Group statement. Qualifiers that apply only
     to a specific rule in the group list must appear inside the parentheses for that group item
     rule.

  6. Allowable rule qualifiers: DontShare, Hide, HideRule, HighPriority, LowPriority,
     LowestPriority, MaxPassFail, MaxPerDisc, MaxTransfer, MinGrade, MinPerDisc, NotGPA,
     ProxyAdvice, SameDisc, ShareWith, MinClass, MinCredit, RuleTag.

  7. Do not mix course rules with Block rules in a group. Although this will parse, the auditor may
     not handle this as expected. Putting Block rules into Groups is not a best practice.
 */
group           : NUMBER GROUP group_list
                  group_qualifier*
                  label?
                ;
group_list      : group_item (OP group_item)*; // Not clear why this has to be OP rather than OR.
group_item      : LP
                    (class_credit | group | block | blocktype | rule_complete | noncourse)
                    group_qualifier*
                    label?
                  RP
                  group_qualifier*
                  label?
                ;
group_qualifier : maxpassfail
                | maxtransfer
                | mingrade
                | minperdisc
                | samedisc
                | share
                | minclass
                | mincredit
                | ruletag
                ;

//  Rule Subset
//  -----------------------------------------------------------------------------------------------
subset            : BEGINSUB (class_credit | copy_rules | group)+ ENDSUB subset_qualifier* label;
subset_qualifier  : mingpa | mingrade | maxtransfer | minperdisc | maxperdisc;

// Blocks
// ------------------------------------------------------------------------------------------------
block           : NUMBER BLOCK expression label;
blocktype       : NUMBER BLOCKTYPE expression label;

/* Other Rules and Rule Components
 * ------------------------------------------------------------------------------------------------
 */
allow_clause    : LP ALLOW (NUMBER|RANGE) RP;
class_credit    : (NUMBER | RANGE) (CLASS | CREDIT) allow_clause?
                  (OP NUMBER (CLASS | CREDIT) allow_clause?)?
                  (course_list | expression | PSEUDO | share | TAG)* label?;
copy_rules      : COPY_RULES expression SEMICOLON?;
except_clause   : EXCEPT course_list;
including_clause: INCLUDING course_list;
label           : LABEL (SYMBOL|NUMBER)? STRING SEMICOLON? label*;
// LastRes 15 of 30 Credits in @ (With DWResident=Y or Attribute=SE)
// Except PE @ Tag=LASTRES
lastres         : LASTRES NUMBER (OF NUMBER (CREDIT | CLASS))? course_list? TAG?;

maxclass        : MAXCLASS NUMBER course_list? TAG?;
maxcredit       : MAXCREDIT NUMBER course_list? TAG?;

maxpassfail     : MAXPASSFAIL NUMBER (CREDIT | CLASS) course_list? TAG?;
maxperdisc      : MAXPERDISC NUMBER (CREDIT | CLASS) LP SYMBOL (LIST_OR SYMBOL)* RP TAG?;
maxtransfer     : MAXTRANSFER NUMBER (CREDIT | CLASS) (LP SYMBOL (LIST_OR SYMBOL)* RP)? TAG?;
minarea         : MINAREA NUMBER TAG?;
minclass        : MINCLASS NUMBER course_list TAG?;
mincredit       : MINCREDIT NUMBER course_list TAG?;

mingpa          : MINGPA NUMBER course_list?;
mingrade        : MINGRADE NUMBER;
minperdisc      : MINPERDISC NUMBER (CREDIT | CLASS)  LP SYMBOL (',' SYMBOL)* TAG?;
minres          : MINRES NUMBER (CREDIT | CLASS);
minspread       : MINSPREAD NUMBER TAG?;

noncourse       : NUMBER NONCOURSE LP SYMBOL (',' SYMBOL)* RP label?;
remark          : REMARK STRING SEMICOLON? remark*;
rule_complete   : RULE_COMPLETE | RULE_INCOMPLETE label?;
ruletag         : RULE_TAG SYMBOL EQ (SYMBOL | STRING);
samedisc        : SAME_DISC LP SYMBOL OP SYMBOL (LIST_OR SYMBOL OP SYMBOL)* RP TAG?;
under           : UNDER NUMBER (CREDIT | CLASS)  full_course or_list? label;

with_clause     : LP WITH expression RP;

share           : (SHARE | DONT_SHARE) (NUMBER (CREDIT | CLASS))? LP share_list RP;
share_item      : SYMBOL (OP (SYMBOL | NUMBER | STRING))?;
share_list      : share_item (LIST_OR share_item)*;

expression      : expression OP expression
                | full_course
                | NUMBER
                | SYMBOL
                | STRING
                | CATALOG_NUMBER
                | LP expression RP
                ;

// Lexer
// ================================================================================================

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
                | [Cc][Oo][Uu][Rr][Ss][Ee][Ss?];
COPY_RULES      : [Cc][Oo][Pp][Yy]'-'?[Rr][Uu][Ll][Ee][Ss]?'-'?[Ff][Rr][Oo][Mm];
CREDIT          : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]?;
DONT_SHARE      : [Dd][Oo][Nn][Tt][Ss][Ss][Hh][Aa][Rr][Ee]
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
SHARE           : [Ss][Hh][Aa][Rr][Ee]([Ww][Ii][Tt][Hh])?
                | [Nn][Oo][Nn][Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee];
TAG             : [Tt][Aa][Gg] (EQ SYMBOL)?;
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

// Logical Operators
OP          : (AND | OR | EQ | GE | GT | LE | LT | NE);

// List separators
LIST_OR     : (COMMA | OR);
LIST_AND    : (PLUS | AND);
AND         : [Aa][Nn][Dd];
OR          : [Oo][Rr];

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
HIDE            : [Hh][Ii][Dd][Ee]
                  ([\-]?[Ff][Rr][Oo][Mm][\-]?[Aa][Dd][Vv][Ii][Cc][Ee])? -> skip;
HIDE_RULE       : [Hh][Ii][Dd][Ee] '-'? [Rr][Uu][Ll][Ee] -> skip;
HIGH_PRIORITY   : [Hh][Ii][Gg][Hh]([Ee][Ss][Tt])? '-'? [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip;
FROM            : [Ff][Rr][Oo][Mm] -> skip;
IN              : [Ii][Nn] -> skip;
LOW_PRIORITY    : [Ll][Oo][Ww]([Ee][Ss][Tt])? '-'? [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip;
NOTGPA          : [Nn][Oo][Tt][Gg][Pp][Aa] -> skip;
PROXYADVICE     : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] .*? '\n' -> skip;
RULE_TAG        : [Rr][Uu][Ll][Ee]'-'?[Tt][Aa][Gg] -> skip;

// Before BEGIN and fter ENDOT, the lexer does token recognition.
// To avoid errors from text that can't be tokenized, skip Log lines and otherwise-illegal chars.
LOGS            : [Ll][Oo][Gg] .*? '\n' -> skip;
CRUFT           : [:/'*\\]+ -> skip;

SB              : [[\]] ->skip; // Used for MinAreas; not implemented
WHITESPACE      : [ \t\n\r]+ -> skip;

NUMBER          : DIGIT+ (DOT DIGIT*)?;
RANGE           : NUMBER ':' NUMBER;

CATALOG_NUMBER  : DIGIT+ LETTER+;
WILD            : (LETTER|DIGIT)* AT (LETTER|DIGIT)*;

SYMBOL          : (LETTER | DIGIT | DOT | HYPHEN | UNDERSCORE | AMPERSAND)+;

STRING      : '"' .*? '"';

//  Punctuation and operator tokens
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

