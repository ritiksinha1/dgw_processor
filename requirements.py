import json


class Requirements():
  """ Representation of the requirements for an academic program.
      The constructor takes a text description in Degreeworks Scribe format, which is stored as the
      "scribe_text" member. The parsed information is available in the "json" and "html" members.
      The _str_() method returns a plain text version.
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

