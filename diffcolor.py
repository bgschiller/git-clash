"""
Start with a file with conflicts and its revision immediately prior.
    - split the file on its conflicts, syntax highlight it.
    - syntax highlight the prior revision
    - perform a diff between the two files, to get a list of all added and removed lines.
        - Diff output is one of:
            - `LaM[,N]`: lines M..N were added in the new version to position L of the original.
            - `M[,N]dL`: lines M..N in original were deleted. They would have appeared at
            position L of the new version.
    - For each added line, mark it green unless it's already a conflict
    - For each removed line, insert it into the list marked red.
"""

import difflib
from itertools import groupby
from operator import attrgetter

import pygments
from pygments.lexer import RegexLexer
import pygments.lexers
import pygments.formatters
from pygments.token import Text


def read_file(fn):
    with open(fn) as f:
        return f.read()

file_names = ['example-repo/pre_conflict.py', 'example-repo/same_fringe.py']
file_contents = [read_file(fn) for fn in file_names]

# Override HtmlFormatter's wrap function so it
# doesn't wrap our result in excess HTML containers
class SparseFormatter(pygments.formatters.HtmlFormatter):
    def wrap(self, source, outfile):
        return source

class EmptyLexer(RegexLexer):
    name = 'Empty'
    tokens = {
        'root': [
            (r'.*\n', Text)
        ]
    }
no_lexer = EmptyLexer()

class HighlightedLine(object):
    def __init__(self, cls, html, line_no):
        self.cls = cls
        self.html = html
        self.line_no = line_no

    def __str__(self):
        if self.cls is not None:
            return '<div class="{s.cls}" id="line_{s.line_no}">{s.html}</div>'.format(s=self)
        return '<div id="line_{s.line_no}">{s.html}</div>'.format(s=self)
    def __repr__(self):
        return '<HighlightedLine %s>' % self

def highlight_base_file(fname):
    with open(fname) as f:
        lines = f.readlines()
    language_lexer = pygments.lexers.guess_lexer_for_filename(fname, ''.join(lines))
    return [HighlightedLine(cls='', line=html, line_no=ix)
            for ix, html in enumerate(pygments.highlight(
            ''.join(lines), language_lexer, SparseFormatter()
        ).splitlines(True))]

def highlight_conflict_file(fname):
    """
    Find the <<<<<<<, =======, >>>>>>>> markers that represent
    the start, middle, and end of merge conflicts. highlight
    the code separated by each of these.
    """
    with open(fname) as f:
        lines = f.readlines()
    language_lexer = pygments.lexers.guess_lexer_for_filename(fname, ''.join(lines))

    def highlight(text, lexer, cls, start_line):
        return [HighlightedLine(cls, line, line_no)
                for line_no, line in
                enumerate(pygments.highlight(text, lexer, SparseFormatter()).splitlines(True), start_line)]
    ix = 0
    outlines = []
    while ix is not None and ix < len(lines):
        if lines[ix].startswith('<<<<<<<'):
            # Start of a conflict section!
            outlines.extend(highlight(lines[ix], no_lexer, 'conflict', ix))
            end_chunk = next(ix for ix, line in enumerate(lines[ix:], ix)
                             if line.startswith('======='))
            outlines.extend(highlight(
                text=''.join(lines[ix+1:end_chunk]),
                lexer=language_lexer,
                cls='conflict',
                start_line=ix+1))
            outlines.extend(highlight(lines[end_chunk], no_lexer, 'conflict', end_chunk))
            ix = end_chunk + 1

            # End of first half of conflict, now find ending bit

            end_chunk = next(ix for ix, line in enumerate(lines[ix:], ix)
                             if line.startswith('>>>>>>>'))
            outlines.extend(highlight(
                text=''.join(lines[ix:end_chunk]),
                lexer=language_lexer,
                cls='conflict',
                start_line=ix))
            outlines.extend(highlight(lines[end_chunk], no_lexer, 'conflict', end_chunk))
            ix = end_chunk + 1

            # End of conflict
        else:
            # Read until we find a conflict, or until the end ([ix:None])
            end_chunk = next((ix for ix, line in enumerate(lines[ix:], ix)
                              if line.startswith('<<<<<<<')), None)
            outlines.extend(highlight(''.join(lines[ix:end_chunk]),
                                      lexer=language_lexer,
                                      cls='',
                                      start_line=ix))
            ix = end_chunk
    return outlines

with open('out.html', 'w') as out_file:
    # Write the needed HTML to enable styles
    out_file.write('<head><link rel="stylesheet" type="text/css" href="style.css"></head>\n')
    out_file.write('<pre class="code">')
    # Get the diff line by line
    # The 4 arguments are 2 files and their 2 names
    for cls, section in groupby(highlight_conflict_file('example-repo/same_fringe.py'), attrgetter('cls')):
        out_file.write('<div' + (cls and ' class="{}"'.format(cls)) + '>')
        for line in section:
            out_file.write(line.html)
        out_file.write('</div>')
    out_file.write('</pre>')
