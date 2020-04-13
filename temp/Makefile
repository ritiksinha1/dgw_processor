CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

default: sentence

gui: sentence
	$(grun) Temp sentence -gui < sentence.txt

tree: sentence
	$(grun) Temp sentence -tree < sentence.txt > tree

tokens: sentence
	$(grun) Temp sentence -tokens < sentence.txt > tokens

sentence: Temp.g4
	$(antlr4) Temp.g4
	javac *.java
	touch sentence

clean:
	 rm -f *.java *.class *.interp *.tokens tokens tree
