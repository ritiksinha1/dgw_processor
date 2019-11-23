grammar BLOCK;

/*
 * Parser Rules
 */

block       : .*? BEGIN headers ';' rules ENDDOT .*? EOF ;
headers     : mingpa
            | minres
            | (STRING | LABEL | REMARK | keyword | SYMBOL)+ ;
rules       : (STRING | LABEL | REMARK | keyword | SYMBOL)+ ;

mingpa      : MINGPA NUMBER ;
minres      : MINRES NUMBER ;
numclasses  : NUMBER CLASSES INFROM? COURSE_LIST;
numcredits  : NUMBER CREDITS INFROM? COURSE_LIST;

keyword     : CREDITS | CLASSES | MINRES | PROXYADVICE | EXCLUSIVE ;


/*
 * Lexer Rules
 */

BEGIN       : [Bb][Ee][Gg][Ii][Nn] ;
ENDDOT      : [Ee][Nn][Dd]DOT ;
STRING      : '"' .*? '"' ;

INFROM      : ([Ii][Nn])|([Ff][Rr][Oo][Mm]) ;

LABEL       : [Ll][Aa][Bb][Ee][Ll] SYMBOL? STRING ';'? LABEL* ;
REMARK      : [Rr][Ee][Mm][Aa][Rr][Kk] STRING ';'? REMARK* ;

COURSE      : ('@' | DISCIPLINE) ' '* COURSE_NUM ;
CREDITS     : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]?
            | [Mm] [Ii] [Nn] CREDITS
            | [Mm] [Aa] [Xx] CREDITS
            ;
CLASSES     : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])?
            | [Mm] [Ii] [Nn] CLASSES
            | [Mm] [Aa] [Xx] CLASSES
            ;
MINRES      : [Mm][Ii][Nn][Rr][Ee][Ss] ;
MINGPA      : [Mm][Ii][Nn][Gg][Pp][Aa] ;
PROXYADVICE : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] ;
EXCLUSIVE   : [Ee] [Xx] [Cc] [Ll] [Uu] [Ss] [Ii] [Vv] [Ee]
            | [Nn] [Oo] [Nn] '-'? EXCLUSIVE
            ;

/* DWResident, DW... etc. are DWIDs */
/* (Decide=DWID) is a phrase used for tie-breaking by the auditor.*/

DISCIPLINE  : LETTER+ '@'? ;
COURSE_NUM  : ('@'? NUMBER LETTER+? | NUMBER | NUMBER '@')
              (':' ('@'? NUMBER LETTER+? | NUMBER | NUMBER '@'))?
            ;

NUMBER      : DIGIT+ '.'? DIGIT* ;
RANGE       : NUMBER ':' NUMBER ;
SYMBOL      : (LETTER | DIGIT | '_')+ ;

COURSE_LIST : COURSE (OR (COURSE | COURSE_NUM))*
            | COURSE (AND (COURSE | COURSE_NUM))*
            ;

LB          : '{' ;
RB          : '}' ;
LP          : '(' ;
RP          : ')' ;
SEMI        : ';' ;
COLON       : ':' ;
DOT         : '.' ;
EQ          : '=' ;
NE          : '<>' ;
GT          : '>' ;
LT          : '<' ;
LE          : '<=' ;
GE          : '>=' ;

OR          : ',' | [Oo][Rr] ;
AND         : '+' | [Aa][Nn][Dd] ;

DIGIT    : [0-9] ;
LETTER   : [a-zA-Z] ;

HIDE        : '{' [Hh][Ii][Dd][Ee] .*? '}' -> skip ;
DECIDE      : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip ;
COMMENT     : '#' .*? '\n' -> skip ;
LOG         : [Ll][Oo][Gg] .*? '\n' -> skip ;
WHITESPACE  : [ \t\n\r]+ -> skip ;
