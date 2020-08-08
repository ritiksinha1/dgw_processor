grammar Temp_1;

list_test: class_rule* EOF;

class_rule: NUMBER CLASS IN? DISCIPLINE catalog_number (LIST_OR DISCIPLINE? catalog_number)* label?;

catalog_number: NUMBER | (LB .*? RB);

label: LABEL STRING ';'?;

LIST_OR: ','
       | [Oo][Rr]
       | (LB .*? (',' RB | COMMA_RB));

LABEL: [Ll][Aa][Bb][Ee][Ll];
CLASS: [Cc][Ll][Aa][Ss][Ss]([Ee][Ss])?;
IN: ([Ii][Nn])|([Ff][Rr][Oo][Mm]);

STRING: '"' ~'"'* '"';


DISCIPLINE: LETTER+;
NUMBER: DIGIT+ LETTER*;

LB: '{';
RB: '}';
COMMA_RB: ',}';

fragment DIGIT: [0-9];
fragment LETTER: [A-Za-z_];

COMMENT: '#' .*? '\n';
WHITESPACE: [ \n\r\t]+ -> skip;
