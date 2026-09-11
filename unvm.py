from step import walk


def tally(node):
    if node.kind != 'table':
        return {'str': 0, 'num': 0, 'total': 0}
    counts = {'str': 0, 'num': 0, 'total': 0}
    for entry in node.items:
        if entry[0] == 'key':
            value = entry[2]
        else:
            value = entry[1]
        counts['total'] += 1
        if value.kind == 'str':
            counts['str'] += 1
        elif value.kind == 'num':
            counts['num'] += 1
    return counts


def strings(node):
    out = []
    for entry in node.items:
        if entry[0] == 'key':
            value = entry[2]
        else:
            value = entry[1]
        if value.kind == 'str':
            out.append(value.val)
    return out


def numbers(node):
    out = []
    for entry in node.items:
        if entry[0] != 'val':
            return None
        value = entry[1]
        if value.kind != 'num':
            return None
        try:
            out.append(int(value.val))
        except ValueError:
            return None
    return out


def program(node):
    vals = numbers(node)
    if vals is None:
        return None
    if len(vals) < 40:
        return None
    small = sum(1 for v in vals if 0 <= v <= 90)
    if small < len(vals) * 0.7:
        return None
    return vals


def review(tree):
    report = {
        'strings': [],
        'program': [],
        'notes': [],
    }

    def visit(node):
        if node.kind != 'local':
            return
        for name, expr in zip(node.names, node.exprs):
            if expr.kind != 'table':
                continue
            counts = tally(expr)
            if counts['str'] >= 20 and counts['str'] >= counts['num']:
                report['strings'] = strings(expr)
                report['notes'].append('string table at ' + name)
            prog = program(expr)
            if prog is not None:
                report['program'] = prog
                report['notes'].append('program table at ' + name)

    walk(tree, visit)
    return report


def dump(tree):
    return review(tree)
