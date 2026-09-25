def at(cells, target):
    for i, c in enumerate(cells):
        if c.lo <= target <= c.hi:
            return i
    return None


def link(cells):
    for i, c in enumerate(cells):
        for kind, target in c.exit:
            j = at(cells, target)
            if j is not None and j != i:
                cells[j].prev.append((kind, i))
    return cells


def edges(cells):
    out = []
    for i, c in enumerate(cells):
        for kind, target in c.exit:
            j = at(cells, target)
            if j is not None:
                out.append((i, kind, target, j))
    return out


def rank(cells):
    n = len(cells)
    if n == 0:
        return cells
    cells[0].dom = {0}
    for i in range(1, n):
        cells[i].dom = set(range(n))
    changed = True
    while changed:
        changed = False
        for i in range(1, n):
            prev = cells[i].prev
            if not prev:
                continue
            first = prev[0][1]
            common = set(cells[first].dom)
            for kind, p in prev[1:]:
                common = common & cells[p].dom
            common.add(i)
            if common != cells[i].dom:
                cells[i].dom = common
                changed = True
    for i in range(1, n):
        strict = cells[i].dom - {i}
        head = None
        for d in strict:
            if all(e == d or d in cells[e].dom for e in strict):
                head = d
                break
        cells[i].head = head
    return cells


def post(cells):
    n = len(cells)
    if n == 0:
        return cells
    pdom = [set(range(n)) for _ in range(n)]
    last = n - 1
    pdom[last] = {last}
    changed = True
    while changed:
        changed = False
        for i in range(n):
            if i == last:
                continue
            succs = []
            for kind, target in cells[i].exit:
                j = at(cells, target)
                if j is not None:
                    succs.append(j)
            if not succs:
                continue
            common = set(pdom[succs[0]])
            for s in succs[1:]:
                common = common & pdom[s]
            common.add(i)
            if common != pdom[i]:
                pdom[i] = common
                changed = True
    for i in range(n):
        if i == last:
            continue
        strict = pdom[i] - {i}
        head = None
        for d in strict:
            if all(e == d or d in pdom[e] for e in strict):
                head = d
                break
        cells[i].post = head
    return cells
