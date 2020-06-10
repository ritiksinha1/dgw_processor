# Project Design Notes
The goal is to translate Program Requirements in Degreeworks scribing format into a representation
that can be used to generate either a textual or graphical representation of that information.

Since the are multiple views anticipated, the first step is to translate the requirements into a
structured format. A JSON object for each requirements block was chosen rather that a relational
db ... because it seemed like a good idea at the time.

Fields:

* Program Code from CUNYfirst
* Program Name
* Catalog Year(s)
* Total Credits
* Transfer Credits Allowed
* Required Courses
* Notes

Required Courses is a list consisting of the following items
  
* A requirement group name (optional)
* A Subgroup name (optional)
    * Minimum grade required (optional)
    * List of course(s)
      * Discipline
      * Catalog Number: may be one, a list, or a range of numbers

Command Line Arguments for testing

  Canonical forms:
    Institution: lower-case 3-letter instutition code (qns => Queens College)
      Accept upper or lower case, with or without 01 suffix
    Any number of program codes
      Accept upper or lower case

### Hidden Rules (from Dennis Avalos)
  Documentation comments would be the comments you see in “#”. For example, Sociology made changes
  to some of their courses like SOC 212W. Any plan that requires DATA 212W will now have SOC 212W
  hidden. This allows the audit to show the student that they need DATA 212W but if a student
  already took SOC 212W it gets checked off.
    1 Class in DATA 212W, {HIDE SOC 212, 212W}
      Label "Sociological Analysis"

  Class in, HIDE, and Label are all keywords shown in red in the code image Dennis sent.
