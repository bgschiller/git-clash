"""
mkdir temp-repo
cd temp-repo
git init
git remote add origin {remote}
git fetch origin {base}:base
git fetch origin {compare}:compare
git checkout base
git merge compare
git status # Parse out all the 'Changes to be committed:' and 'Unmerged paths:' lines that start with \t
"""
from itertools import tee, ifilterfalse, ifilter
import json

import os
import subprocess
import shutil
from diffcolor import merge_conflict_diff

debug = True

def read_file(fn):
    try:
        with open(fn) as f:
            return f.readlines()
    except IOError:
        return []

def partition(pred, iterable):
    'Use a predicate to partition entries into false entries and true entries'
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return ifilterfalse(pred, t1), ifilter(pred, t2)

def merge_diff(repo, base_branch, compare_branch):
    os.mkdir('temp-repo')
    os.chdir('temp-repo')
    os.system('git init')
    os.system('git remote add origin {}'.format(repo))
    os.system('git fetch origin {}:base'.format(base_branch))
    os.system('git fetch origin {}:compare'.format(compare_branch))
    os.system('git checkout base')
    os.system('git merge compare --no-commit --no-ff')
    changed_files = [line.split(' ', 1)[1].strip() for line in
                     subprocess.check_output('git status -s'.split()).splitlines()]

    file_contents = {fname: read_file(fname) for fname in changed_files}
    os.system('git merge --abort')
    pre_merge = {fname: read_file(fname) for fname in changed_files}
    os.chdir('..')
    shutil.rmtree('temp-repo')
    if debug:
        with open('save_tree.json', 'w') as f:
            json.dump(dict(pre_merge=pre_merge, post_merge=file_contents), f)

    diffs = [merge_conflict_diff(fname, pre_merge[fname], file_contents[fname], header=(ix == 0))
             for ix, fname in enumerate(changed_files)]

    return '\n'.join(diffs)

if __name__ == '__main__':
    with open('out2.html', 'w') as f:
        f.write(merge_diff('https://{}@github.com/TopOPPS/topopps-web.git'.format(os.getenv('GITHUB_TOKEN')),
                           'release2_2', 'conflict-resolution').encode('utf-8'))
