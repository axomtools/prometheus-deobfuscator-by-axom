from node import node
from scan import scan

bind = {
    'or': (1, 1),
    'and': (2, 2),
    '<': (3, 3), '>': (3, 3), '<=': (3, 3), '>=': (3, 3),
    '~=': (3, 3), '==': (3, 3),
    '|': (4, 4),
    '~': (5, 5),
    '&': (6, 6),
    '<<': (7, 7), '>>': (7, 7),
    '..': (9, 8),
    '+': (10, 10), '-': (10, 10),
    '*': (11, 11), '/': (11, 11), '//': (11, 11), '%': (11, 11),
    '^': (14, 13),
}

class feed:
    def __init__(self, toks):
        self.toks = toks
        self.pos = 0

    def peek(self):
        return self.toks[self.pos]

    def next(self):
        item = self.toks[self.pos]
        self.pos += 1
        return item

    def far(self, off):
        idx = self.pos + off
        if idx < len(self.toks):
            return self.toks[idx]
        return self.toks[-1]

    def isop(self, word):
        item = self.peek()
        return item.kind in ('word', 'sym') and item.value == word

    def eat(self, word):
        if not self.isop(word):
            item = self.peek()
            raise SyntaxError('want %s got %s at line %s' % (word, item.value, item.line))
        return self.next()

    def call(self):
        item = self.peek()
        if item.kind != 'name':
            raise SyntaxError('want name got %s at line %s' % (item.value, item.line))
        self.next()
        return item.value


def parse(src):
    if isinstance(src, str):
        toks = scan(src)
    else:
        toks = src
    return block(feed(toks))


def block(reader):
    stmts = []
    while True:
        item = reader.peek()
        if item.kind == 'eof':
            break
        if item.kind == 'word' and item.value in ('end', 'else', 'elseif', 'until'):
            break
        if item.kind == 'sym' and item.value == ';':
            reader.next()
            continue
        if item.kind == 'word' and item.value == 'return':
            reader.next()
            exprs = []
            nxt = reader.peek()
            ok = nxt.kind == 'eof' or (nxt.kind == 'word' and nxt.value in ('end', 'else', 'elseif', 'until'))
            if not ok:
                exprs = list(reader)
            stmts.append(node('ret', exprs=exprs))
            break
        stmts.append(statement(reader))
    return node('blk', stmts=stmts)


def list(reader):
    items = [expr(reader)]
    while reader.isop(','):
        reader.next()
        items.append(expr(reader))
    return items


def expr(reader, limit=0):
    item = reader.peek()
    if item.kind == 'word' and item.value == 'not':
        reader.next()
        return node('un', op='not', arg=expr(reader, 11))
    if item.kind == 'sym' and item.value in ('-', '#', '~'):
        reader.next()
        return node('un', op=item.value, arg=expr(reader, 11))
    left = atom(reader)
    while True:
        item = reader.peek()
        if item.kind not in ('sym', 'word'):
            break
        pair = bind.get(item.value)
        if pair is None:
            break
        low, high = pair
        if low <= limit:
            break
        reader.next()
        right = expr(reader, high)
        left = node('bin', op=item.value, left=left, right=right)
    return left


def atom(reader):
    item = reader.peek()
    if item.kind == 'num':
        reader.next()
        return node('num', val=item.value)
    if item.kind == 'str':
        reader.next()
        return node('str', val=item.value)
    if item.kind == 'word':
        if item.value == 'nil':
            reader.next()
            return node('nil')
        if item.value == 'true':
            reader.next()
            return node('true')
        if item.value == 'false':
            reader.next()
            return node('false')
        if item.value == 'function':
            reader.next()
            return funcbody(reader)
    if item.kind == 'name':
        reader.next()
        return node('name', name=item.value)
    if item.kind == 'sym' and item.value == '...':
        reader.next()
        return node('dots')
    if item.kind == 'sym' and item.value == '(':
        reader.next()
        inner = expr(reader)
        reader.eat(')')
        return node('pare', exp=inner)
    if item.kind == 'sym' and item.value == '{':
        return maker(reader)
    raise SyntaxError('unexp %s at line %s' % (item.value, item.line))


def funcbody(reader):
    params = []
    reader.eat('(')
    if not reader.isop(')'):
        while True:
            if reader.isop('...'):
                reader.next()
                params.append('...')
                break
            params.append(reader.call())
            if not reader.isop(','):
                break
            reader.next()
    reader.eat(')')
    body = block(reader)
    reader.eat('end')
    return node('func', params=params, body=body)


def maker(reader):
    reader.eat('{')
    items = []
    while not reader.isop('}'):
        item = reader.peek()
        if item.kind == 'sym' and item.value == '[':
            reader.next()
            key = expr(reader)
            reader.eat(']')
            reader.eat('=')
            val = expr(reader)
            items.append(('key', key, val))
        elif item.kind == 'name' and reader.far(1).kind == 'sym' and reader.far(1).value == '=':
            name = reader.call()
            reader.eat('=')
            val = expr(reader)
            items.append(('key', node('str', val=name), val))
        else:
            items.append(('val', expr(reader)))
        if not (reader.isop(',') or reader.isop(';')):
            break
        reader.next()
    reader.eat('}')
    return node('table', items=items)


