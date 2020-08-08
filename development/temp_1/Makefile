CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

diagnostics := '-diagnostics'
diagnostics :=

default: AreaTestParser.class

gui: AreaTestParser.class
	$(grun) AreaTest area_test $(diagnostics) -gui < test_data

tree: AreaTestParser.class
	$(grun) AreaTest area_test $(diagnostics) -tree < test_data > tree

tokens: AreaTestParser.class
	$(grun) AreaTest area_test $(diagnostics) -tokens < test_data > tokens

AreaTestParser.class: AreaTest.g4 Makefile test_data
	$(antlr4) AreaTest.g4
	javac *.java

clean:
	 rm -f *.java *.class *.interp *.tokens tokens tree
