from node import node
from step import walk
from toy import space, load, grab, fire, one
from trace import say
import unmask


def unbox(tree):
    if tree.kind == 'blk':
        stmts = tree.stmts
        if stmts:
            tail = stmts[-1]
            if tail.kind == 'ret' and len(tail.exprs) == 1:
                call = tail.exprs[0]
                if call.kind == 'call' and call.base.kind == 'pare' and not call.args:
                    inner = call.base.exp
                    if inner.kind == 'func' and not inner.params:
                        tree.stmts = stmts[:-1] + inner.body.stmts
                        say('wash', 'unboxed iife')
    for key, val in tree.__dict__.items():
        if key == 'kind':
            continue
        if isinstance(val, node):
            unbox(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, node):
                    unbox(item)
                elif isinstance(item, tuple):
                    for part in item:
                        if isinstance(part, node):
                            unbox(part)
    return tree


def locate(tree):
    if tree.kind != 'blk':
        say('wash', 'locate: root is %s not blk' % tree.kind)
        return None
    if len(tree.stmts) != 1:
        say('wash', 'locate: root has %d statements' % len(tree.stmts))
        return None
    s = tree.stmts[0]
    if s.kind != 'ret' or len(s.exprs) != 1:
        say('wash', 'locate: root statement is %s' % s.kind)
        return None
    e = s.exprs[0]
    if e.kind != 'call':
        say('wash', 'locate: return expr is %s' % e.kind)
        return None
    if e.base.kind != 'pare':
        say('wash', 'locate: call base is %s' % e.base.kind)
        return None
    fn = e.base.exp
    if fn.kind != 'func':
        say('wash', 'locate: paren contains %s' % fn.kind)
        return None
    if fn.body.kind != 'blk':
        say('wash', 'locate: func body is %s' % fn.body.kind)
        return None
    say('wash', 'locate: found wrapper body with %d statements' % len(fn.body.stmts))
    return fn.body


def simple(v):
    if v is None:
        return True
    if isinstance(v, (bool, int, float, str)):
        return True
    return False


def plain(v):
    if v is None:
        return node('nil')
    if isinstance(v, bool):
        return node('true' if v else 'false')
    if isinstance(v, int):
        return node('num', val=str(v))
    if isinstance(v, float):
        return node('num', val=repr(v))
    return node('str', val=v)


def rewrite(tree, env):
    count = [0]

    def visit(n):
        if n.kind != 'local':
            return
        for i, name in enumerate(n.names):
            if i >= len(n.exprs):
                continue
            ex = n.exprs[i]
            if ex.kind != 'table':
                continue
            if name not in env.map:
                continue
            val = env.map[name]
            if not isinstance(val, list):
                continue
            if not val:
                continue
            if not all(simple(v) for v in val):
                continue
            items = [('val', plain(v)) for v in val]
            n.exprs[i] = node('table', items=items)
            count[0] += 1

    walk(tree, visit)
    return count[0]


def uses(tree, name):
    hits = [0]

    def visit(n):
        if n.kind == 'call' and n.base.kind == 'name' and n.base.name == name:
            hits[0] += 1
        elif n.kind == 'mcall' and n.base.kind == 'name' and n.base.name == name:
            hits[0] += 1
        elif n.kind == 'name' and n.name == name:
            hits[0] += 1

    walk(tree, visit)
    return hits[0]


def decrypt(tree):
    env = space()
    load(env)
    env.make('...', [])

    setup = locate(tree)
    if setup is None:
        say('wash', 'no wrapper block found')
        return tree

    for i, stmt in enumerate(setup.stmts):
        say('wash', '  setup [%d] %s' % (i, stmt.kind))

    running = [5000000]
    ran = 0
    for stmt in setup.stmts:
        if stmt.kind == 'ret':
            break
        try:
            one(stmt, env, running)
        except Exception as e:
            say('wash', 'setup %d raised %s: %s' % (ran, e.__class__.__name__, e))
        ran += 1
    say('wash', 'ran %d statements, %d budget left' % (ran, running[0]))

    n = rewrite(tree, env)
    say('wash', 'rewrote %d tables with decoded contents' % n)

    names = set()
    for key, val in env.map.items():
        if isinstance(val, tuple) and val and val[0] == 'func':
            names.add(key)
    if names:
        say('wash', 'decoders available: %s' % ', '.join(sorted(names)))

    hits = [0]

    def rebuild(n):
        for key, val in n.__dict__.items():
            if key == 'kind':
                continue
            if isinstance(val, node):
                setattr(n, key, rebuild(val))
            elif isinstance(val, list):
                setattr(n, key, [rebuild(x) if isinstance(x, node) else x for x in val])
        if n.kind == 'call' and n.base.kind == 'name' and n.base.name in names:
            try:
                val = grab(n, env, [20000])
            except Exception:
                return n
            if isinstance(val, str):
                hits[0] += 1
                return node('str', val=val)
            if isinstance(val, bool):
                return node('true' if val else 'false')
            if isinstance(val, int):
                return node('num', val=str(val))
            if isinstance(val, float):
                return node('num', val=repr(val))
            if val is None:
                return node('nil')
        return n

    tree = rebuild(tree)
    say('wash', 'replaced %d calls with literals' % hits[0])

    kept = []
    dropped = 0
    for stmt in setup.stmts:
        if stmt.kind == 'localfunc' and stmt.name in names:
            probe = node('blk', stmts=[s for s in setup.stmts if s is not stmt])
            if uses(probe, stmt.name) == 0:
                say('wash', 'dropping dead function %s' % stmt.name)
                dropped += 1
                continue
        kept.append(stmt)
    setup.stmts = kept
    if dropped:
        say('wash', 'dropped %d dead statements' % dropped)

    return tree