def prefix(reader):
    inner = atom(reader)
    while True:
        item = reader.peek()
        if item.kind == 'sym' and item.value == '.':
            reader.next()
            name = reader.call()
            inner = node('idx', base=inner, key=node('str', val=name))
            continue
        if item.kind == 'sym' and item.value == '[':
            reader.next()
            key = expr(reader)
            reader.eat(']')
            inner = node('idx', base=inner, key=key)
            continue
        if item.kind == 'sym' and item.value == ':':
            reader.next()
            name = reader.call()
            args = []
            if reader.isop('('):
                reader.next()
                if not reader.isop(')'):
                    args = list(reader)
                reader.eat(')')
            else:
                args = [tail(reader)]
            inner = node('mcall', base=inner, name=name, args=args)
            continue
        if item.kind == 'sym' and item.value == '(':
            reader.next()
            args = []
            if not reader.isop(')'):
                args = list(reader)
            reader.eat(')')
            inner = node('call', base=inner, args=args)
            continue
        if item.kind == 'sym' and item.value == '{':
            args = [maker(reader)]
            inner = node('call', base=inner, args=args)
            continue
        if item.kind == 'str':
            args = [atom(reader)]
            inner = node('call', base=inner, args=args)
            continue
        break
    return inner


def tail(reader):
    item = reader.peek()
    if item.kind == 'sym' and item.value == '{':
        return maker(reader)
    if item.kind == 'str':
        return atom(reader)
    return atom(reader)


def statement(reader):
    item = reader.peek()
    if item.kind == 'word':
        if item.value == 'local':
            reader.next()
            if reader.isop('function'):
                reader.next()
                name = reader.call()
                fb = funcbody(reader)
                return node('localfunc', name=name, params=fb.params, body=fb.body)
            names = [reader.call()]
            while reader.isop(','):
                reader.next()
                names.append(reader.call())
            exprs = []
            if reader.isop('='):
                reader.next()
                exprs = list(reader)
            return node('local', names=names, exprs=exprs)
        if item.value == 'function':
            reader.next()
            name = reader.call()
            fb = funcbody(reader)
            return node('funcstat', name=name, params=fb.params, body=fb.body)
        if item.value == 'if':
            reader.next()
            cond = expr(reader)
            reader.eat('then')
            body = block(reader)
            chains = []
            while reader.isop('elseif'):
                reader.next()
                c = expr(reader)
                reader.eat('then')
                chains.append((c, block(reader)))
            otherwise = None
            if reader.isop('else'):
                reader.next()
                otherwise = block(reader)
            reader.eat('end')
            return node('if', cond=cond, body=body, chains=chains, otherwise=otherwise)
        if item.value == 'while':
            reader.next()
            cond = expr(reader)
            reader.eat('do')
            body = block(reader)
            reader.eat('end')
            return node('while', cond=cond, body=body)
        if item.value == 'for':
            reader.next()
            first = reader.call()
            if reader.isop('='):
                reader.next()
                start = expr(reader)
                reader.eat(',')
                stop = expr(reader)
                step = None
                if reader.isop(','):
                    reader.next()
                    step = expr(reader)
                reader.eat('do')
                body = block(reader)
                reader.eat('end')
                return node('fornum', name=first, start=start, stop=stop, step=step, body=body)
            names = [first]
            while reader.isop(','):
                reader.next()
                names.append(reader.call())
            reader.eat('in')
            exprs = list(reader)
            reader.eat('do')
            body = block(reader)
            reader.eat('end')
            return node('forgen', names=names, exprs=exprs, body=body)
        if item.value == 'repeat':
            reader.next()
            body = block(reader)
            reader.eat('until')
            cond = expr(reader)
            return node('repeat', body=body, cond=cond)
        if item.value == 'do':
            reader.next()
            body = block(reader)
            reader.eat('end')
            return node('do', body=body)
        if item.value == 'return':
            reader.next()
            exprs = []
            nxt = reader.peek()
            ok = nxt.kind == 'eof' or (nxt.kind == 'word' and nxt.value in ('end', 'else', 'elseif', 'until'))
            if not ok:
                exprs = list(reader)
            return node('ret', exprs=exprs)
        if item.value == 'break':
            reader.next()
            return node('break')
        if item.value == 'continue':
            reader.next()
            return node('continue')
        if item.value == 'goto':
            reader.next()
            name = reader.call()
            return node('goto', name=name)
    if item.kind == 'sym' and item.value == '::':
        reader.next()
        name = reader.call()
        reader.eat('::')
        return node('label', name=name)
    head = prefix(reader)
    if reader.isop('=') or reader.isop(','):
        targets = [head]
        while reader.isop(','):
            reader.next()
            targets.append(prefix(reader))
        reader.eat('=')
        exprs = list(reader)
        return node('assign', targets=targets, exprs=exprs)
    return node('callstat', exp=head)
