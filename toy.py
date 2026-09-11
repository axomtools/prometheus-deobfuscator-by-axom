import math

class fall(Exception):
    pass


class jump(Exception):
    def __init__(self, what, args=None):
        self.what = what
        self.args = args or []


class space:
    def __init__(self, up=None):
        self.map = {}
        self.up = up

    def grab(self, key):
        s = self
        while s is not None:
            if key in s.map:
                return s.map[key]
            s = s.up
        raise KeyError(key)

    def make(self, key, val):
        self.map[key] = val

    def put(self, key, val):
        s = self
        while s is not None:
            if key in s.map:
                s.map[key] = val
                return
            s = s.up
        self.map[key] = val


def fchar(args):
    return ''.join(chr(int(a) & 0xFF) for a in args)


def fbyte(args):
    s = args[0]
    i = int(args[1]) if len(args) > 1 else 1
    j = int(args[2]) if len(args) > 2 else i
    if i < 0:
        i = len(s) + i + 1
    if j < 0:
        j = len(s) + j + 1
    got = [ord(c) for c in s[i - 1:j]]
    if len(args) <= 1:
        return got[0] if got else None
    return got


def fsub(args):
    s = args[0]
    i = int(args[1]) if len(args) > 1 else 1
    j = int(args[2]) if len(args) > 2 else len(s)
    if i < 0:
        i = max(len(s) + i + 1, 1)
    if j < 0:
        j = len(s) + j + 1
    i = max(i, 1)
    j = min(j, len(s))
    if i > j:
        return ''
    return s[i - 1:j]


def frep(args):
    s = args[0]
    n = int(args[1]) if len(args) > 1 else 1
    sep = args[2] if len(args) > 2 else ''
    if n <= 0:
        return ''
    return sep.join([s] * n)


def frev(args):
    return args[0][::-1]


def flen(args):
    return len(args[0])


def flow(args):
    return args[0].lower()


def fup(args):
    return args[0].upper()


def ffmt(args):
    fmt = args[0]
    rest = list(args[1:])
    out = []
    i = 0
    ai = 0
    while i < len(fmt):
        c = fmt[i]
        if c == '%' and i + 1 < len(fmt):
            j = i + 1
            while j < len(fmt) and fmt[j] in '-+ #0123456789.':
                j += 1
            if j < len(fmt):
                spec = fmt[j]
                if spec == '%':
                    out.append('%')
                elif spec in 'di':
                    out.append(str(int(rest[ai])))
                    ai += 1
                elif spec == 's':
                    out.append(str(rest[ai]))
                    ai += 1
                elif spec == 'f':
                    out.append(str(float(rest[ai])))
                    ai += 1
                elif spec == 'x':
                    out.append('%x' % int(rest[ai]))
                    ai += 1
                elif spec == 'X':
                    out.append('%X' % int(rest[ai]))
                    ai += 1
                else:
                    out.append(fmt[i:j + 1])
                i = j + 1
                continue
        out.append(c)
        i += 1
    return ''.join(out)


def fcat(args):
    t = args[0]
    sep = args[1] if len(args) > 1 else ''
    i = int(args[2]) if len(args) > 2 else 1
    j = int(args[3]) if len(args) > 3 else len(t)
    out = []
    for x in t[i - 1:j]:
        if x is not None:
            out.append(str(x))
    return sep.join(out)


def fbxor(args):
    r = 0
    for a in args:
        r = r ^ int(a)
    return r & 0xFFFFFFFF


def fband(args):
    r = args[0]
    for a in args[1:]:
        r = r & a
    return r & 0xFFFFFFFF


def fbor(args):
    r = 0
    for a in args:
        r = r | int(a)
    return r & 0xFFFFFFFF


def fbnot(args):
    return (~int(args[0])) & 0xFFFFFFFF


def fls(args):
    return (int(args[0]) << int(args[1])) & 0xFFFFFFFF


def frs(args):
    return (int(args[0]) & 0xFFFFFFFF) >> int(args[1])


def fpairs(args):
    t = args[0]
    if isinstance(t, dict):
        keys = list(t.keys())
    else:
        keys = list(range(1, len(t) + 1))
    state = {'i': 0, 'keys': keys, 't': t}

    def iterfn(s, ctrl=None):
        i = s['i']
        if i >= len(s['keys']):
            return None
        kk = s['keys'][i]
        s['i'] = i + 1
        vv = s['t'][kk] if isinstance(s['t'], dict) else s['t'][kk - 1]
        return (kk, vv)

    return (iterfn, state, None)


def fipairs(args):
    t = args[0]
    state = {'i': 0, 't': t}

    def iterfn(s, ctrl=None):
        i = s['i']
        if i >= len(s['t']):
            return None
        s['i'] = i + 1
        return (i + 1, s['t'][i])

    return (iterfn, state, None)


