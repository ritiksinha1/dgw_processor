# Degree Works Processor
## Extract Program Requirements From Degree Works Scribe Blocks

## Goal
Degree Works (aka “DegreeWorks”) Scribe Blocks specify the requirements a student must meet to obtain an academic degree, major, minor, or concentration. Normally, they are used in conjunction with a student’s transcript to produce an audit report telling what requirements a student has already completed and what the student still needs in order to complete the requirements.
Scribe Blocks provide (or _should_ provide) a definitive specification of requirements. The goal of this project is to extract program/degree requirements in a form that can serve as the basis for other applications, such as producing catalog descriptions for programs or course maps, and for institutional research. An initial application for the project is to provide a mechanism for publicizing the academic programs for which a course can satisfy a requirement.

## Terminology
- _Scribe Block_
: Code written in the Degre Works Scribe language that specifies requirements for a degree or for a major, minor, concentration or “other” part of a degree, including references to institutional information, student transcript information, as well as the actual requrirements themselves.
- _Requirement Block_
: Another name for a Scribe Block
- _WIP_
: “Work in Progress” The status of this project!

## Methodology
For this project, all Scribe Blocks for all degrees and programs at the City University of New York (CUNY) are available from the CUNY Office of Institutional Research and Assessment. These Scribe Blocks and associated metadata are copied to a local database for development work. This Degree Works Processor parses requirement block text from the database into a JSON-encoded parse tree suitable for later processing by other applications. The parse trees are saved in the local database.

## Subprojects
- An [ANTLR](https://www.antlr.org/) grammar for the Scribe language (_ReqBlock.g4_); ANTLR generates lexer/parser code from the grammar in either JavaScript or Python. (Other languages, too.)The JavaScript parser is used during testing for a relatively-quick check that all Scribe Blocks can be parsed using the grammar, and reports the handful that have syntax errors.
- Quarantine Manager: When the ANTLR lexer/parser fails, for some reason, the block has to be examined manually to determine whether the problem is in the grammar or the Scribe code. If the problem is in the Scribe code, the block is “quarantined” and blocked from further processing.
- The Python parser (_dgw\_parser.py_), which traverses the ANTLR parse tree and turns it into the
JSON-encoded parse_tree that is saved for use by other applications. Modules related to this subproject have names that start with _dgw_.
- An HTML Viewer (_htmlificization.py_). Modules related to this subproject have names that begin with _html_ or _format_.
- The Course Mapper (_course\_mapper.py_)

### Quarantine Manager
The quarantine manager provides a singleton object that other modules can use to determine whether a block has been quarantined or not. The module also provides a command-line interface for performing CRUD operations on the set of quarantined blocks. While the quarantined blocks are identified in their parse trees in the database, a CSV file is also maintained as a backing store for the list to help handle cases where different development systems get out of sync with one another. The CLI provides commands for managing the interchange of information among the CSV file, the in-memory dictionary, and the parse trees in the database.

### HTML Viewer
The Viewer is part of one of two “Transfer Explorer” projects at CUNY that use this project. The [development project](https://github.com/cvickery/transfer-app/) provides an interface for looking up [any NYS-approved program at CUNY](https://transfer-app.qc.cuny.edu/requirements/), and to view the requirements for that program using the HTML Viewer.
The Viewer shows the program requirements and the currently-active courses that can be used to satisfy them. The development project was the pilot implementation for viewing the rules that govern how courses transfer among CUNY colleges.

### Course Mapper
THE [CUNY Transfer Explorer (“T-Rex”)](https://explorer.cuny.edu/) is being developed as a “one-stop shop” for all things transfer-related at CUNY. The Course Mapper generates a structured table of program requirements and a mapping table of currently-active courses to those requirements. At the present time, those tables are generated on a development system and exported to T-Rex.

## Stand With Ukraine
[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://stand-with-ukraine.pp.ua)
