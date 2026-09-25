from walker import walk


class cell:
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi
        self.body = []
        self.exit = []
        self.prev = []
        self.dom = set()
        self.head = None
        self.reads = set()
        self.writes = set()
        self.ops = []
        self.ir = []


def cond(n):
    if n.kind != 'if':
        return None
    c = n.cond
    if c.kind != 'bin':
        return None
    op = c.op
    if op not in ('>', '>=', '<', '<='):
        return None
    if c.left.kind == 'name' and c.right.kind == 'num':
        name = c.left.name
        try:
            val = int(c.right.val)
        except ValueError:
            return None
    elif c.right.kind == 'name' and c.left.kind == 'num':
        name = c.right.name
        try:
            val = int(c.left.val)
        except ValueError:
            return None
        op = {'>': '<', '<': '>', '>=': '<=', '<=': '>='}[op]
    else:
        return None
    return (name, op, val)


def jump(stmts, ip):
    out = []
    for s in stmts:
        if s.kind != 'assign':
            continue
        if len(s.targets) != 1 or len(s.exprs) != 1:
            continue
        t = s.targets[0]
        if t.kind != 'name' or t.name != ip:
            continue
        e = s.exprs[0]
        if e.kind == 'num':
            try:
                out.append(('go', int(e.val)))
            except ValueError:
                pass
        elif e.kind == 'bin' and e.op == 'or':
            a = e.left
            b = e.right
            if a.kind == 'bin' and a.op == 'and':
                x = a.right
                y = b
                if x.kind == 'num' and y.kind == 'num':
                    try:
                        out.append(('yes', int(x.val)))
                        out.append(('no', int(y.val)))
                    except ValueError:
                        pass
    return out


def walkrange(n, lo, hi, ip, out):
    if n.kind == 'blk':
        if len(n.stmts) == 1 and n.stmts[0].kind == 'if':
            walkrange(n.stmts[0], lo, hi, ip, out)
        else:
            c = cell(lo, hi)
            c.body = list(n.stmts)
            c.exit = jump(n.stmts, ip)
            out.append(c)
        return
    if n.kind != 'if':
        return
    p = cond(n)
    if p is None:
        c = cell(lo, hi)
        c.body = [n]
        out.append(c)
        return
    name, op, val = p
    if name != ip:
        c = cell(lo, hi)
        c.body = [n]
        out.append(c)
        return
    if op == '>':
        a_lo, a_hi = val + 1, hi
        b_lo, b_hi = lo, val
    elif op == '>=':
        a_lo, a_hi = val, hi
        b_lo, b_hi = lo, val - 1
    elif op == '<':
        a_lo, a_hi = lo, val - 1
        b_lo, b_hi = val, hi
    else:
        a_lo, a_hi = lo, val
        b_lo, b_hi = val + 1, hi
    walkrange(n.body, a_lo, a_hi, ip, out)
    if n.otherwise is not None:
        walkrange(n.otherwise, b_lo, b_hi, ip, out)


def find(tree):
    hits = []

    def visit(n):
        if n.kind != 'while':
            return
        if n.cond.kind != 'name':
            return
        if n.body.kind != 'blk':
            return
        if len(n.body.stmts) != 1:
            return
        hits.append((n.cond.name, n))

    walk(tree, visit)
    return hits


def build(tree):
    hits = find(tree)
    if not hits:
        return None
    ip, loop = hits[0]
    out = []
    walkrange(loop.body, 0, 1 << 60, ip, out)
    return ip, out