def shrink(tree):
    if tree.kind == 'bin':
        tree.left = shrink(tree.left)
        tree.right = shrink(tree.right)
        if tree.left.kind == 'num' and tree.right.kind == 'num':
            try:
                a = eval(tree.left.val)
                b = eval(tree.right.val)
                op = tree.op
                if op == '+':
                    return node('num', val=repr(a + b) if isinstance(a, float) or isinstance(b, float) else str(a + b))
                if op == '-':
                    return node('num', val=repr(a - b) if isinstance(a, float) or isinstance(b, float) else str(a - b))
                if op == '*':
                    return node('num', val=repr(a * b) if isinstance(a, float) or isinstance(b, float) else str(a * b))
                if op == '/':
                    return node('num', val=repr(a / b))
                if op == '//':
                    return node('num', val=str(a // b))
                if op == '%':
                    return node('num', val=str(a % b))
                if op == '^':
                    return node('num', val=repr(a ** b))
            except Exception:
                pass
        if tree.left.kind == 'str' and tree.right.kind == 'str' and tree.op == '..':
            return node('str', val=tree.left.val + tree.right.val)
        return tree
    if tree.kind == 'un':
        tree.arg = shrink(tree.arg)
        if tree.arg.kind == 'num':
            try:
                v = eval(tree.arg.val)
                if tree.op == '-':
                    return node('num', val=repr(-v) if isinstance(v, float) else str(-v))
                if tree.op == '~':
                    return node('num', val=str(~int(v)))
            except Exception:
                pass
        return tree
    if tree.kind == 'pare':
        tree.exp = shrink(tree.exp)
        if tree.exp.kind in ('num', 'str', 'nil', 'true', 'false'):
            return tree.exp
        return tree
    for key, val in tree.__dict__.items():
        if key == 'kind':
            continue
        if isinstance(val, node):
            setattr(tree, key, shrink(val))
        elif isinstance(val, list):
            setattr(tree, key, [shrink(x) if isinstance(x, node) else x for x in val])
    return tree


def prune(tree):
    if tree.kind == 'if':
        tree.cond = prune(tree.cond)
        tree.body = prune(tree.body)
        if tree.otherwise is not None:
            tree.otherwise = prune(tree.otherwise)
        tree.chains = [(prune(c), prune(b)) for c, b in tree.chains]
        if tree.cond.kind == 'true' and not tree.chains:
            return node('do', body=tree.body)
        if tree.cond.kind == 'false' and not tree.chains:
            if tree.otherwise is not None:
                return node('do', body=tree.otherwise)
            return node('blk', stmts=[])
        return tree
    if tree.kind == 'while' and tree.cond.kind == 'false':
        return node('blk', stmts=[])
    for key, val in tree.__dict__.items():
        if key == 'kind':
            continue
        if isinstance(val, node):
            setattr(tree, key, prune(val))
        elif isinstance(val, list):
            setattr(tree, key, [prune(x) if isinstance(x, node) else x for x in val])
    return tree


def squash(tree):
    if tree.kind == 'do':
        tree.body = squash(tree.body)
        if not tree.body.stmts:
            return node('blk', stmts=[])
        return tree
    if tree.kind == 'blk':
        tree.stmts = [squash(s) for s in tree.stmts]
        flat = []
        for s in tree.stmts:
            if s.kind == 'do':
                flat.extend(s.body.stmts)
            else:
                flat.append(s)
        tree.stmts = flat
        return tree
    for key, val in tree.__dict__.items():
        if key == 'kind':
            continue
        if isinstance(val, node):
            setattr(tree, key, squash(val))
        elif isinstance(val, list):
            setattr(tree, key, [squash(x) if isinstance(x, node) else x for x in val])
    return tree


def wash(tree, opts):
    if opts.get('unbox', True):
        tree = unbox(tree)
    if opts.get('shrink', True):
        tree = shrink(tree)
    if opts.get('unmask', True):
        tree = unmask.tag(tree)
    if opts.get('decrypt', True):
        tree = decrypt(tree)
    if opts.get('prune', True):
        tree = prune(tree)
    if opts.get('squash', True):
        tree = squash(tree)
    if opts.get('shrink', True):
        tree = shrink(tree)
    return tree
