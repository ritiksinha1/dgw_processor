#! /usr/local/bin/python3
""" Function to filter out cruft at the end of requirement blocks.
    Can be used from the command line as a filter.
"""

import re
import sys


# dgw_filter()
# -------------------------------------------------------------------------------------------------
def dgw_filter(src, remove_comments=True, remove_hide=False):
  """ Remove all text following "END."
      Straighten left curly single quotes. # TESTING: is this necessary?
      Optional (default True): remove all comments.
      Optional (default False):remove content inside hide-from-advice structures. Default is to
                remove all curly braces and hide-from-advice keywords.
  """

  # Remove all text following END.
  return_str = re.sub(r'[Ee][Nn][Dd]\.(.|\n)*', 'END.\n', src)

  # Assume any apostrophes were originally primes that were replaced for db storage: undo them
  return_str = return_str.replace('’', '\'')

  # Remove comments
  if remove_comments:
    # Protect strings that contain #'s and/or !'s
    while re.search(r'".*?#|!.*?"', return_str):
      return_str = re.sub(r'(.*".*?)#|!(.*?".*)', r'\1VICKERY\2', return_str)

    return_str = re.sub(f'#.*?\n', '\n', return_str)

    # Restore strings
    return_str = re.sub('VICKERY', '#', return_str)

  # Hide hide-rule to avoid confound with hide(-from-advice)? keyword
  return_str = re.sub(r'hide-?rule', 'VICKERY', return_str, flags=re.I)

  if remove_hide:
    # Remove {HIDE-FROM-ADVICE <hidden_content>}
    """
        From Scribe Language Users Guide:
        The trick to knowing where the place the commas when using Hide (from advice) is to be sure
        that everything within and including the braces can be removed leaving a valid, parseable
        course rule.
        # Hide ECON 112 from the advice
         3 Classes in ACCT 103, 105, {Hide ECON 112,} 114
          Label ACCOUNTING "Accounting Requirements";
        # Hide MATH 104 from the advice
         3 Credits in MATH 184, {HideFromAdvice MATH 104 (WITH DWTerm < 201230)}
           Label MATH "Math Requirement";
        # Show HIST 184 but hide the WITH information
         5 Credits in HIST 184 (WITH Hide DWResident = Y)
           Label HIST "History Requirement";

        But Note that the hide clause can be inside a with-clause or group enclosed in parentheses
        instead of curly quotes, or an area enclosed in square brackets.

        Other observation: if all the courses in an area are hidden, you can end up with an empty
        area. Likewise, you can end up with a class/credit requirement where the course list ends up
        missing. And handling hidden groups means dealing with OR before, after, or neither of the
        parens.

        Further note, that a course can satisfy a requirement even if it is hidden, so the mapper
        should see them anyway.

        So this feature is not implemented at this time
  """
    exit('dgw_filter: remove_hide option not supported at this time.')

  else:
    # remove all curly braces and hide-from-advice keywords
    return_str = return_str.replace('{', '').replace('}', '')
    # Note that this also removes "hide" from proxy-advice and remark strings.
    # https://www.thefreedictionary.com/words-containing-hide suggests that this will not be an
    # issue.
    return_str = re.sub(r'hide(-?from-?advice)?', '', return_str, flags=re.I | re.S)

    # Restore any omitted Hide-Rule keywords
    return_str = re.sub('VICKERY', 'Hide-Rule', return_str)

  return return_str


# As a command, act as a stdin|stdout filter
if __name__ == "__main__":
  print(dgw_filter(sys.stdin.read()))
