grammar BLOCK;

/*
 * Parser Rules
 */

block       : .*? BEGIN headers ';' rules ENDDOT .*? EOF ;
headers     : (STRING | keyword | course_list | symbol)+ ;
rules       : (STRING | keyword | course_list | symbol)+ ;

keyword     : CREDITS | CLASSES | MINRES | PROXYADVICE | EXCLUSIVE ;
course_list : COURSE (OR (COURSE | COURSE_NUM))*
            | COURSE (AND (COURSE | COURSE_NUM))*
            ;
symbol      : (LETTER | DIGIT | '_')+ ;


/*
 * Lexer Rules
 */

BEGIN       : [Bb][Ee][Gg][Ii][Nn] ;
ENDDOT      : [Ee][Nn][Dd]DOT ;
STRING      : '"' .*? '"' ;

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

INFROM      : (([Ii][Nn])|([Ff][Rr][Oo][Mm])) ->skip ;
HIDE        : '{' [Hh][Ii][Dd][Ee] .*? '}' -> skip ;
DECIDE      : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip ;
COMMENT     : '#' .*? '\n' -> skip ;
LOG         : [Ll][Oo][Gg] .*? '\n' -> skip ;
WHITESPACE  : [ \t\n\r]+ -> skip ;
