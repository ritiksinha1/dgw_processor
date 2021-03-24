antlr := java -Xmx500M -cp .:/usr/local/lib/antlr-4.9-complete.jar org.antlr.v4.Tool
antpy := java -Xmx500M -Dlanguage=Python3 -cp .:/usr/local/lib/antlr-4.9-complete.jar org.antlr.v4.Tool

.PHONY: parser

default: parser

parser: ReqBlockParser.py

ReqBlockParser.py: ReqBlock.g4 Makefile
	$(antpy) -Dlanguage=Python3 -visitor ReqBlock.g4

clean:
	 rm -f *.java *.class tokens tree
