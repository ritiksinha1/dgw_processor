CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig

default: skip_test

gui: skip_test
	$(grun) Temp_1 skip_test  -diagnostics -gui < test_data

tree: skip_test
	$(grun) Temp_1 skip_test  -diagnostics -tree < test_data > tree

tokens: skip_test
	$(grun) Temp_1 skip_test  -diagnostics -tokens < test_data > tokens

atn: Temp_1.g4
	$(antlr4) -atn Temp_1.g4
	dot_to_svg
	ls -lF *.svg

skip_test: Temp_1.g4 Makefile test_data
	$(antlr4) Temp_1.g4
	javac *.java
	touch skip_test

clean:
	 rm -f *.java *.class *.interp *.tokens *.dot *.svg tokens tree
