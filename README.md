# Degreeworks Processor
## Extract Program Requirements From Degreeworks Scribe Blocks

## Goal
Degreeworks (aka “DegreeWorks” or “Degree Works”) Scribe Blocks specify the requirements a student must meet to obtain an academic degree, major, minor, or concentration. Normally, they are used in conjuction with a studen’s transcript to produce an audit report telling what requirements a student has already completed and what the student still needs in order to complete the requirements.
Scribe Blocks provide (or _should_ provide) a definitive specification of requirements. The goal of this project is to extract program/degree requrements in a form that can serve as the basis for other applications, such as producing catalog descriptions for programs or course maps, and for institutional research. An initial application for the project is to provide a mechanism for publicizing the majors for which a course can satisfy a requirement.

## Terminology
- Scribe Block
: Code written in the Degreeworks Scribe language that specifies requirements for a degree or for a major, minor, concentration or “other” part of a degree, including references to institutional information, student transcript information, as well as the actual requrirements themselves.
- Requirement Block
: Another name for a Scribe Block
- WIP
: “Work in Progress” The status of this project!

## Methodology
For this project, all Scribe Blocks for all degrees and programs at the City University of New York (CUNY) are available in a database, which is updated regularly by the CUNY Office of Institutional Research and Assessment. This Degreeworks Processor extracts requirement block text from the database and converts it into a JSON data structure suitable for later processing by other applications. As part of the development process, the [Transfer Explorer project](https://github.com/cvickery/transfer-app/) pulls the JSON data from the database and presents the result on a web page. The Transfer Explorer’s [requirements page](https://transfer-app.qc.cuny.edu/requirements/) gives access to this information, but coverage of “processed blocks” is very spotty during the WIP phase of this project.
The project consists of an [ANTLR](https://www.antlr.org/) grammar for the Scribe language (_ReqBlock.g4_); ANTLR generates a parser from the grammar in either JavaScript or Python. The JavaScript parser is used in testing for a relatively-quick check that all Scribe Blocks can be parsed using the grammar. The Python parser is used by _dgw_interpreter.py_ to generate the JSON representation of Scribe Blocks for storage in the database.
