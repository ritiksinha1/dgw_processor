#! /usr/local/bin/python3
""" Convert a Python data structure to an HTML structure that can be opened/collapsed to reveal/hide
    nested parts.
"""
import sys
import os
DEBUG = os.getenv('DEBUG')

indent_level = 0
sample_data = {
    'title': 'The name of the thing',
    'author': 'A. A. Person',
    'other_book': [{'title': 'First Other Book',
                    'author': 'First Other Author'},
                   {'title': 'Second Other Book',
                    'author': 'Second Other Author',
                    'coauthor': [{'name': 'A. Co-Author',
                                  'age': 12.6,
                                  'word': ['many', 'many', 'words']
                                  },
                                 {'name': 'Another Co-Author',
                                  'word': ['in', 'other', 'words', 'maybe'],
                                  'number': 42000
                                  }
                                 ]
                    },
                   {'title': 'Third Other Book',
                    'author': 'Anonynmous'}
                   ]
}


def scalar2str(arg, title=''):
  """ Return a single li element with the value and possibly the title of the item.
      Handles strings, ints, and floats.
  """
  assert not (isinstance(arg, dict) or isinstance(arg, list) or isinstance(arg, tuple))
  if title == '':
    title_str = ''
  else:
    title_str = f'<strong>{title}:</strong> '

  if isinstance(arg, str):
    return f'{title_str}{arg}'
  if isinstance(arg, int):
    return f'{title_str}{arg:,}'
  if isinstance(arg, float):
    return f'{title_str}{arg:0.2f}'
  return 'unexpected'


def items2html(arg, title='item'):
  """ If arg has multiple items, return a closeable list. Otherwise, return a single li.
  """
  global indent_level
  if DEBUG:
    print(f'*** items2html({arg})', file=sys.stderr)
  assert isinstance(arg, list) or isinstance(arg, tuple)

  n = len(arg)
  suffix = 's' if n != 1 else ''
  html = f'\n{indent_level * "  "}<section>\n'
  indent_level += 1
  html += f'{indent_level * "  "}<h1 class="closer"><strong>' \
          f'{n} {title}{suffix}</strong></h1>\n{indent_level * "  "}<ul>\n'
  indent_level += 1
  for i in range(len(arg)):
    item = arg[i]
    if DEBUG:
      print(f'*** [{i}]; value: {item}', file=sys.stderr)
    html += f'{indent_level * "  "}<li><strong>{title}[{i}]:</strong> '
    if isinstance(item, dict):
      indent_level += 1
      html += dict2html(item, 'item')
      indent_level -= 1
      html += f'{indent_level * "  "}</li>\n'
    elif isinstance(item, list) or isinstance(arg, tuple):
      indent_level += 1
      html += items2html(item, f'{title}[{i}]')
      indent_level -= 1
      html += f'{indent_level * "  "}</li>\n'
    else:
      html += scalar2str(item) + '</li>\n'
  indent_level -= 1
  html += f'{indent_level * "  "}</ul>\n'
  indent_level -= 1
  html += f'{indent_level * "  "}</section>\n'
  return html


def dict2html(arg, title=''):
  """ If arg has multiple items, return a closeable list. Otherwise, return a single li.
  """
  global indent_level
  if DEBUG:
    print(f'*** dict2html({arg})', file=sys.stderr)
  assert isinstance(arg, dict)

  n = len(arg)
  suffix = 's' if n != 1 else ''
  html = f'\n{indent_level * "  "}<section>\n'
  indent_level += 1
  html += f'{indent_level * "  "}<h1 class="closer"><strong>{n} {title}{suffix}</strong>' \
          f'</h1>\n{indent_level * "  "}<ul>\n'
  indent_level += 1
  for key, value in arg.items():
    if DEBUG:
      print(f'*** key: {key}; value: {value}', file=sys.stderr)
    html += f'{indent_level * "  "}<li><strong>{key}: </strong> '
    if isinstance(value, dict):
      indent_level += 1
      html += dict2html(value)
      indent_level -= 1
      html += f'{indent_level * "  "}</li>\n'
    elif isinstance(value, list) or isinstance(value, tuple):
      indent_level += 1
      html += items2html(value, key)
      indent_level -= 1
      html += f'{indent_level * "  "}</li>\n'
    else:
      html += scalar2str(value) + '</li>\n'
  indent_level -= 1
  html += f'{indent_level * "  "}</ul>\n'
  indent_level -= 1
  return html + f'{indent_level * "  "}</section>\n'


if __name__ == '__main__':
  indent_level = 3
  print(f"""<!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="utf-8"/>
      <title>Closeable Test</title>
      <script src="./closeable.js"></script>
      <link rel="stylesheet" href="./closeable.css">
    </head>
    <body>
{dict2html(sample_data, 'Book')}
    </body>
  </html>
""")
