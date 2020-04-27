grammar Temp;

paragraph       : (or_phrase | end_phrase | list)* ;

list            : WORD+ ':' (or_phrase | (WORD COMMA))* (end_phrase | WORD) ;
end_phrase      : LB ~(COMMA_RB|RB)*? RB ;
or_phrase       : LB ~(COMMA_RB|RB)*? COMMA_RB {System.err.println($COMMA_RB.text);};

WORD            : ([a-zA-Z0-9]|'’')+ ;
ENDMARKER       : '.' | '?' | '!' ;
COMMA           : ',' ;
LB              : '{' ;
RB              : '}' ;
COMMA_RB        : COMMA ' '* RB;

WS              : [ \t\n\r]+ -> skip ;
