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
            | mingpa
            | minres
            | numclass
            | numcredit
            | proxy_advice
            | remark
            | share
            | under
            )*
            ;
body        :
            ( rule_subset
            | block_type
            | label
            | remark
            | numclass
            | numcredit
            | maxperdisc
            )*
            ;

rule_subset : BEGINSUB (numclass | numcredit label)+ ENDSUB qualifier* label ;
group       : NUMBER GROUP IN group_list qualifier* label ;
group_list  : LP course_list
            | block
            | block_type
            | group
            | RULE_COMPLETE
            | noncourse (OR group_list)* ;

/* Parser
 * ------------------------------------------------------------------------------------------------
 *  UNRESOLVED: The Scribe manual gives an example
 *                # Disallow classes older than 10 years – but allow any ANTH to be older
 *                MaxCredits 0 in @ (With DWAge>10)
 *                Except ANTH @ tag=MAX10
 *              In this case, the first course_list is "@ (WITH DWAge>10)"
 *              This has to be recognized and reported in English, but omit the course lookup step.
 *              I've added the WITH clause below to get past parser errors.
 */
block       : NUMBER BLOCK LP SHARE_LIST RP ;
block_type  : NUMBER BLOCKTYPE SHARE_LIST label ;

course_list     : course (and_list | or_list)? ;
course          : DISCIPLINE (CATALOG_NUMBER | WILDNUMBER | NUMBER | RANGE | WITH) ;
course_item     : DISCIPLINE? (CATALOG_NUMBER | WILDNUMBER | NUMBER | RANGE) ;
and_list        : (AND course_item)+ ;
or_list         : (OR course_item)+ ;

label           : LABEL ALPHANUM*? STRING ';' label* ;
lastres         : LASTRES NUMBER (OF NUMBER CREDIT | CLASS)? ;
maxclass        : MAXCLASS NUMBER INFROM? course_list WITH? (EXCEPT course_list)? TAG? ;
maxcredit       : MAXCREDIT NUMBER INFROM? course_list WITH? (EXCEPT course_list)? TAG? ;
maxpassfail     : MAXPASSFAIL NUMBER (CREDIT | CLASS) TAG? ;
maxperdisc      : MAXPERDISC NUMBER (CREDIT | CLASS) INFROM? LP SYMBOL (',' SYMBOL)* TAG? ;
mingpa          : MINGPA NUMBER ;
mingrade        : MINGRADE NUMBER ;
minres          : MINRES NUMBER (CREDIT | CLASS) ;
numclass        : (NUMBER | RANGE) CLASS INFROM? course_list? TAG? label* ;
numcredit       : (NUMBER | RANGE) CREDIT PSEUDO? INFROM? course_list? TAG? ;
noncourse       : NUMBER NONCOURSE LP SYMBOL (',' SYMBOL)* RP ;
proxy_advice    : PROXYADVICE STRING proxy_advice* ;
remark          : REMARK STRING (SEMI? remark)* ;
qualifier       : mingpa | mingrade ;
share           : SHARE SHARE_LIST ;
under           : UNDER NUMBER (CREDIT | CLASS) INFROM? course or_list? proxy_advice label ;
symbol          : SYMBOL ;

/* Lexer
 * ------------------------------------------------------------------------------------------------
 */

