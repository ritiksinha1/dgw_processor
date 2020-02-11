#! /usr/local/bin/python3
""" Convert a Python data structure to an HTML structure that can be opened/collapsed to reveal/hide
    nested parts.
"""
import sys

sample_data = {
    'title': 'The name of the thing',
    'author': 'A. A. Person',
    'other_books':
    [
        {
            'title': 'First Other Book',
            'author': 'First Other Author'
        },
        {
            'title': 'Second Other Book',
            'author': 'Second Other Author',
            'coauthors':
            [
                {
                    'name': 'A. Co-Author',
                    'age': 12.6,
                    'words': ['many', 'many', 'words']
                },
                {
                    'name': 'Another Co-Author',
                    'words': ['in', 'other', 'words', 'maybe'],
                    'number': 42
                }
            ]
        }
    ]
}


def mk_html(arg, root=None):
  print(f'*** mkhtml({arg})', file=sys.stderr)
  if isinstance(arg, dict):
    html = ''
    for key, value in arg.items():
      if isinstance(value, dict) or isinstance(value, list):
        html += f'<section><h1 class="collapser">{key}</h1><ul>'
        html += mk_html(value)
        html += '</ul></section>'
      else:
        html += f'<li>{key}: {value}</li>'
    return html

  if isinstance(arg, list):
    return '<ul>' + '\n'.join([mk_html(item) for item in arg]) + '</ul>\n'

  # if isinstance(arg, str):
  #   return f'<li>{arg}</li>\n'

  # if isinstance(arg, int):
  #   return f'<li>{arg}</li>\n'

  # if isinstance(arg, float):
  #   return f'<li>{arg}</li>\n'

  return '<unexpected>'


if __name__ == '__main__':
  html = mk_html(sample_data, 'Sample Data')
  print(html)
