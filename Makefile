CLASSPATH := .:/usr/local/lib/antlr-4.8-complete.jar

default: req_block

req_block: ReqBlock.g4
	antlr -Dlanguage=Python3 ReqBlock.g4
	touch req_block

clean:
	 rm -f *.java *.class tokens tree
