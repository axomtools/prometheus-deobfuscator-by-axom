class item:
    def __init__(self, tag, **kw):
        self.tag = tag
        self.__dict__.update(kw)


opnames = {
    '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '//': 'IDIV', '%': 'MOD', '^': 'POW',
    '<': 'LT', '>': 'GT', '<=': 'LE', '>=': 'GE', '==': 'EQ', '~=': 'NE',
    '&': 'BAND', '|': 'BOR', '~': 'BXOR', '<<': 'SHL', '>>': 'SHR',
    'and': 'AND', 'or': 'OR', '..': 'CONCAT',
}


def const(v):
    if v is None:
        return 'nil'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, str):
        return repr(v)
    return str(v)


def mnemonic(op):
    if op.tag == 'set':
        return ('LOADK', 'R%d' % op.reg, const(op.value))
    if op.tag == 'copy':
        return ('MOVE', 'R%d' % op.to, 'R%d' % op.fr)
    if op.tag == 'calc':
        name = opnames.get(op.op, 'BINOP')
        hask = (op.left is None and op.leftv is not None) or (op.right is None and op.rightv is not None)
        if hask:
            name = name + 'K'
        left = 'R%d' % op.left if op.left is not None else const(op.leftv)
        right = 'R%d' % op.right if op.right is not None else const(op.rightv)
        return (name, 'R%d' % op.dest, left, right)
    if op.tag == 'cmp':
        name = opnames.get(op.op, 'CMP')
        return (name, 'R%d' % op.dest)
    if op.tag == 'load':
        return ('GETTABLE', 'R%d' % op.dest, 'R%d' % op.base, 'R%d' % op.key)
    if op.tag == 'save':
        return ('SETTABLE', 'R%d' % op.base, 'R%d' % op.key, 'R%d' % op.src)
    if op.tag == 'call':
        return ('CALL', 'R%d' % op.dest)
    if op.tag == 'and':
        return ('AND', 'R%d' % op.dest)
    if op.tag == 'or':
        return ('OR', 'R%d' % op.dest)
    if op.tag == 'not':
        return ('NOT', 'R%d' % op.dest)
    if op.tag == 'neg':
        return ('UNM', 'R%d' % op.dest)
    if op.tag == 'len':
        return ('LEN', 'R%d' % op.dest)
    if op.tag == 'bitnot':
        return ('BNOT', 'R%d' % op.dest)
    if op.tag == 'concat':
        return ('CONCAT', 'R%d' % op.dest)
    if op.tag == 'bits':
        name = opnames.get(op.op, 'BINOP')
        return (name, 'R%d' % op.dest)
    if op.tag == 'raw':
        return ('RAW',)
    return ('UNK',)


def build(cells, ip):
    for i, c in enumerate(cells):
        ops = []
        for op in getattr(c, 'ops', []):
            kind = op[0]
            if kind == 'const':
                ops.append(item('set', reg=op[1], value=op[2]))
            elif kind == 'move':
                ops.append(item('copy', to=op[1], fr=op[2]))
            elif kind == 'math':
                ops.append(item('calc', dest=op[1], op=op[2], left=op[3], right=op[5], leftv=op[4], rightv=op[6]))
            elif kind == 'cmp':
                ops.append(item('cmp', dest=op[1], op=op[2], left=op[3], leftv=op[4], right=op[5], rightv=op[6]))
            elif kind == 'and':
                ops.append(item('and', dest=op[1], left=op[2], leftv=op[3], right=op[4], rightv=op[5]))
            elif kind == 'or':
                ops.append(item('or', dest=op[1], left=op[2], leftv=op[3], right=op[4], rightv=op[5]))
            elif kind == 'not':
                ops.append(item('not', dest=op[1], inner=op[2], inner_v=op[3]))
            elif kind == 'neg':
                ops.append(item('neg', dest=op[1], inner=op[2], inner_v=op[3]))
            elif kind == 'len':
                ops.append(item('len', dest=op[1], inner=op[2], inner_v=op[3]))
            elif kind == 'bitnot':
                ops.append(item('bitnot', dest=op[1], inner=op[2], inner_v=op[3]))
            elif kind == 'concat':
                ops.append(item('concat', dest=op[1], left=op[2], leftv=op[3], right=op[4], rightv=op[5]))
            elif kind == 'bits':
                ops.append(item('bits', dest=op[1], op=op[2], left=op[3], right=op[5], leftv=op[4], rightv=op[6]))
            elif kind == 'load':
                ops.append(item('load', dest=op[1], base=op[2], key=op[3]))
            elif kind == 'save':
                ops.append(item('save', base=None, key=op[1], src=op[2]))
            elif kind == 'call':
                ops.append(item('call', dest=op[1], name=op[2], arg=op[3]))
            else:
                ops.append(item('raw', stmt=op[1]))
        c.ir = ops
    return cells
