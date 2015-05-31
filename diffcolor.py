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
import StringIO

import difflib
from itertools import groupby, izip_longest
from operator import attrgetter

import pygments
import pygments.lexers
import pygments.formatters



# Override HtmlFormatter's wrap function so it
# doesn't wrap our result in excess HTML containers
from pygments.util import ClassNotFound


class SparseFormatter(pygments.formatters.HtmlFormatter):
    def wrap(self, source, outfile):
        return source
formatter = SparseFormatter()

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

def highlight_base_file(contents, lexer):
    return [HighlightedLine(cls='', html=html, line_no=ix)
            for ix, html in enumerate(pygments.highlight(
            ''.join(contents), lexer, formatter).splitlines(True))]

def highlight_conflict_file(lines, lexer):
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

def merge_conflict_diff(fname, base_lines, flict_lines, header=True):
    out_file = StringIO.StringIO()
    # Write the needed HTML to enable styles
    if header:
        out_file.write('<head><link rel="stylesheet" type="text/css" href="/style.css"></head>\n')
    out_file.write('<h3>' + fname + '</h3>')
    out_file.write('<pre class="code">')
    try:
        language_lexer = pygments.lexers.guess_lexer_for_filename(fname, ''.join(base_lines))
    except ClassNotFound:
        language_lexer = pygments.lexers.diff.DiffLexer()

    hbase = highlight_base_file(flict_lines, lexer=language_lexer)
    hflict = highlight_conflict_file(flict_lines, lexer=language_lexer)

    classed = diff(base_lines, flict_lines, hbase, hflict)
    for cls, section in groupby(classed, attrgetter('cls')):
        out_file.write('<div' + (cls and ' class="{}"'.format(cls)) + '>')
        for line in section:
            out_file.write(line.html)
        out_file.write('</div>')
    out_file.write('</pre>')
    ret = out_file.getvalue()
    out_file.close()
    return ret

if __name__ == '__main__':
    with open('out.html', 'w') as out_file:
        out_file.write(merge_conflict_diff('example-repo/pre_conflict.py', 'example-repo/same_fringe.py'))
