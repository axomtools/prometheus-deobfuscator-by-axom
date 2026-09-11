import re
from scan import words

ident = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

rank = {
    'or': 1, 'and': 2,
    '<': 3, '>': 3, '<=': 3, '>=': 3, '~=': 3, '==': 3,
    '|': 4, '~': 5, '&': 6, '<<': 7, '>>': 7,
    '..': 8, '+': 9, '-': 9,
    '*': 10, '/': 10, '//': 10, '%': 10,
    '^': 12,
}

right = {'..', '^'}


def escape(text):
    out = []
    for c in text:
        if c == '\\':
            out.append('\\\\')
        elif c == '"':
            out.append('\\"')
        elif c == '\n':
            out.append('\\n')
        elif c == '\r':
            out.append('\\r')
        elif c == '\t':
            out.append('\\t')
        elif c == '\0':
            out.append('\\0')
        elif ord(c) < 32:
            out.append('\\' + str(ord(c)))
        else:
            out.append(c)
    return ''.join(out)


def short(text):
    return ident.match(text) and text not in words


def emit(tree, depth=0, limit=0):
    pad = '  ' * depth
    kind = tree.kind
    if kind == 'blk':
        return '\n'.join(emit(s, depth, 0) for s in tree.stmts)
    if kind == 'ret':
        if not tree.exprs:
            return pad + 'return'
        return pad + 'return ' + ', '.join(emit(e, 0, 0) for e in tree.exprs)
    if kind == 'local':
        text = pad + 'local ' + ', '.join(tree.names)
        if tree.exprs:
            text += ' = ' + ', '.join(emit(e, 0, 0) for e in tree.exprs)
        return text
    if kind == 'localfunc':
        head = pad + 'local function ' + tree.name + '(' + ', '.join(tree.params) + ')'
        return head + '\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
    if kind == 'funcstat':
        head = pad + 'function ' + tree.name + '(' + ', '.join(tree.params) + ')'
        return head + '\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
    if kind == 'assign':
        return pad + ', '.join(emit(t, 0, 0) for t in tree.targets) + ' = ' + ', '.join(emit(e, 0, 0) for e in tree.exprs)
    if kind == 'callstat':
        return pad + emit(tree.exp, 0, 0)
    if kind == 'if':
        text = pad + 'if ' + emit(tree.cond, 0, 0) + ' then\n' + emit(tree.body, depth + 1, 0)
        for cond, body in tree.chains:
            text += '\n' + pad + 'elseif ' + emit(cond, 0, 0) + ' then\n' + emit(body, depth + 1, 0)
        if tree.otherwise is not None:
            text += '\n' + pad + 'else\n' + emit(tree.otherwise, depth + 1, 0)
        text += '\n' + pad + 'end'
        return text
    if kind == 'ifexp':
        text = 'if ' + emit(tree.cond, 0, 0) + ' then ' + emit(tree.yes, 0, 0) + ' else ' + emit(tree.no, 0, 0)
        if 1 < limit:
            return '(' + text + ')'
        return text
    if kind == 'while':
        return pad + 'while ' + emit(tree.cond, 0, 0) + ' do\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
    if kind == 'fornum':
        text = pad + 'for ' + tree.name + ' = ' + emit(tree.start, 0, 0) + ', ' + emit(tree.stop, 0, 0)
        if tree.step is not None:
            text += ', ' + emit(tree.step, 0, 0)
        text += ' do\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
        return text
    if kind == 'forgen':
        return pad + 'for ' + ', '.join(tree.names) + ' in ' + ', '.join(emit(e, 0, 0) for e in tree.exprs) + ' do\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
    if kind == 'repeat':
        return pad + 'repeat\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'until ' + emit(tree.cond, 0, 0)
    if kind == 'do':
        return pad + 'do\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
    if kind == 'break':
        return pad + 'break'
    if kind == 'continue':
        return pad + 'continue'
    if kind == 'label':
        return pad + '::' + tree.name + '::'
    if kind == 'goto':
        return pad + 'goto ' + tree.name
    if kind == 'num':
        return tree.val
    if kind == 'str':
        return '"' + escape(tree.val) + '"'
    if kind == 'nil':
        return 'nil'
    if kind == 'true':
        return 'true'
    if kind == 'false':
        return 'false'
    if kind == 'dots':
        return '...'
    if kind == 'name':
        return tree.name
    if kind == 'bin':
        p = rank[tree.op]
        if tree.op in right:
            left = emit(tree.left, 0, p + 1)
            other = emit(tree.right, 0, p)
        else:
            left = emit(tree.left, 0, p)
            other = emit(tree.right, 0, p + 1)
        text = left + ' ' + tree.op + ' ' + other
        if p < limit:
            return '(' + text + ')'
        return text
    if kind == 'un':
        p = 11
        text = tree.op + (' ' if tree.op == 'not' else '') + emit(tree.arg, 0, p)
        if p < limit:
            return '(' + text + ')'
        return text
    if kind == 'func':
        head = 'function(' + ', '.join(tree.params) + ')'
        return head + '\n' + emit(tree.body, depth + 1, 0) + '\n' + pad + 'end'
    if kind == 'table':
        parts = []
        for entry in tree.items:
            if entry[0] == 'key':
                kk = entry[1]
                if kk.kind == 'str' and short(kk.val):
                    parts.append(kk.val + ' = ' + emit(entry[2], 0, 0))
                else:
                    parts.append('[' + emit(kk, 0, 0) + '] = ' + emit(entry[2], 0, 0))
            else:
                parts.append(emit(entry[1], 0, 0))
        return '{' + ', '.join(parts) + '}'
    if kind == 'idx':
        if tree.key.kind == 'str' and short(tree.key.val):
            text = emit(tree.base, 0, 13) + '.' + tree.key.val
        else:
            text = emit(tree.base, 0, 13) + '[' + emit(tree.key, 0, 0) + ']'
        if 13 < limit:
            return '(' + text + ')'
        return text
    if kind == 'call':
        text = emit(tree.base, 0, 13) + '(' + ', '.join(emit(a, 0, 0) for a in tree.args) + ')'
        if 13 < limit:
            return '(' + text + ')'
        return text
    if kind == 'mcall':
        text = emit(tree.base, 0, 13) + ':' + tree.name + '(' + ', '.join(emit(a, 0, 0) for a in tree.args) + ')'
        if 13 < limit:
            return '(' + text + ')'
        return text
    if kind == 'pare':
        return '(' + emit(tree.exp, 0, 0) + ')'
    return ''
