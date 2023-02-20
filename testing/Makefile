ifeq (${HOSTTYPE},aarch64)
	CLASSPATH := ./classes:/opt/homebrew/Cellar/antlr/4.12.0/antlr-4.12.0-complete.jar
	antlr4 := java -Xmx500M -cp ./classes:/opt/homebrew/Cellar/antlr/4.12.0/antlr-4.12.0-complete.jar org.antlr.v4.Tool
	antpy := antlr4 -Dlanguage=Python3
	grun := java -Xmx500M -cp ./classes:/opt/homebrew/Cellar/antlr/4.12.0/antlr-4.12.0-complete.jar org.antlr.v4.gui.TestRig
else
	CLASSPATH := ./classes:/usr/local/lib/antlr-4.12.0-complete.jar
	antlr4 := java -Xmx500M -cp ./classes:/usr/local/lib/antlr-4.12.0-complete.jar org.antlr.v4.Tool
	antpy := antlr4 -Dlanguage=Python3
	grun := java -Xmx500M -cp ./classes:/usr/local/lib/antlr-4.12.0-complete.jar org.antlr.v4.gui.TestRig
endif

build_args := -Xlog
build_args :=

run_args := -diagnostics
run_args :=

.PHONY: atn parser

default: run

run: ./classes/ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | ../dgw_preprocessor.py | $(grun) ReqBlock req_block $(run_args)

gui: ./classes/ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | ../dgw_preprocessor.py | $(grun) ReqBlock req_block $(run_args) -gui

tree: ./classes/ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | ../dgw_preprocessor.py | $(grun) ReqBlock req_block $(run_args) -tree > tree

tokens: ./classes/ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | ../dgw_preprocessor.py | $(grun) ReqBlock req_block $(run_args) -tokens > tokens

atn: ReqBlock.g4
	$(antlr4) -atn ReqBlock.g4
	ls -lF *.dot | echo "Congratulations, you now have `wc -l` dot files!"

parser: ./classes/ReqBlockParser.class

ReqBlock.g4: ../ReqBlock.g4
	cp ../ReqBlock.g4 .

./classes/ReqBlockParser.class: ReqBlock.g4 Makefile
	$(antlr4) $(build_args) ReqBlock.g4
	javac *.java -d classes

clean:
	 rm -f *.java ./classes/*.class *.interp *.tokens *.dot *.svg parser tokens tree
