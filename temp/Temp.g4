grammar Temp;

tempest         : sentence <EOF> ;

sentence        : (with_comma | without_comma)* ;

without_comma   : LB .*? RB ;
with_comma      : LB .*? COMMA_RB ;

WORD            : [,'!.a-zA-Z0-9]+ ;
COMMA_RB        : COMMA RB;
COMMA           : ',' ;
LB              : '{' ;
RB              : '}' ;

WS              : [ \t\n\r]+ -> skip ;
