import sys
import argparse
from parser import parse
from printer import emit
from pipeline import wash
from renamer import rename
from log import say, fail
import detector
import partitions as shape
import controlflow
import analysis
import instructions
import recover
import output
import environment

default = {name: True for name in ('unbox', 'shrink', 'unmask', 'decrypt', 'strip', 'prune', 'squash')}


def vmrun(tree):
    got = shape.build(tree)
    if got is None:
        return None
    ip, cs = got
    controlflow.link(cs)
    controlflow.rank(cs)
    controlflow.post(cs)
    analysis.scan(cs, 'MathFloor')
    analysis.all(cs, 'MathFloor')
    instructions.build(cs, ip)
    return ip, cs


def clean(src):
    environment.reset()
    say('main', 'input length %d' % len(src))
    tree = parse(src)
    say('main', 'wash starting')
    tree = wash(tree, default)
    say('main', 'wash done')
    payload = environment.build()
    if payload:
        say('main', 'using sandbox payload (%d lines)' % len(payload.splitlines()))
        return rename(payload), {'notes': [], 'strings': [], 'hints': set()}
    note = detector.review(tree)
    got = vmrun(tree)
    if got is not None:
        ip, cs = got
        note['blocks'] = len(cs)
        nodes = recover.top(cs)
        body = output.body(cs, ip, nodes)
        note['disassembly'] = output.disassemble(cs, ip)
        say('main', 'vm: %d blocks, %d top nodes' % (len(cs), len(nodes) if nodes else 0))
        return rename(body, preserved=note.get('hints', set())), note
    say('main', 'falling back to wrapper')
    body = emit(tree)
    return rename(body, preserved=note.get('hints', set())), note


def main(argv):
    ap = argparse.ArgumentParser(prog='pdeob', add_help=True)
    ap.add_argument('source', nargs='?', help='input lua file')
    ap.add_argument('-o', '--out', dest='out', nargs='?', const='output', default=None,
                    help='write to file (default name: output)')
    ap.add_argument('--debug', dest='debug', action='store_true', default=False,
                    help='write vm.txt for inspection')
    args = ap.parse_args(argv[1:])

    if args.source is None:
        sys.stderr.write('usage: main.py input.lua [-o [file]]\n')
        return 1

    say('main', 'reading ' + args.source)
    try:
        with open(args.source, 'r') as handle:
            data = handle.read()
    except FileNotFoundError as e:
        sys.stderr.write('missing file: %s\n' % e)
        return 2

    try:
        out, note = clean(data)
    except SyntaxError as e:
        sys.stderr.write('parse error: %s\n' % e)
        fail('main', e)
        return 3
    except Exception as e:
        fail('main', e)
        return 4

    for row in note.get('notes', []):
        sys.stderr.write('vm: ' + row + '\n')
    if note.get('strings'):
        sys.stderr.write('vm: %d strings found\n' % len(note['strings']))

    if args.debug and 'disassembly' in note:
        with open('vm.txt', 'w') as handle:
            handle.write(note['disassembly'])
            handle.write('\n')
        sys.stderr.write('wrote vm.txt\n')

    if args.out is not None:
        with open(args.out, 'w') as handle:
            handle.write(out)
            if not out.endswith('\n'):
                handle.write('\n')
        sys.stderr.write('wrote ' + args.out + '\n')
    else:
        sys.stdout.write(out)
        if not out.endswith('\n'):
            sys.stdout.write('\n')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
