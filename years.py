""" Classes CatalogYears and AcademicYear
"""

import re
from datetime import datetime

# Class CatalogYears
# =================================================================================================
class CatalogYears():
  """ Represents a range of catalog years and which catalogs (graduate, undergraduate, both, or
      unspecified) are involved. When a student starts a program, the catalog year tells what the
      requirements are at that time.
  """
  # __init__()
  # -----------------------------------------------------------------------------------------------
  def __init__(self, period_start, period_stop):
    self.which_catalogs = []  # Serializable
    which_catalogs = set()  # Not serializable
    self.first_academic_year = None
    self.last_academic_year = None

    m_start = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_start)
    if m_start is not None:
      century_1, year_1, century_2, year_2, catalog = m_start.groups()
      try:
        self.first_academic_year = AcademicYear(century_1, year_1, century_2, year_2)
      except ValueError as e:
        self.first_academic_year = f'Unknown: {e}.'
      self.first_year = (century_1 * 100) + year_1
      if catalog == 'U':
        which_catalogs.add('Undergraduate')
      if catalog == 'G':
        which_catalogs.add('Graduate')

    if re.search(r'9999+', period_stop):
      self.last_academic_year = AcademicYear()
    else:
      m_stop = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_stop)
      if m_stop is not None:
        century_1, year_1, century_2, year_2, catalog = m_stop.groups()
        try:
          self.last_academic_year = AcademicYear(century_1, year_1, century_2, year_2)
        except ValueError as e:
          self.last_academic_year = f'Unknown: {e}.'
        self.last_year = (century_1 * 100) + year_1
        if catalog == 'U':
          which_catalogs.add('Undergraduate')
        if catalog == 'G':
          which_catalogs.add('Graduate')
    self.which_catalogs = sorted(list(which_catalogs), reverse=True)

  # __str__()
  # -----------------------------------------------------------------------------------------------
  def __str__(self):
    if self.first_academic_year != self.last_academic_year:
      return f'{self.first_academic_year} through {self.last_academic_year}'
    else:
      return f'{self.first_academic_year}'


# Class AcademicYear
# =================================================================================================
class AcademicYear:
  """ This is a helper class for representing one academic year as a string.
      Academic years run from September through the following August.
      The sting will be either CCYY-YY or CCYY-CCYYY or Now
  """
  # __init__()
  # -----------------------------------------------------------------------------------------------
  def __init__(self, century_1=None, year_1=None, century_2=None, year_2=None):
    """ Academic_Year constructor. Second year must be one greater than the first.
        if no args, the year is “Now”
    """
    if century_1 is None:
      self.is_now = True
      now = datetime.now()
      # The current academic year began last year if it is now Jan-Aug.
      if now.month < 9:
        self.year = now.year - 1
      else:
        self.year = now.year
    else:
      self.is_now = False
      self.century_1 = int(century_1)
      self.year_1 = int(year_1)
      self.century_2 = int(century_2)
      self.year_2 = int(year_2)
      self.year = 100 * self.century_1 + self.year_1
      if (100 * self.century_1 + self.year_1 + 1) != (100 * self.century_2 + self.year_2):
        raise ValueError(f'{100 * self.century_1 + self.year_1}, '
                         f'{100 * self.century_2 + self.year_2} is not a valid pair of years')

  # __str__()
  # -----------------------------------------------------------------------------------------------
  def __str__(self):
    if self.is_now:
      return 'Now'
    else:
      if self.century_1 != self.century_2:
        return f'{self.century_1}{self.year_1:02}-{self.century_2}{self.year_2:02}'
      else:
        return f'{self.century_1}{self.year_1:02}-{self.year_2:02}'