def mfloor(args):
    return math.floor(args[0])


def mceil(args):
    return math.ceil(args[0])


def mabs(args):
    return abs(args[0])


def mmax(args):
    return max(args)


def mmin(args):
    return min(args)


libs = {
    'string': {
        'char': fchar, 'byte': fbyte, 'sub': fsub,
        'rep': frep, 'reverse': frev, 'len': flen,
        'lower': flow, 'upper': fup, 'format': ffmt,
    },
    'table': {'concat': fcat},
    'math': {
        'floor': mfloor, 'ceil': mceil, 'abs': mabs,
        'max': mmax, 'min': mmin,
    },
    'bit': {
        'bxor': fbxor, 'band': fband, 'bor': fbor, 'bnot': fbnot,
        'lshift': fls, 'rshift': frs, 'arshift': frs,
    },
    'bit32': {
        'bxor': fbxor, 'band': fband, 'bor': fbor, 'bnot': fbnot,
        'lshift': fls, 'rshift': frs, 'arshift': frs,
    },
}


def load(env):
    env.make('pairs', fpairs)
    env.make('ipairs', fipairs)
    for name, lib in libs.items():
        env.make(name, lib)


def run(body, env, budget):
    for stmt in body.stmts:
        one(stmt, env, budget)
    return None


def one(n, env, budget):
    budget[0] -= 1
    if budget[0] < 0:
        raise fall('budget')
    kind = n.kind
    if kind == 'local':
        vals = [grab(e, env, budget) for e in n.exprs]
        while len(vals) < len(n.names):
            vals.append(None)
        for nm, vl in zip(n.names, vals):
            env.make(nm, vl)
        return
    if kind == 'assign':
        vals = [grab(e, env, budget) for e in n.exprs]
        while len(vals) < len(n.targets):
            vals.append(None)
        for tgt, vl in zip(n.targets, vals):
            if tgt.kind == 'name':
                env.put(tgt.name, vl)
            elif tgt.kind == 'idx':
                base = grab(tgt.base, env, budget)
                kk = grab(tgt.key, env, budget)
                if isinstance(base, list):
                    base[int(kk) - 1] = vl
                elif isinstance(base, dict):
                    base[kk] = vl
            else:
                raise fall('assign')
        return
    if kind == 'ret':
        vals = [grab(e, env, budget) for e in n.exprs]
        raise jump('return', vals)
    if kind == 'if':
        if grab(n.cond, env, budget):
            run(n.body, env, budget)
        else:
            done = False
            for cond, body in n.chains:
                if grab(cond, env, budget):
                    run(body, env, budget)
                    done = True
                    break
            if not done and n.otherwise is not None:
                run(n.otherwise, env, budget)
        return
    if kind == 'while':
        while grab(n.cond, env, budget):
            try:
                run(n.body, env, budget)
            except jump as j:
                if j.what == 'break':
                    break
                if j.what == 'continue':
                    continue
                raise
        return
    if kind == 'fornum':
        a = grab(n.start, env, budget)
        b = grab(n.stop, env, budget)
        c = grab(n.step, env, budget) if n.step is not None else 1
        x = a
        while (c > 0 and x <= b) or (c < 0 and x >= b):
            env.make(n.name, x)
            try:
                run(n.body, env, budget)
            except jump as j:
                if j.what == 'break':
                    break
                if j.what == 'continue':
                    x = x + c
                    continue
                raise
            x = x + c
        return
    if kind == 'forgen':
        vals = [grab(e, env, budget) for e in n.exprs]
        if not vals or not callable(vals[0]):
            raise fall('for')
        it = vals[0]
        st = vals[1] if len(vals) > 1 else None
        ctrl = vals[2] if len(vals) > 2 else None
        while True:
            got = it(st, ctrl)
            if got is None:
                break
            if isinstance(got, tuple):
                for nm, vv in zip(n.names, got):
                    env.make(nm, vv)
            else:
                env.make(n.names[0], got)
            try:
                run(n.body, env, budget)
            except jump as j:
                if j.what == 'break':
                    break
                if j.what == 'continue':
                    continue
                raise
        return
    if kind == 'break':
        raise jump('break')
    if kind == 'continue':
        raise jump('continue')
    if kind == 'do':
        run(n.body, env, budget)
        return
    if kind == 'callstat':
        grab(n.exp, env, budget)
        return
    raise fall('stmt ' + kind)


