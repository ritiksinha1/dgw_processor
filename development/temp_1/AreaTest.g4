grammar AreaTest;

area_test   : .*? BEGIN head (SEMICOLON body)? ENDOT .*? EOF;
head        :
            (
              label
            )*
            ;
body        :
            (
              class_credit
            )*
            ;

course_list     : course_item (and_list | or_list)? course_qualifier* label?;
full_course     : discipline catalog_number course_qualifier*;
course_item     : discipline? catalog_number course_qualifier*;
and_list        : (list_and course_item )+;
or_list         : (list_or course_item)+;
discipline      : SYMBOL | WILD | BLOCK | IS; // Include keywords that appear as discipline names
catalog_number  : SYMBOL | NUMBER | CATALOG_NUMBER | RANGE | WILD;
course_qualifier: with_clause
                | except_clause
                | including_clause
                | maxpassfail
                | maxperdisc
                | maxspread
                | maxtransfer
                | mincredit
                | mingpa
                | mingrade
                | minspread
                | ruletag
                | samedisc
                | share
                | with_clause
                ;

allow_clause    : LP ALLOW (NUMBER|RANGE) RP;
area_list       : area_element+ minarea;
area_element    : SQLB course_list ','? SQRB;
class_credit    : (NUMBER | RANGE) (CLASS | CREDIT)
                  allow_clause?
                  (logical_op NUMBER (CLASS | CREDIT) ruletag? allow_clause?)?
                  (area_list | course_list | expression | PSEUDO | share | tag)* label?;
except_clause   : EXCEPT course_list;
including_clause: INCLUDING course_list;
label           : LABEL label_tag STRING SEMICOLON? label*;
label_tag       : ~'"'*?;

lastres         : LASTRES NUMBER (OF NUMBER )? (CLASS | CREDIT) course_list? tag?;

maxclass        : MAXCLASS NUMBER course_list? tag?;
maxcredit       : MAXCREDIT NUMBER course_list? tag?;

maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT) course_list? tag?;
maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP tag?;
maxspread       : MAXSPREAD NUMBER tag?;
maxterm         : MAXTERM NUMBER (CLASS | CREDIT) course_list tag?;
maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)? tag?;

minarea         : MINAREA NUMBER tag?;
minclass        : MINCLASS (NUMBER|RANGE) course_list tag?;
mincredit       : MINCREDIT (NUMBER|RANGE) course_list tag?;
mingpa          : MINGPA NUMBER (course_list | expression)? tag? label?;
mingrade        : MINGRADE NUMBER;
minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP tag?;
minres          : MINRES NUMBER (CLASS | CREDIT) label? tag?;
minspread       : MINSPREAD NUMBER tag?;

noncourse       : NUMBER NONCOURSE expression course_qualifier? label?;
optional        : OPTIONAL;
remark          : REMARK STRING SEMICOLON? remark*;
rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) label?;
ruletag         : RULE_TAG expression;
samedisc        : SAME_DISC expression tag?;
share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression? tag?;
standalone      : STANDALONE;
tag             : TAG (EQ (NUMBER|SYMBOL|CATALOG_NUMBER))?;
under           : UNDER NUMBER (CLASS | CREDIT)  full_course or_list? label;
with_clause     : LP WITH expression RP;

expression      : expression relational_op expression
                | expression logical_op expression
                | expression ',' expression
                | full_course
                | discipline
                | NUMBER
                | SYMBOL
                | STRING
                | CATALOG_NUMBER
                | LP expression RP
                ;

// Operators and Separators
logical_op    : (AND | OR);
relational_op : (EQ | GE | GT | IS | ISNT | LE | LT | NE);
list_or       : (COMMA | OR);
list_and      : (PLUS | AND);

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

NONCOURSE       : [Nn][Oo][Nn][Cc][Oo][Uu][Rr][Ss][Ee][Ss]?;
OPTIONAL        : [Oo][Pp][Tt][Ii][Oo][Nn][Aa][Ll];
OF              : [Oo][Ff];
PSEUDO          : [Pp][Ss][Ee][Uu][Dd][Oo];
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
ISNT            : ([Ii][Ss][Nn][Tt])|([Ww][Aa][Ss][Nn][Tt]);
THEN            : [Tt][Hh][Ee][Nn];


COMMENT         : '#' .*? '\n' -> skip;
FROM            : [Ff][Rr][Oo][Mm] -> skip;
IN              : [Ii][Nn] -> skip;
WHITESPACE      : [ \t\n\r]+ -> skip;

// List separator aliases
AND         : [Aa][Nn][Dd];
OR          : [Oo][Rr];

// Scribe atoms
NUMBER          : DIGIT+ (DOT DIGIT*)?;
RANGE           : NUMBER ' '* ':' ' '* NUMBER;
CATALOG_NUMBER  : DIGIT+ LETTER+;
WILD            : (SYMBOL)* AT (SYMBOL)*;
SYMBOL          : (LETTER | DIGIT | DOT | HYPHEN | SOLIDUS | UNDERSCORE | AMPERSAND)+;
STRING      : '"' .*? '"';

//  Character and operator names
//  -----------------------------------------------------------------------------------------------
AMPERSAND   : '&';
AT          : '@'+;
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
SOLIDUS     : '/';
SQLB        : '[';
SQRB        : ']';
UNDERSCORE  : '_';

//  Fragments
//  -----------------------------------------------------------------------------------------------
/*  By prefixing the rule with fragment, we let ANTLR know that the rule will be used only by other
 *  lexical rules. It is not a token in and of itself.
 */
fragment DOT         : '.';
fragment DIGIT       : [0-9];
fragment LETTER      : [a-zA-Z];
