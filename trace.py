import sys
import traceback

on = True


def say(area, text):
    if on:
        sys.stderr.write('[' + area + '] ' + text + '\n')
        sys.stderr.flush()


def fail(area, err):
    say(area, err.__class__.__name__ + ': ' + str(err))
    if on:
        for row in traceback.format_exc().splitlines():
            sys.stderr.write('    ' + row + '\n')
        sys.stderr.flush()


def dump(label, obj, deep=0):
    if not on:
        return
    pad = '  ' * deep
    sys.stderr.write(pad + label + ': ' + repr(obj) + '\n')
    sys.stderr.flush()