//  Keywords
BEGIN         : [Bb][Ee][Gg][Ii][Nn] ;
BEGINSUB      : BEGIN [Ss][Uu][Bb] ;
BLOCK         : [Bb][Ll][Oo][Cc][Kk] ;
BLOCKTYPE     : BLOCK [Tt][Yy][Pp][Ee][Ss]? ;
CLASS         : [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])? ;
CONC          : [Cc][Oo][Nn][Cc] ;
CREDIT        : [Cc][Rr][Ee][Dd][Ii][Tt][Ss]? ;
DEGREE        : [Dd][Ee][Gg][Rr][Ee][Ee] ;
ENDDOT        : [Ee][Nn][Dd]DOT ;
ENDSUB        : [Ee][Nn][Dd][Ss][Uu][Bb] ;
GROUP         : [Gg][Rr][Oo][Uu][Pp] ;
LABEL         : [Ll][Aa][Bb][Ee][Ll] ;
LASTRES       : [Ll][Aa][Ss][Tt][Rr][Ee][Ss] ;
MAJOR         : [Mm][Aa][Jj][Oo][Rr] ;
MAXCLASS      : [Mm][Aa][Xx] CLASS ;
MAXCREDIT     : [Mm][Aa][Xx] CREDIT ;
MINGPA        : [Mm][Ii][Nn][Gg][Pp][Aa] ;
MINGRADE      : [Mm][Ii][Nn][Gg][Rr][Aa][Dd][Ee] ;
MAXPASSFAIL   : [Mm][Aa][Xx][Pp][Aa][Ss][Ss][Ff][Aa][Ii][Ll] ;
MAXPERDISC    : [Mm][Aa][Xx][Pp][Ee][Rr][Dd][Ii][Ss][Cc] ;
MINOR         : [Mm][Ii][Nn][Oo][Rr] ;
MINCLASS      : [Mm][Ii][Nn] CLASS ;
MINCREDITS    : [Mm][Ii][Nn] CREDIT ;
MINRES        : [Mm][Ii][Nn][Rr][Ee][Ss] ;
NONCOURSE     : [Nn][Oo][Nn][Cc][Oo][Uu][Rr][Ss][Ee][Ss]? ;
OTHER         : [Oo][Tt][Hh][Ee][Rr] ;
PROXYADVICE   : [Pp][Rr][Oo][Xx][Yy][\-]?[Aa][Dd][Vv][Ii][Cc][Ee] ;
PSEUDO        : [Pp][Ss][Ee][Uu][Dd][Oo] ;
REMARK        : [Rr][Ee][Mm][Aa][Rr][Kk] ;
RULE_COMPLETE : [Rr][Uu][Ll][Ee]([Ii][Nn])?[Cc][Oo][Mm][Pp][Ll][Ee][Tt][Ee] ;
SHARE         : ([Nn][Oo][Nn] '-'?)?[Ee][Xx][Cc][Ll][Uu][Ss][Ii][Vv][Ee]
              | [Dd][Oo][Nn][Tt][Ss][Ss][Hh][Aa][Rr][Ee]
              | [Ss][Hh][Aa][Rr][Ee]([Ww][Ii][Tt][Hh])?
              ;
SHARE_LIST    : LP SHARE_ITEM (COMMA SHARE_ITEM)* RP ;
SHARE_ITEM    : DEGREE | CONC | MAJOR | MINOR | (OTHER (EQ SYMBOL)?) | THIS_BLOCK;
THIS_BLOCK    : [Tt][Hh][Ii][Ss][Bb][Ll][Oo][Cc][Kk] ;
UNDER         : [Uu][Nn][Dd][Ee][Rr] ;


/* DWResident, DW... etc. are DWIDs */
/* (Decide=DWID) is a phrase used for tie-breaking by the auditor.*/

STRING      : '"' .*? '"' ;

INFROM      : IN | FROM ;
OR          : COMMA | [Oo][Rr] ;
AND         : PLUS | [Aa][Nn][Dd] ;

EXCEPT      : [Ee][Xx][Cc][Ee][Pp][Tt] ;
FROM        : [Ff][Rr][Oo][Mm] ;
IN          : [Ii][Nn] ;
OF          : [Oo][Ff] ;
TAG         : [Tt][Aa][Gg] (EQ SYMBOL)? ;
WITH        : LP [Ww][Ii][Tt][Hh] .*? RP ;

DISCIPLINE      : (LETTER | AT) (DIGIT | DOT | HYPHEN | LETTER)* ;
NUMBER      : DIGIT+ (DOT DIGIT*)? ;
CATALOG_NUMBER  : (NUMBER | WILDNUMBER) LETTER? ;
SYMBOL      : LETTER (LETTER | DIGIT | '_' | '-' | '&')* ;
ALPHANUM    : (LETTER | DIGIT | DOT | '_')+ ;
RANGE       : NUMBER ':' NUMBER ;

WILDNUMBER      : (DIGIT+ AT DIGIT* LETTER?) | (AT DIGIT+ LETTER?) ;

AT          : '@' ;
COMMA       : ',' ;
EQ          : '=' ;
GE          : '>=' ;
GT          : '>' ;
HYPHEN      : '-' ;
LE          : '<=' ;
LP          : '(' ;
LT          : '<' ;
PLUS        : '+' ;
RP          : ')' ;
SEMI        : ';' ;

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
HIDE           : '{' [Hh][Ii][Dd][Ee] .*? '}' -> skip ;
HIDERULE       : [Hh][Ii][Dd][Ee][Rr][Uu][Ll][Ee] -> skip ;
LOG            : [Ll][Oo][Gg] .*? '\n' -> skip ;

WHITESPACE  : [ \t\n\r]+ -> skip ;
