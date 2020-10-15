
class Any():
  """ Used for matching tuples of unequal length, but could be used elsewhere.
      From https://stackoverflow.com/questions/29866269/
      Not the same as unittest.mock.ANY
  """
  def __eq__(self, other):
    return True

  def __repr__(self):
    return 'Any'


ANY = Any()
