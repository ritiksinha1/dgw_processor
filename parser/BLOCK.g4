grammar BLOCK;

/*
 *  The words reserved by the python antlr runtime are as follows:
 *
 *  python3Keywords = {
 *     "abs", "all", "any", "apply", "as",
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
 *  All these raise an error. If they don’t, it’s a bug. Indeed assert is missing and should be added.
 *
 */

/*
 * Parser Rules
 */

req_text    : .*? req_block .*? EOF ;
req_block   : BEGIN headers ';' rules ENDDOT ;
headers     : mingpa
            | minres
            | numclasses
            | numcredits
            | (LABEL | REMARK )+ ;
rules       : .*? ;

and_courses : INFROM? WILDSYMBOL WILDNUMBER (AND (SYMBOL NUMBER) | NUMBER)* ;
or_courses  : INFROM? WILDSYMBOL WILDNUMBER (OR  (SYMBOL NUMBER) | NUMBER)* ;
mingpa      : MINGPA NUMBER ;
minres      : MINRES NUMBER ;
numclasses  : NUMBER CLASSES (and_courses | or_courses) ;
numcredits  : NUMBER CREDITS (and_courses | or_courses)? ;

keyword     : CREDITS | CLASSES | MINRES | PROXYADVICE | EXCLUSIVE ;


/*
 * Lexer Rules
 */

BEGIN       : [Bb][Ee][Gg][Ii][Nn] ;
ENDDOT      : [Ee][Nn][Dd]DOT ;
STRING      : '"' .*? '"' ;


LABEL       : [Ll][Aa][Bb][Ee][Ll] SYMBOL? STRING ';'? LABEL* ;
REMARK      : [Rr][Ee][Mm][Aa][Rr][Kk] STRING ';'? REMARK* ;

CREDITS     : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]? ;
MINCREDITS  : [Mm] [Ii] [Nn] CREDITS ;
MAXCREDITS  : [Mm] [Aa] [Xx] CREDITS ;


CLASSES     : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])? ;
MINCLASSES  : [Mm] [Ii] [Nn] CLASSES ;
MAXCLASSES  : [Mm] [Aa] [Xx] CLASSES ;


MINRES      : [Mm][Ii][Nn][Rr][Ee][Ss] ;
MINGPA      : [Mm][Ii][Nn][Gg][Pp][Aa] ;
PROXYADVICE : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] ;
EXCLUSIVE   : [Ee] [Xx] [Cc] [Ll] [Uu] [Ss] [Ii] [Vv] [Ee]
            | [Nn] [Oo] [Nn] '-'? EXCLUSIVE
            ;

/* DWResident, DW... etc. are DWIDs */
/* (Decide=DWID) is a phrase used for tie-breaking by the auditor.*/


OR          : ',' | [Oo][Rr] ;
AND         : '+' | [Aa][Nn][Dd] ;

INFROM      : ([Ii][Nn])|([Ff][Rr][Oo][Mm]) ;
WILDNUMBER  : (DIGIT | WILDCARD)+ ;
WILDSYMBOL  : (LETTER | DIGIT | WILDCARD)+ ;
WILDCARD    : '@' ;
SYMBOL      : (LETTER | DIGIT | '_')+ ;
RANGE       : NUMBER ':' NUMBER ;
NUMBER      : DIGIT+ DOT? DIGIT* ;
fragment
DOT         : '.' ;
fragment
DIGIT       : [0-9] ;
fragment
LETTER      : [a-zA-Z] ;

HIDE        : '{' [Hh][Ii][Dd][Ee] .*? '}' -> skip ;
DECIDE      : '(' [Dd] [Ee] [Cc] [Ii] [Dd] [Ee] .+? ')' -> skip ;
COMMENT     : '#' .*? '\n' -> skip ;
LOG         : [Ll][Oo][Gg] .*? '\n' -> skip ;
WHITESPACE  : [ \t\n\r]+ -> skip ;
