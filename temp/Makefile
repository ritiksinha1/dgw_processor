CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

default: paragraph

gui: paragraph
	$(grun) Temp paragraph  -diagnostics -gui < sentence.txt

tree: paragraph
	$(grun) Temp paragraph  -diagnostics -tree < sentence.txt > tree

tokens: paragraph
	$(grun) Temp paragraph  -diagnostics -tokens < sentence.txt > tokens

paragraph: Temp.g4
	$(antlr4) Temp.g4
	javac *.java
	touch paragraph

clean:
	 rm -f *.java *.class *.interp *.tokens tokens tree
