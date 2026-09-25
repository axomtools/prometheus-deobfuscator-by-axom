from controlflow import at


class tree:
    def __init__(self, tag, **kw):
        self.tag = tag
        self.__dict__.update(kw)


def back(cells):
    out = []
    for i, c in enumerate(cells):
        for kind, target in c.exit:
            j = at(cells, target)
            if j is None or j == i:
                continue
            if j in c.dom:
                out.append((j, i, kind))
    return out


def inside(cells, head, latches):
    found = set([head])
    stack = list(latches)
    while stack:
        n = stack.pop()
        if n in found:
            continue
        found.add(n)
        for kind, p in cells[n].prev:
            if p not in found:
                stack.append(p)
    return found


def two_way(cells, i):
    exits = cells[i].exit
    kinds = [k for k, a in exits]
    if len(exits) != 2:
        return None
    if 'yes' not in kinds or 'no' not in kinds:
        return None
    yes = None
    no = None
    for kind, target in exits:
        j = at(cells, target)
        if kind == 'yes':
            yes = j
        elif kind == 'no':
            no = j
    if yes is None or no is None:
        return None
    return (yes, no)


def reaches(cells, start, stop=None):
    seen = set()
    stack = [start]
    while stack:
        n = stack.pop()
        if n in seen or n == stop:
            continue
        seen.add(n)
        for kind, target in cells[n].exit:
            j = at(cells, target)
            if j is not None and j != stop:
                stack.append(j)
    return seen


def lastcmp(c):
    for op in reversed(c.ir):
        if op.tag == 'cmp':
            return op
    return None


def counter(loop, cells):
    inc = None
    for c in list(loop.body) + [cells[loop.at]]:
        for op in c.ir:
            if op.tag == 'calc' and op.op in ('+', '-') and op.left == op.dest and op.rightv is not None:
                inc = (op.dest, op.op, op.rightv)
                break
        if inc:
            break
    if inc is None:
        return None
    cmp = None
    for c in list(loop.body) + [cells[loop.at]]:
        for op in c.ir:
            if op.tag == 'cmp':
                if op.left == inc[0] or op.right == inc[0]:
                    cmp = op
                    break
        if cmp:
            break
    if cmp is None:
        return None
    return {'var': inc[0], 'step': inc[2], 'cmp': cmp}


def top(cells):
    if not cells:
        return []
    backs = back(cells)
    if not backs:
        return [tree('plain', at=i) for i in range(len(cells))]
    heads = {}
    for h, l, k in backs:
        heads.setdefault(h, []).append(l)
    out = []
    seen = set()
    for i, c in enumerate(cells):
        if i in seen:
            continue
        if i in heads:
            latches = heads[i]
            members = inside(cells, i, latches)
            inner = tree('loop', at=i, latches=latches)
            inner.body = []
            for k in sorted(members):
                if k == i:
                    continue
                inner.body.append(cells[k])
                seen.add(k)
            seen.add(i)
            got = counter(inner, cells)
            if got:
                inner.counter = got
            out.append(inner)
        else:
            seen.add(i)
            tw = two_way(cells, i)
            if tw is not None:
                nxt = cells[i].post if hasattr(cells[i], 'post') else None
                if nxt is None:
                    nxt = len(cells) - 1
                then_part = []
                else_part = []
                reach_yes = reaches(cells, tw[0], nxt)
                reach_no = reaches(cells, tw[1], nxt)
                for k in sorted(reach_yes - reach_no):
                    then_part.append(cells[k])
                    seen.add(k)
                for k in sorted(reach_no - reach_yes):
                    else_part.append(cells[k])
                    seen.add(k)
                cond = lastcmp(cells[i])
                out.append(tree('branch', at=i, cond=cond, then_part=then_part, else_part=else_part))
                continue
            out.append(tree('plain', at=i))
    return out
