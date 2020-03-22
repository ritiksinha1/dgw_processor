antlr := java -Xmx500M -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool
antpy := java -Xmx500M -Dlanguage=Python3 -cp .:/usr/local/lib/antlr-4.8-complete.jar org.antlr.v4.Tool

default: req_block

req_block: ReqBlock.g4
	$(antpy) -Dlanguage=Python3 ReqBlock.g4
	touch req_block

clean:
	 rm -f *.java *.class tokens tree
