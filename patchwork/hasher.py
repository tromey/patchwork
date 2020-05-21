#!/usr/bin/env python
#
# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Hash generation for diffs."""

import hashlib
import re
import sys

from patchwork.parser import parse_patch

HUNK_RE = re.compile(r'^\@\@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? \@\@')
FILENAME_RE = re.compile(r'^(---|\+\+\+) (\S+)')
CHANGEID_RE = re.compile(r'^\s*Change-Id:\s+(\S+)$')


def hash_diff(diff):
    """Generate a hash from a diff."""

    # normalise spaces
    diff = diff.replace('\r', '')
    diff = diff.strip() + '\n'

    prefixes = ['-', '+', ' ']
    hashed = hashlib.sha1()

    for line in diff.split('\n'):
        if len(line) <= 0:
            continue

        hunk_match = HUNK_RE.match(line)
        filename_match = FILENAME_RE.match(line)

        if filename_match:
            # normalise -p1 top-directories
            if filename_match.group(1) == '---':
                filename = 'a/'
            else:
                filename = 'b/'
            filename += '/'.join(filename_match.group(2).split('/')[1:])

            line = filename_match.group(1) + ' ' + filename
        elif hunk_match:
            # remove line numbers, but leave line counts
            def fn(x):
                if not x:
                    return 1
                return int(x)
            line_nos = list(map(fn, hunk_match.groups()))
            line = '@@ -%d +%d @@' % tuple(line_nos)
        elif line[0] in prefixes:
            # if we have a +, - or context line, leave as-is
            pass
        else:
            # other lines are ignored
            continue

        hashed.update((line + '\n').encode('utf-8'))

    return hashed.hexdigest()


def hash_comment(comment):
    """Look for a Change-Id in the comment and return it, or None."""
    # normalise spaces
    comment = comment.replace('\r', '')
    comment = comment.strip() + '\n'

    for line in diff.split('\n'):
        change_match = CHANGEID_RE.match(line)
        if change_match:
            return change_match.group(1)

    return None


def hash_comment_or_diff(comment, diff):
    """Generate a hash from comment or a diff.

    A Change-Id in the comment is preferred; but if it is not available,
    then the diff will be hashed."""
    result = None
    if comment is not None:
        result = hash_comment(comment)
    if result is None and diff is not None:
        result = hash_diff(diff)
    return result


def split_and_hash(text):
    """Split the text into a comment and a patch, then use hash_comment_or_diff."""

    (patch, comment) = parse_patch(text)
    return hash_comment_or_diff(comment, patch)


def main(args):
    """Hash a diff provided by stdin.

    This is required by scripts found in /tools
    """
    print(split_and_hash('\n'.join(sys.stdin.readlines())))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
