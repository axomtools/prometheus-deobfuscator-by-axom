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
