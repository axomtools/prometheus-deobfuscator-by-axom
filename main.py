import sys
from read import parse
from emit import emit
from wash import wash
from rename import rename
from trace import say, fail
import unvm

default = {name: True for name in ('unbox', 'shrink', 'unmask', 'decrypt', 'strip', 'prune', 'squash')}


def clean(src):
    say('main', 'input length %d' % len(src))
    tree = parse(src)
    say('main', 'wash starting')
    tree = wash(tree, default)
    say('main', 'wash done')
    note = unvm.review(tree)
    say('main', 'emit starting')
    out = emit(tree)
    say('main', 'emit produced %d chars' % len(out))
    say('main', 'rename starting')
    out = rename(out)
    say('main', 'rename produced %d chars' % len(out))
    return out, note


def spot(src, line, col):
    rows = src.split('\n')
    if line - 1 >= len(rows):
        return ''
    row = rows[line - 1]
    start = max(col - 40, 0)
    end = min(col + 40, len(row))
    return row[start:end]


def main(argv):
    if len(argv) < 2:
        sys.stderr.write('usage: main.py input.lua\n')
        return 1
    say('main', 'reading ' + argv[1])
    try:
        with open(argv[1], 'r') as handle:
            data = handle.read()
    except FileNotFoundError as e:
        sys.stderr.write('missing file: %s\n' % e)
        return 2
    say('main', 'file size %d bytes' % len(data))
    try:
        out, note = clean(data)
    except SyntaxError as e:
        msg = str(e)
        sys.stderr.write('parse error: %s\n' % msg)
        parts = msg.split(' at line ')
        if len(parts) == 2:
            rest = parts[1].split(' col ')
            if len(rest) == 2:
                try:
                    line = int(rest[0])
                    col = int(rest[1])
                    near = spot(data, line, col)
                    sys.stderr.write('near: %s\n' % near)
                except ValueError:
                    pass
        fail('main', e)
        return 3
    except Exception as e:
        fail('main', e)
        return 4
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
    say('main', 'complete')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
