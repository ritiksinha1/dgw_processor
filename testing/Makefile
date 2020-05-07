CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

args := -diagnostics
args :=

default: req_block

gui: req_block
	$(grun) ReqBlock req_block $(args) -gui < $(TEST_DATA)

tree: req_block tree
	$(grun) ReqBlock req_block $(args) -tree < $(TEST_DATA) > tree

tokens: req_block tokens
	$(grun) ReqBlock req_block $(args) -tokens < $(TEST_DATA) > tokens

atn: ReqBlock.g4
	$(antlr4) -atn ReqBlock.g4
	dot_to_svg
	ls -lF *.svg

req_block: ReqBlock.g4 Makefile
	$(antlr4) ReqBlock.g4
	javac *.java
	touch req_block

clean:
	 rm -f *.java *.class *.interp *.tokens *.dot *.svg req_block tokens tree
