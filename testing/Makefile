CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

build_args := -Xlog
build_args :=

run_args := -diagnostics
run_args :=

.PHONY: atn tokens

default: ReqBlockParser.class

gui: ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | filter | $(grun) ReqBlock req_block $(run_args) -gui

tree: ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | filter | $(grun) ReqBlock req_block $(run_args) -tree > tree

tokens: ReqBlockParser.class $(TEST_DATA)
	cat $(TEST_DATA) | filter | $(grun) ReqBlock req_block $(run_args) -tokens > tokens

atn: ReqBlock.g4
	$(antlr4) -atn ReqBlock.g4
	dot_to_svg
	ls -lF *.svg

ReqBlockParser.class: ReqBlock.g4 Makefile
	$(antlr4) $(build_args) ReqBlock.g4
	javac *.java

clean:
	 rm -f *.java *.class *.interp *.tokens *.dot *.svg parser tokens tree
