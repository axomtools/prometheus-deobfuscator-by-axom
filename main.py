import sys
from read import parse
from emit import emit
from wash import wash
from rename import rename
import unvm

default = {name: True for name in ('unbox', 'shrink', 'unmask', 'decrypt', 'prune', 'squash')}


def clean(src):
    tree = parse(src)
    tree = wash(tree, default)
    note = unvm.review(tree)
    out = emit(tree)
    out = rename(out)
    return out, note


def main(argv):
    if len(argv) < 2:
        sys.stderr.write('usage: main.py input.lua\n')
        return 1
    try:
        with open(argv[1], 'r') as handle:
            data = handle.read()
    except FileNotFoundError as e:
        sys.stderr.write('missing file: %s\n' % e)
        return 2
    try:
        out, note = clean(data)
    except SyntaxError as e:
        sys.stderr.write('parse error: %s\n' % e)
        return 3
    if note['notes']:
        for line in note['notes']:
            sys.stderr.write('vm: ' + line + '\n')
        if note['strings']:
            sys.stderr.write('vm: %d strings found\n' % len(note['strings']))
        if note['program']:
            sys.stderr.write('vm: %d program cells found\n' % len(note['program']))
    sys.stdout.write(out)
    if not out.endswith('\n'):
        sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
