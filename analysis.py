from walker import walk


def grabs(stmt, base):
    out = set()

    def visit(n):
        if n.kind == 'idx' and n.base.kind == 'name' and n.base.name == base:
            if n.key.kind == 'num':
                try:
                    out.add(int(n.key.val))
                except ValueError:
                    pass

    walk(stmt, visit)
    return out


def puts(stmt, base):
    out = set()

    def visit(n):
        if n.kind == 'assign':
            for t in n.targets:
                if t.kind == 'idx' and t.base.kind == 'name' and t.base.name == base:
                    if t.key.kind == 'num':
                        try:
                            out.add(int(t.key.val))
                        except ValueError:
                            pass

    walk(stmt, visit)
    return out


def scan(cells, base):
    for c in cells:
        reads = set()
        writes = set()
        for s in c.body:
            reads |= grabs(s, base)
            writes |= puts(s, base)
        c.reads = reads
        c.writes = writes
    return cells


def slot(n, base):
    if n.kind != 'idx':
        return None
    if n.base.kind != 'name' or n.base.name != base:
        return None
    if n.key.kind != 'num':
        return None
    try:
        return int(n.key.val)
    except ValueError:
        return None


def number(n):
    if n.kind != 'num':
        return None
    try:
        return int(n.val)
    except ValueError:
        return None


def slotarg(n, base):
    if n is None:
        return None, None
    return slot(n, base), number(n)


def mathop(e, base):
    op = e.op
    lreg, lval = slotarg(e.left, base)
    rreg, rval = slotarg(e.right, base)
    return (op, lreg, lval, rreg, rval)


def callop(e, base):
    if e.kind != 'call':
        return None
    if e.base.kind != 'name':
        return None
    reg = None
    if e.args and len(e.args) == 1:
        reg, _ = slotarg(e.args[0], base)
    return (e.base.name, reg)


def read(stmt, base):
    if stmt.kind != 'assign':
        return None
    if len(stmt.targets) != 1 or len(stmt.exprs) != 1:
        return None
    t = stmt.targets[0]
    e = stmt.exprs[0]
    dest = slot(t, base)
    if dest is None:
        return None
    if e.kind == 'num':
        try:
            return ('const', dest, int(e.val))
        except ValueError:
            return None
    if e.kind == 'str':
        return ('const', dest, e.val)
    if e.kind == 'nil':
        return ('const', dest, None)
    if e.kind == 'true':
        return ('const', dest, True)
    if e.kind == 'false':
        return ('const', dest, False)
    src = slot(e, base)
    if src is not None:
        return ('move', dest, src)
    if e.kind == 'bin':
        got = mathop(e, base)
        if got is not None:
            op, lreg, lval, rreg, rval = got
            if op in ('<', '>', '<=', '>=', '==', '~='):
                return ('cmp', dest, op, lreg, lval, rreg, rval)
            if op == 'and':
                return ('and', dest, lreg, lval, rreg, rval)
            if op == 'or':
                return ('or', dest, lreg, lval, rreg, rval)
            if op == '..':
                return ('concat', dest, lreg, lval, rreg, rval)
            if op in ('&', '|', '~', '<<', '>>'):
                return ('bits', dest, op, lreg, lval, rreg, rval)
            return ('math', dest, op, lreg, lval, rreg, rval)
    if e.kind == 'un':
        inner = slot(e.arg, base)
        val = number(e.arg)
        if e.op == 'not':
            return ('not', dest, inner, val)
        if e.op == '-':
            return ('neg', dest, inner, val)
        if e.op == '#':
            return ('len', dest, inner, val)
        if e.op == '~':
            return ('bitnot', dest, inner, val)
    if e.kind == 'idx':
        b = slot(e.base, base)
        k = slot(e.key, base)
        if b is not None and k is not None:
            return ('load', dest, b, k)
    if e.kind == 'call':
        got = callop(e, base)
        if got is not None:
            return ('call', dest, got[0], got[1])
        return ('call', dest, None, None)
    return None


def store(stmt, base):
    if stmt.kind != 'assign':
        return None
    if len(stmt.targets) != 1 or len(stmt.exprs) != 1:
        return None
    t = stmt.targets[0]
    e = stmt.exprs[0]
    if t.kind != 'idx' or t.base.kind != 'name' or t.base.name != base:
        return None
    k = slot(t.key, base)
    if k is None:
        return None
    src = slot(e, base)
    if src is not None:
        return ('save', k, src)
    return None


def tag(c, base):
    out = []
    for s in c.body:
        got = read(s, base)
        if got is not None:
            out.append(got)
            continue
        got = store(s, base)
        if got is not None:
            out.append(got)
            continue
        out.append(('raw', s))
    c.ops = out
    return c


def all(cells, base):
    for c in cells:
        tag(c, base)
    return cells
