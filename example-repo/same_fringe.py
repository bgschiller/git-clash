<<<<<<< HEAD
# to give credit where credit is due:
# This problem comes from http://rosettacode.org/wiki/Same_Fringe#Python

=======
"""
This problem comes from http://rosettacode.org/wiki/Same_Fringe#Python

Write a routine that will compare the leaves ("fringe") of two binary trees to determine
whether they are the same list of leaves when visited left-to-right. The structure or
balance of the trees does not matter; only the number, order, and value of the leaves is
important.

Any solution is allowed here, but many computer scientists will consider it inelegant to
collect either fringe in its entirety before starting to collect the other one. In fact,
this problem is usually proposed in various forums as a way to show off various forms of
concurrency (tree-rotation algorithms have also been used to get around the need to collect
one tree first). Thinking of it a slightly different way, an elegant solution is one that
can perform the minimum amount of work to falsify the equivalence of the fringes when they
differ somewhere in the middle, short-circuiting the unnecessary additional traversals and
comparisons.

Any representation of a binary tree is allowed, as long as the nodes are orderable, and
only downward links are used (for example, you may not use parent or sibling pointers to
avoid recursion).
"""
>>>>>>> better-docstring
try:
    from itertools import zip_longest as izip_longest # Python 3.x
except:
    from itertools import izip_longest                # Python 2.6+

def fringe(tree):
    """Yield tree members L-to-R depth first,
    as if stored in a binary tree"""
    for node1 in tree:
        if isinstance(node1, tuple):
            for node2 in fringe(node1):
                yield node2
        else:
            yield node1

def same_fringe(tree1, tree2):
    return all(node1 == node2 for node1, node2 in
               izip_longest(fringe(tree1), fringe(tree2)))

# A non-conflicting comment

if __name__ == '__main__':
    a = 1, 2, 3, 4, 5, 6, 7, 8
    b = 1, (( 2, 3 ), (4, (5, ((6, 7), 8))))
    c = (((1, 2), 3), 4), 5, 6, 7, 8

    x = 1, 2, 3, 4, 5, 6, 7, 8, 9
    y = 0, 2, 3, 4, 5, 6, 7, 8
    z = 1, 2, (4, 3), 5, 6, 7, 8

    assert same_fringe(a, a)
    assert same_fringe(a, b)
    assert same_fringe(a, c)

    assert not same_fringe(a, x)
    assert not same_fringe(a, y)
    assert not same_fringe(a, z)