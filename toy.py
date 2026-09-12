import math
from node import node

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


def finsert(args):
    t = args[0]
    if isinstance(t, list):
        if len(args) == 2:
            t.append(args[1])
            return len(t)
        if len(args) == 3:
            pos = int(args[1])
            t.insert(pos - 1, args[2])
            return len(t)
    return None


def ftype(args):
    v = args[0]
    if v is None:
        return 'nil'
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, (int, float)):
        return 'number'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, (list, dict)):
        return 'table'
    if callable(v):
        return 'function'
    if isinstance(v, tuple) and v and v[0] == 'func':
        return 'function'
    return 'userdata'


def ftostring(args):
    v = args[0]
    if v is None:
        return 'nil'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    return str(v)


def ftonumber(args):
    v = args[0]
    if isinstance(v, (int, float)):
        return v
    try:
        return int(v)
    except (ValueError, TypeError):
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


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


def fselect(args):
    n = args[0]
    rest = list(args[1:])
    if n == '#':
        return len(rest)
    if isinstance(n, int):
        if n < 0:
            n = len(rest) + n + 1
        return rest[n - 1] if 1 <= n <= len(rest) else None
    return rest


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
    'table': {'concat': fcat, 'insert': finsert},
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
    env.make('type', ftype)
    env.make('tostring', ftostring)
    env.make('tonumber', ftonumber)
    env.make('select', fselect)
    for name, lib in libs.items():
        env.make(name, lib)


def multi(e, env, budget):
    v = grab(e, env, budget)
    if isinstance(v, tuple):
        return list(v)
    return [v]


def spread(exprs, env, budget):
    out = []
    total = len(exprs)
    for i, e in enumerate(exprs):
        part = multi(e, env, budget)
        if i < total - 1:
            out.append(part[0] if part else None)
        else:
            out.extend(part)
    return out


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
        vals = spread(n.exprs, env, budget)
        while len(vals) < len(n.names):
            vals.append(None)
        for nm, vl in zip(n.names, vals):
            env.make(nm, vl)
        return
    if kind == 'localfunc':
        fn = node('func', params=n.params, body=n.body)
        env.make(n.name, ('func', fn, env))
        return
    if kind == 'funcstat':
        fn = node('func', params=n.params, body=n.body)
        env.put(n.name, ('func', fn, env))
        return
    if kind == 'assign':
        infos = []
        for tgt in n.targets:
            if tgt.kind == 'name':
                infos.append(('name', tgt.name, None, None))
            elif tgt.kind == 'idx':
                base = grab(tgt.base, env, budget)
                kk = grab(tgt.key, env, budget)
                infos.append(('idx', None, base, kk))
            else:
                raise fall('assign target')
        vals = spread(n.exprs, env, budget)
        while len(vals) < len(infos):
            vals.append(None)
        for info, vl in zip(infos, vals):
            if info[0] == 'name':
                env.put(info[1], vl)
            else:
                base = info[2]
                kk = info[3]
                if isinstance(base, list):
                    i = int(kk)
                    if i < 1:
                        i = len(base) + i + 1
                    while len(base) < i:
                        base.append(None)
                    base[i - 1] = vl
                elif isinstance(base, dict):
                    base[kk] = vl
        return
    if kind == 'ret':
        vals = [grab(e, env, budget) for e in n.exprs]
        raise jump('return', vals)
    if kind == 'if':
        if grab(n.cond, env, budget):
            inner = space(env)
            run(n.body, inner, budget)
        else:
            done = False
            for cond, body in n.chains:
                if grab(cond, env, budget):
                    inner = space(env)
                    run(body, inner, budget)
                    done = True
                    break
            if not done and n.otherwise is not None:
                inner = space(env)
                run(n.otherwise, inner, budget)
        return
    if kind == 'while':
        while grab(n.cond, env, budget):
            inner = space(env)
            try:
                run(n.body, inner, budget)
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
        if not isinstance(a, (int, float)):
            raise fall('fornum start')
        if not isinstance(b, (int, float)):
            raise fall('fornum stop')
        if not isinstance(c, (int, float)):
            raise fall('fornum step')
        x = a
        while (c > 0 and x <= b) or (c < 0 and x >= b):
            inner = space(env)
            inner.make(n.name, x)
            try:
                run(n.body, inner, budget)
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
        vals = spread(n.exprs, env, budget)
        if not vals or not callable(vals[0]):
            raise fall('forgen')
        it = vals[0]
        st = vals[1] if len(vals) > 1 else None
        ctrl = vals[2] if len(vals) > 2 else None
        while True:
            got = it(st, ctrl)
            if got is None:
                break
            inner = space(env)
            if isinstance(got, tuple):
                for nm, vv in zip(n.names, got):
                    inner.make(nm, vv)
                ctrl = got[0] if got else None
            else:
                inner.make(n.names[0], got)
                ctrl = got
            try:
                run(n.body, inner, budget)
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
        inner = space(env)
        run(n.body, inner, budget)
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
    if kind == 'ifexp':
        if grab(n.cond, env, budget):
            return grab(n.yes, env, budget)
        return grab(n.no, env, budget)
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
    if isinstance(val, tuple) and val and val[0] == 'func':
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
