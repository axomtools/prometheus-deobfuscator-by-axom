from printer import emit
from instructions import mnemonic


NAMES = {}


def build_names(cells, nodes):
    out = {}
    letters = 'ijklmnopqrstuvwxyz'
    used = [0]

    def walktree(node):
        if node.tag == 'loop' and hasattr(node, 'counter'):
            var = node.counter['var']
            if var not in out:
                idx = min(used[0], len(letters) - 1)
                out[var] = letters[idx]
                used[0] += 1

    for n in nodes or []:
        walktree(n)

    seen = set()
    for c in cells:
        for op in c.ir:
            for attr in ('reg', 'dest', 'to', 'fr', 'base', 'key', 'src', 'inner', 'arg'):
                v = getattr(op, attr, None)
                if v is not None:
                    seen.add(v)
            if hasattr(op, 'left') and op.left is not None:
                seen.add(op.left)
            if hasattr(op, 'right') and op.right is not None:
                seen.add(op.right)
    for n in sorted(seen):
        if n not in out:
            out[n] = 'r' + str(n)
    return out


def reg(n):
    return NAMES.get(n, 'r' + str(n))


def val(v):
    if v is None:
        return 'nil'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, str):
        esc = v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return '"' + esc + '"'
    return str(v)


def opnd(side_reg, side_val):
    if side_reg is not None:
        return reg(side_reg)
    return val(side_val)


def line(op):
    if op.tag == 'set':
        return reg(op.reg) + ' = ' + val(op.value)
    if op.tag == 'copy':
        return reg(op.to) + ' = ' + reg(op.fr)
    if op.tag == 'calc':
        left = opnd(op.left, op.leftv)
        right = opnd(op.right, op.rightv)
        return reg(op.dest) + ' = ' + left + ' ' + op.op + ' ' + right
    if op.tag == 'cmp':
        left = opnd(op.left, op.leftv)
        right = opnd(op.right, op.rightv)
        return reg(op.dest) + ' = ' + left + ' ' + op.op + ' ' + right
    if op.tag == 'and':
        return reg(op.dest) + ' = ' + opnd(op.left, op.leftv) + ' and ' + opnd(op.right, op.rightv)
    if op.tag == 'or':
        return reg(op.dest) + ' = ' + opnd(op.left, op.leftv) + ' or ' + opnd(op.right, op.rightv)
    if op.tag == 'not':
        return reg(op.dest) + ' = not ' + opnd(op.inner, op.inner_v)
    if op.tag == 'neg':
        return reg(op.dest) + ' = -' + opnd(op.inner, op.inner_v)
    if op.tag == 'len':
        return reg(op.dest) + ' = #' + opnd(op.inner, op.inner_v)
    if op.tag == 'bitnot':
        return reg(op.dest) + ' = ~' + opnd(op.inner, op.inner_v)
    if op.tag == 'concat':
        return reg(op.dest) + ' = ' + opnd(op.left, op.leftv) + ' .. ' + opnd(op.right, op.rightv)
    if op.tag == 'bits':
        return reg(op.dest) + ' = ' + opnd(op.left, op.leftv) + ' ' + op.op + ' ' + opnd(op.right, op.rightv)
    if op.tag == 'load':
        return reg(op.dest) + ' = ' + reg(op.base) + '[' + reg(op.key) + ']'
    if op.tag == 'save':
        return reg(op.base) + '[' + reg(op.key) + '] = ' + reg(op.src)
    if op.tag == 'call':
        arg = reg(op.arg) if op.arg is not None else ''
        name = op.name or 'f'
        if arg:
            return reg(op.dest) + ' = ' + name + '(' + arg + ')'
        return reg(op.dest) + ' = ' + name + '()'
    if op.tag == 'raw':
        return emit(op.stmt, 0, 0)
    return ''


