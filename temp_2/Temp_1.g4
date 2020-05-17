grammar Temp_1;

skip_test: (course | discipline | catalog_number | symbol | number)*? EOF;

course: discipline catalog_number;
discipline: SYMBOL | WILD_SYMBOL;
catalog_number: CATALOG_NUMBER | WILD_NUMBER;
symbol: SYMBOL;
number: NUMBER;

BEGIN           : [Bb][Ee][Gg][Ii][Nn] ;
BEGINSUB        : BEGIN [Ss][Uu][Bb] ;
BLOCK           : [Bb][Ll][Oo][Cc][Kk] ;
BLOCKTYPE       : BLOCK [Tt][Yy][Pp][Ee][Ss]? ;
CLASS           : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])? ;
CREDIT          : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]? ;
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

//  Skips
//  -----------------------------------------------------------------------------------------------
// Comments and auditor directives, not requirements.
// Defined here so they won't match Symbols.
CHECKELECTIVES : [Cc][Hh][Ee][Cc][Kk]
                 [Ee][Ll][Ee][Cc][Tt][Ii][Vv][Ee]
                 [Cc][Rr][Ee][Dd][Ii][Tt][Ss]
                 [Aa][Ll][Ll][Oo][Ww][Ee][Dd] -> skip ;
COMMENT        : '#' .*? '\n' -> skip ;
DECIDE         : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip ;
HIDE           : [Hh][Ii][Dd][Ee]
                 ([\-]?[Ff][Rr][Oo][Mm][\-]?[Aa][Dd][Vv][Ii][Cc][Ee])? -> skip;
HIDE_RULE      : [Hh][Ii][Dd][Ee][\-]?[Rr][Uu][Ll][Ee] -> skip ;
NOTGPA         : [Nn][Oo][Tt][Gg][Pp][Aa] -> skip ;
LOW_PRIORITY   : [Ll][Oo][Ww]([Ee][Ss][Tt])? '-' [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip ;
HIGH_PRIORITY  : [Hh][Ii][Gg][Hh]([Ee][Ss][Tt])? '-' [Pp][Rr][Ii]([Oo][Rr][Ii][Tt][Yy])? -> skip ;
PROXYADVICE    : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] .*? '\n' -> skip;
// Including '/' as whitespace is a hack to reduce token recognition errors: I can't figure out how
// to ignore text following ENDDOT.
WHITESPACE  : [ \t\n\r/}{]+ -> skip ;

// Things outside the BEGIN...ENDDOT that cause unnecessary grief
LOG            : [Ll][Oo][Gg] .*? '\n' -> skip ;

NUMBER          : DIGIT+ (DOT DIGIT*)? ;
RANGE           : NUMBER ':' NUMBER ;

CATALOG_NUMBER  : DIGIT+ LETTER+ ;
WILD_SYMBOL     : LETTER* AT (LETTER|DIGIT)* ;
WILD_NUMBER     : NUMBER* AT NUMBER* ;

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

