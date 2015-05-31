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
from itertools import groupby, izip_longest
from operator import attrgetter

import pygments
from pygments.lexer import RegexLexer
import pygments.lexers
import pygments.formatters
from pygments.token import Text


def read_file(fn):
    with open(fn) as f:
        return f.readlines()

# Override HtmlFormatter's wrap function so it
# doesn't wrap our result in excess HTML containers
class SparseFormatter(pygments.formatters.HtmlFormatter):
    def wrap(self, source, outfile):
        return source
formatter = SparseFormatter()

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

def _set_class(lst, cls):
    for hl in lst:
        hl.cls = hl.cls or cls
    return lst

def diff(prior, post, hbase, hflict):
    unified_diff = []
    for code, istart, iend, jstart, jend in difflib.SequenceMatcher(
            None, prior, post).get_opcodes():
        if code == 'equal':
            unified_diff.extend(hflict[jstart:jend])
        if code in ('delete', 'replace'):
            unified_diff.extend(_set_class(hbase[istart:iend], 'removal'))
        if code in ('insert', 'replace'):
            unified_diff.extend(_set_class(hflict[jstart:jend], 'addition'))
    return unified_diff

def highlight_base_file(contents, fname, lexer):
    return [HighlightedLine(cls='', html=html, line_no=ix)
            for ix, html in enumerate(pygments.highlight(
            ''.join(contents), lexer, formatter).splitlines(True))]

def highlight_conflict_file(lines, fname, lexer):
    """
    Find the <<<<<<<, =======, >>>>>>>> markers that represent
    the start, middle, and end of merge conflicts. highlight
    the code separated by each of these.
    """
    def highlight(text, cls, start_line):
        highlighted_text = pygments.highlight(text, lexer, formatter)
        return [HighlightedLine(cls, line or default, line_no)
                for line_no, (default, line) in
                enumerate(izip_longest(text.splitlines(True), highlighted_text.splitlines(True)), start_line)]
    ix = 0
    outlines = []
    while ix is not None and ix < len(lines):
        if lines[ix].startswith('<<<<<<<'):
            # Start of a conflict section!
            outlines.append(HighlightedLine(cls='conflict', html=lines[ix], line_no=ix))
            end_chunk = next(ix for ix, line in enumerate(lines[ix:], ix)
                             if line.startswith('======='))
            outlines.extend(highlight(
                text=''.join(lines[ix+1:end_chunk]),
                cls='conflict',
                start_line=ix+1))
            outlines.append(HighlightedLine(cls='conflict', html=lines[end_chunk], line_no=end_chunk))
            ix = end_chunk + 1

            # End of first half of conflict, now find ending bit

            end_chunk = next(ix for ix, line in enumerate(lines[ix:], ix)
                             if line.startswith('>>>>>>>'))
            outlines.extend(highlight(
                text=''.join(lines[ix:end_chunk]),
                cls='conflict',
                start_line=ix))
            outlines.append(HighlightedLine(cls='conflict', html=lines[end_chunk], line_no=end_chunk))
            ix = end_chunk + 1

            # End of conflict
        else:
            # Read until we find a conflict, or until the end ([ix:None])
            end_chunk = next((ix for ix, line in enumerate(lines[ix:], ix)
                              if line.startswith('<<<<<<<')), None)
            outlines.extend(highlight(''.join(lines[ix:end_chunk]),
                                      cls='',
                                      start_line=ix))
            ix = end_chunk
    assert map(attrgetter('line_no'), outlines) == range(len(outlines)), str(map(attrgetter('line_no'), outlines))
    return outlines

with open('out.html', 'w') as out_file:
    # Write the needed HTML to enable styles
    out_file.write('<head><link rel="stylesheet" type="text/css" href="style.css"></head>\n')
    out_file.write('<pre class="code">')
    base_file = read_file('example-repo/pre_conflict.py')
    language_lexer = pygments.lexers.guess_lexer_for_filename('example-repo/pre_conflict.py', base_file)

    flict_file = read_file('example-repo/same_fringe.py')
    hbase = highlight_base_file(base_file, lexer=language_lexer, fname='example-repo/pre_conflict.py')
    hflict = highlight_conflict_file(flict_file, lexer=language_lexer, fname='example-repo/same_fringe.py')


    classed = diff(base_file, flict_file, hbase, hflict)
    for cls, section in groupby(classed, attrgetter('cls')):
        out_file.write('<div' + (cls and ' class="{}"'.format(cls)) + '>')
        for line in section:
            out_file.write(line.html)
        out_file.write('</div>')
    out_file.write('</pre>')
