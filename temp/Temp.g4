grammar Temp;

paragraph       : (or_item | end_item | list)* ENDMARKER? EOF ;

list            : WORD+ ':' (or_item | (WORD COMMA))* (end_item | WORD) ;
end_item      : LB ~(COMMA_RB|RB)*? RB {System.err.printf("RB %s\n", $RB.text);} ;
or_item       : LB ~(COMMA_RB|RB)*? COMMA_RB {System.err.printf("COMMA_RB %s\n", $COMMA_RB.text);};

WORD            : ([a-zA-Z0-9_]|'’')+ ;
ENDMARKER       : '.' | '?' | '!' ;
COMMA           : ',' ;
LB              : ' '* '{' ;
RB              : ' '* '}' ;
COMMA_RB        : COMMA RB;

WS              : [ \t\n\r]+ -> skip ;
