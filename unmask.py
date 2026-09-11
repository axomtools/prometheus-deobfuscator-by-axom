from node import node
from step import walk
from toy import space, load, fire, grab
import re

show = re.compile(r'^[\x20-\x7e]*$')


def score(fn, env):
    hits = 0
    for i in range(1, 40):
        try:
            val = fire(('func', fn, env), [i], [200])
            if isinstance(val, str) and 0 < len(val) < 512 and show.match(val):
                hits += 1
        except Exception:
            pass
    return hits


def collect(tree):
    env = space()
    load(env)
    found = []

    def take(n):
        if n.kind == 'local':
            for nm, ex in zip(n.names, n.exprs):
                if ex.kind == 'func' and len(ex.params) >= 1:
                    found.append((nm, ex, env))
                if ex.kind == 'func':
                    env.make(nm, ('func', ex, env))
                else:
                    try:
                        env.make(nm, grab(ex, env, [200]))
                    except Exception:
                        pass
        if n.kind == 'localfunc':
            fn = node('func', params=n.params, body=n.body)
            found.append((n.name, fn, env))
            env.make(n.name, ('func', fn, env))
        if n.kind == 'funcstat':
            fn = node('func', params=n.params, body=n.body)
            found.append((n.name, fn, env))
            env.make(n.name, ('func', fn, env))

    walk(tree, take)
    return found, env


def pick(tree):
    found, env = collect(tree)
    if not found:
        return None
    best = None
    topscore = 0
    for nm, fn, e in found:
        s = score(fn, e)
        if s > topscore:
            topscore = s
            best = (nm, fn, e)
    if best is None or topscore == 0:
        return None
    return best


def tag(tree):
    best = pick(tree)
    if best is not None:
        tree.__best_decoder__ = best
    return tree
