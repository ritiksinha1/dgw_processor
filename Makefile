ifeq (${HOSTTYPE},aarch64)
	antlr := java -Xmx500M -cp .:/opt/homebrew/Cellar/antlr/4.9.3/antlr-4.9.3-complete.jar org.antlr.v4.Tool
	antpy := java -Xmx500M -Dlanguage=Python3 -cp .:/opt/homebrew/Cellar/antlr/4.9.3/antlr-4.9.3-complete.jar org.antlr.v4.Tool
else
	antlr := java -Xmx500M -cp .:/usr/local/lib/antlr-4.9.3-complete.jar org.antlr.v4.Tool
	antpy := java -Xmx500M -Dlanguage=Python3 -cp .:/usr/local/lib/antlr-4.9.3-complete.jar org.antlr.v4.Tool
endif

.PHONY: parser

default: parser

parser: ReqBlockParser.py

ReqBlockParser.py: ReqBlock.g4 Makefile
	$(antpy) -Dlanguage=Python3 -visitor ReqBlock.g4

clean:
	 rm -f *.java *.class tokens tree
