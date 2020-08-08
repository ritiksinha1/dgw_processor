CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

default: list_test

gui: list_test
	$(grun) Temp_1 list_test  -diagnostics -gui < test_data

tree: list_test
	$(grun) Temp_1 list_test  -diagnostics -tree < test_data > tree

tokens: list_test
	$(grun) Temp_1 list_test  -diagnostics -tokens < test_data > tokens

list_test: Temp_1.g4 Makefile test_data
	$(antlr4) Temp_1.g4
	javac *.java
	touch list_test

clean:
	 rm -f *.java *.class *.interp *.tokens tokens tree