def cond(c):
    if c is None:
        return 'true'
    if c.tag == 'cmp':
        left = opnd(c.left, c.leftv)
        right = opnd(c.right, c.rightv)
        return left + ' ' + c.op + ' ' + right
    return 'true'


def emit_cell(c, depth):
    pad = '  ' * depth
    lines = []
    for op in c.ir:
        row = line(op)
        if row:
            lines.append(pad + row)
    return lines


def emit_loop(node, cells, depth):
    pad = '  ' * depth
    lines = []
    if hasattr(node, 'counter'):
        cc = node.counter
        var = reg(cc['var'])
        step = cc['step']
        cmp = cc['cmp']
        if cmp.left == cc['var']:
            limit = opnd(cmp.right, cmp.rightv)
        else:
            limit = opnd(cmp.left, cmp.leftv)
        head = 'for ' + var + ' = ' + var + ', ' + limit
        if step != 1:
            head = head + ', ' + str(step)
        head = head + ' do'
        lines.append(pad + head)
        for c in node.body:
            for row in emit_cell(c, depth + 1):
                lines.append(row)
        lines.append(pad + 'end')
    else:
        head_cell = cells[node.at]
        c = None
        for op in reversed(head_cell.ir):
            if op.tag == 'cmp':
                c = op
                break
        lines.append(pad + 'while ' + cond(c) + ' do')
        for row in emit_cell(head_cell, depth + 1):
            lines.append(row)
        for cell in node.body:
            for row in emit_cell(cell, depth + 1):
                lines.append(row)
        lines.append(pad + 'end')
    return lines


def emit_branch(node, cells, depth):
    pad = '  ' * depth
    lines = []
    lines.append(pad + 'if ' + cond(node.cond) + ' then')
    for c in node.then_part:
        for row in emit_cell(c, depth + 1):
            lines.append(row)
    if node.else_part:
        lines.append(pad + 'else')
        for c in node.else_part:
            for row in emit_cell(c, depth + 1):
                lines.append(row)
    lines.append(pad + 'end')
    return lines


def structured(cells, ip, nodes):
    lines = []
    for node in nodes:
        if node.tag == 'loop':
            lines.extend(emit_loop(node, cells, 0))
        elif node.tag == 'branch':
            lines.extend(emit_branch(node, cells, 0))
        else:
            lines.extend(emit_cell(cells[node.at], 0))
    return '\n'.join(lines)


def flat(cells, ip):
    lines = []
    for i, c in enumerate(cells):
        depth = len(c.dom) - 1
        lines.extend(emit_cell(c, depth))
    return '\n'.join(lines)


def body(cells, ip, nodes):
    global NAMES
    NAMES = build_names(cells, nodes)
    used = sorted(NAMES.keys())
    head = 'local ' + ', '.join(NAMES[n] for n in used)
    if nodes:
        return head + '\n' + structured(cells, ip, nodes)
    return head + '\n' + flat(cells, ip)


def disassemble(cells, ip):
    lines = []
    lines.append('dispatcher ip: %s' % ip)
    lines.append('blocks: %d' % len(cells))
    lines.append('')
    pc = 0
    for i, c in enumerate(cells):
        head = ''
        if c.head is not None:
            head = ' head=%d' % c.head
        depth = len(c.dom) - 1
        lines.append('block %d  [%d..%d]  depth=%d%s' % (i, c.lo, c.hi, depth, head))
        for op in c.ir:
            parts = mnemonic(op)
            mnem = parts[0]
            args = ' '.join(parts[1:])
            lines.append('  %04d  %-10s %s' % (pc, mnem, args))
            pc += 1
        for kind, target in c.exit:
            j = None
            for k, cc in enumerate(cells):
                if cc.lo <= target <= cc.hi:
                    j = k
                    break
            if j is not None:
                lines.append('        %-10s -> block %d (%d)' % (kind.upper(), j, target))
            else:
                lines.append('        %-10s -> %d' % (kind.upper(), target))
        lines.append('')
    return '\n'.join(lines)
