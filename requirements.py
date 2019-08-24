import json
import re


class Requirements():
  """ Representation of the requirements for an academic program.
      The constructor takes a text description in Degreeworks Scribe format, which is stored as the
      "scribe_text" member. The parsed information is available in the "json" and "html" members.
      The _str_() method returns a plain text version.

      Fields:
        code    Program Code from CUNYfirst
        title   Program Title
        years   Catalog Year(s)
        credits Total Credits
        limit   Transfer Credits Allowed
        courses Required Courses
        notes   Notes

  """

  def __init__(this, requirement_text):
    this.scribe_text = requirement_text
    this.requirements = {'total_credits': 'unknown'}
    comments = []
    lines = requirement_text.split('\n')
    for line in lines:
      if line.startswith('#'):
        comments.append(line)
    this.requirements['comments'] = comments

  def __str__(this):
    return '\n'.join(this.requirements['comments'])

  def json(this):
    return json.dumps(this.requirements)

  def html(this):
    return f"""<p>A total of {this.requirements['total_credits']} credits.</p>
            """


class AcademicYear:
  """
  """
  def __init__(self, century_1=None, year_1=None, century_2=None, year_2=None):
    """ Academic_Year constructor. Second year must be one greater than the first.
        Omit args for “Now”
    """
    if century_1 is None:
      self.is_now = True
    else:
      self.is_now = False
      self.century_1 = int(century_1)
      self.year_1 = int(year_1)
      self.century_2 = int(century_2)
      self.year_2 = int(year_2)
      if (100 * self.century_1 + self.year_1 + 1) != (100 * self.century_2 + self.year_2):
        raise ValueError(f'{100 * self.century_1 + self.year_1}, '
                         f'{100 * self.century_2 + self.year_2} is not a valid pair of years')

  def __str__(self):
    if self.is_now:
      return 'Now'
    else:
      if self.century_1 != self.century_2:
        return f'{self.century_1}{self.year_1:02}-{self.century_2}{self.year_2:02}'
      else:
        return f'{self.century_1}{self.year_1:02}-{self.year_2:02}'


class Catalogs:
  def __init__(self, period_start, period_stop):
    """ First Year = CCYY-YY or CCYY-CCYY if centuries differ
        Last Year = CCYY-YY or CCYY-CCYY or 'Now'
        Other values: 'Missing', 'Unknown', or 'Unused'
        Catalogs: list which will be either empty, Undergraduate, Graduate, or both

    """
    self.which_catalogs = set()
    self.first_academic_year = None
    self.last_academic_year = None

    m_start = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_start)
    if m_start is not None:
      century_1, year_1, century_2, year_2, catalog = m_start.groups()
      self.first_academic_year = AcademicYear(century_1, year_1, century_2, year_2)
      if catalog == 'U':
        self.which_catalogs.add('Undergraduate')
      if catalog == 'G':
        self.which_catalogs.add('Graduate')

    if re.search(r'9999+', period_stop):
      self.last_academic_year = AcademicYear(None, None, None, None)
    else:
      m_stop = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_stop)
      if m_stop is not None:
        century_1, year_1, century_2, year_2, catalog = m_stop.groups()
        assert (int(century_2) * 100 + int(year_2)) == (1 + int(century_1) * 100 + int(year_1))
        if century_1 != century_2:
          last_academic_year = f'{century_1}{year_1}-{century_2}{year_2}'
        else:
          last_academic_year = f'{century_1}{year_1}-{year_2}'
        if catalog == 'U':
          catalogs.add('Undergraduate')
        if catalog == 'G':
          catalogs.add('Graduate')

    if first_academic_year != last_academic_year:
      return f'{first_academic_year} to {last_academic_year}', catalogs
    else:
      return f'{first_academic_year}', catalogs
