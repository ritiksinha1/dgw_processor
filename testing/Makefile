CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

default: req_block

gui: req_block
	$(grun) ReqBlock req_block -diagnostics -gui < $(TEST_DATA)

tree: req_block
	$(grun) ReqBlock req_block -diagnostics -tree < $(TEST_DATA) > tree

tokens: req_block
	$(grun) ReqBlock req_block -diagnostics -tokens < $(TEST_DATA) > tokens

req_block: ReqBlock.g4
	$(antlr4) ReqBlock.g4
	javac *.java
	touch req_block

clean:
	 rm -f *.java *.class *.interp *.tokens tokens tree