def grab(n, env, budget):
    budget[0] -= 1
    if budget[0] < 0:
        raise fall('budget')
    kind = n.kind
    if kind == 'num':
        if n.val.startswith('0x') or n.val.startswith('0X'):
            return int(n.val, 16)
        if '.' in n.val or 'e' in n.val or 'E' in n.val:
            return float(n.val)
        return int(n.val)
    if kind == 'str':
        return n.val
    if kind == 'nil':
        return None
    if kind == 'true':
        return True
    if kind == 'false':
        return False
    if kind == 'name':
        return env.grab(n.name)
    if kind == 'pare':
        return grab(n.exp, env, budget)
    if kind == 'bin':
        return two(n, env, budget)
    if kind == 'un':
        return oneop(n, env, budget)
    if kind == 'idx':
        base = grab(n.base, env, budget)
        kk = grab(n.key, env, budget)
        if isinstance(base, list):
            i = int(kk)
            if i < 0:
                i = len(base) + i + 1
            if 1 <= i <= len(base):
                return base[i - 1]
            return None
        if isinstance(base, dict):
            return base.get(kk)
        if isinstance(base, str):
            i = int(kk)
            if i < 0:
                i = len(base) + i + 1
            if 1 <= i <= len(base):
                return base[i - 1]
            return None
        raise fall('idx')
    if kind == 'call':
        return docall(n, env, budget)
    if kind == 'mcall':
        base = grab(n.base, env, budget)
        args = [grab(a, env, budget) for a in n.args]
        if isinstance(base, dict):
            fn = base.get(n.name)
            if callable(fn):
                return fn(args)
        raise fall('mcall')
    if kind == 'table':
        return dotable(n, env, budget)
    if kind == 'func':
        return ('func', n, env)
    raise fall('grab ' + kind)


def two(n, env, budget):
    op = n.op
    if op == 'and':
        a = grab(n.left, env, budget)
        if not a:
            return a
        return grab(n.right, env, budget)
    if op == 'or':
        a = grab(n.left, env, budget)
        if a:
            return a
        return grab(n.right, env, budget)
    a = grab(n.left, env, budget)
    b = grab(n.right, env, budget)
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    if op == '*':
        return a * b
    if op == '/':
        return a / b
    if op == '//':
        return a // b
    if op == '%':
        return a % b
    if op == '^':
        return a ** b
    if op == '..':
        return str(a) + str(b)
    if op == '==':
        return a == b
    if op == '~=':
        return a != b
    if op == '<':
        return a < b
    if op == '>':
        return a > b
    if op == '<=':
        return a <= b
    if op == '>=':
        return a >= b
    if op == '&':
        return int(a) & int(b)
    if op == '|':
        return int(a) | int(b)
    if op == '~':
        return int(a) ^ int(b)
    if op == '<<':
        return int(a) << int(b)
    if op == '>>':
        return int(a) >> int(b)
    raise fall('bin ' + op)


def oneop(n, env, budget):
    op = n.op
    if op == 'not':
        return not grab(n.arg, env, budget)
    a = grab(n.arg, env, budget)
    if op == '-':
        return -a
    if op == '#':
        if isinstance(a, (str, list, dict)):
            return len(a)
        raise fall('len')
    if op == '~':
        return int(~a)
    raise fall('un ' + op)


def docall(n, env, budget):
    if n.base.kind == 'name':
        nm = n.base.name
        args = [grab(a, env, budget) for a in n.args]
        try:
            val = env.grab(nm)
        except KeyError:
            raise fall('call ' + nm)
        return fire(val, args, budget)
    if n.base.kind == 'idx':
        base = grab(n.base.base, env, budget)
        kk = grab(n.base.key, env, budget)
        args = [grab(a, env, budget) for a in n.args]
        if isinstance(base, dict):
            fn = base.get(kk)
            if callable(fn):
                return fn(args)
        raise fall('call idx')
    raise fall('call')


def fire(val, args, budget):
    if callable(val):
        return val(args)
    if isinstance(val, tuple) and val[0] == 'func':
        return runclosure(val[1], val[2], args, budget)
    raise fall('fire')


def runclosure(fn, closenv, args, budget):
    inner = space(closenv)
    for i, p in enumerate(fn.params):
        if p == '...':
            inner.make('...', list(args[i:]))
            break
        inner.make(p, args[i] if i < len(args) else None)
    try:
        run(fn.body, inner, budget)
    except jump as j:
        if j.what == 'return':
            if j.args:
                return j.args[0]
            return None
        raise
    return None


def dotable(n, env, budget):
    array = []
    extra = {}
    for entry in n.items:
        if entry[0] == 'key':
            kk = grab(entry[1], env, budget)
            extra[kk] = grab(entry[2], env, budget)
        else:
            array.append(grab(entry[1], env, budget))
    if extra:
        if all(isinstance(x, int) and x > 0 for x in extra):
            size = max(extra)
            while len(array) < size:
                array.append(None)
            for kk, vl in extra.items():
                if kk - 1 < len(array):
                    array[kk - 1] = vl
                else:
                    array.append(vl)
            return array
        d = dict(extra)
        for i, v in enumerate(array):
            d[i + 1] = v
        return d
    return array
