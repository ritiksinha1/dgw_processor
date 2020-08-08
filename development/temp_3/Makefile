CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar
antlr4 := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := antlr4 -Dlanguage=Python3
grun := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.gui.TestRig


run_args := -diagnostics
run_args :=

.phony: tokens

default: test_3

gui: test_3
	$(grun) Temp_3 test_3  $(run_args) -gui < test_data

tree: test_3
	$(grun) Temp_3 test_3  $(run_args) -tree < test_data > tree

tokens: test_3
	$(grun) Temp_3 test_3  $(run_args) -tokens < test_data > tokens

atn: Temp_3.g4
	$(antlr4) -atn Temp_3.g4
	dot_to_svg
	ls -lF *.svg

test_3: Temp_3.g4 Makefile test_data
	$(antlr4) Temp_3.g4
	javac *.java
	touch test_3

clean:
	 rm -f *.java *.class *.interp *.tokens *.dot *.svg tokens tree
