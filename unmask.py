from node import node
from step import walk
from toy import space, load, fire, grab
from trace import say
import re

show = re.compile(r'^[\x20-\x7e]*$')


def offset(fn):
    body = fn.body
    if body.kind != 'blk':
        return None
    if len(body.stmts) != 1:
        return None
    stmt = body.stmts[0]
    if stmt.kind != 'ret' or len(stmt.exprs) != 1:
        return None
    e = stmt.exprs[0]
    if e.kind != 'idx':
        return None
    k = e.key
    if k.kind == 'bin':
        if k.op == '+' and k.left.kind == 'name' and k.right.kind == 'num':
            try:
                return int(k.right.val)
            except ValueError:
                return None
        if k.op == '-' and k.left.kind == 'num' and k.right.kind == 'name':
            try:
                return -int(k.left.val)
            except ValueError:
                return None
    return None


def score(fn, env):
    off = offset(fn)
    if off is not None:
        rng = list(range(-off + 1, -off + 500))
    else:
        rng = list(range(1, 40)) + list(range(-100, 0))
    hits = 0
    for i in rng:
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
                        env.make(nm, grab(ex, env, [2000]))
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
        say('unmask', 'no candidate functions')
        return None
    best = None
    topscore = 0
    for nm, fn, e in found:
        s = score(fn, e)
        say('unmask', 'candidate %s scored %d' % (nm, s))
        if s > topscore:
            topscore = s
            best = (nm, fn, e)
    if best is None or topscore == 0:
        say('unmask', 'no viable decoder')
        return None
    say('unmask', 'chose %s' % best[0])
    return best


def tag(tree):
    best = pick(tree)
    if best is not None:
        tree.__best_decoder__ = best
    return tree
