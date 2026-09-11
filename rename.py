import re
import bisect
from guess import reserved
from guess import guess


def chop(code):
    out = []
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c == "-" and i + 1 < n and code[i + 1] == "-":
            start = i
            if i + 3 < n and code[i + 2] == "[" and code[i + 3] == "[":
                end = code.find("]]", i + 4)
                i = n if end == -1 else end + 2
            else:
                end = code.find("\n", i)
                i = n if end == -1 else end
            out.append(("note", code[start:i], start, i))
            continue
        if c == '"' or c == "'":
            start = i
            q = c
            i += 1
            while i < n and code[i] != q:
                if code[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            if i < n:
                i += 1
            out.append(("str", code[start:i], start, i))
            continue
        if c == "[" and i + 1 < n and (code[i + 1] == "[" or code[i + 1] == "="):
            j = i + 1
            eq = 0
            while j < n and code[j] == "=":
                eq += 1
                j += 1
            if j < n and code[j] == "[":
                close = "]" + "=" * eq + "]"
                end = code.find(close, j + 1)
                stop = n if end == -1 else end + len(close)
                out.append(("str", code[i:stop], i, stop))
                i = stop
                continue
        if c.isalpha() or c == "_":
            start = i
            while i < n and (code[i].isalnum() or code[i] == "_"):
                i += 1
            word = code[start:i]
            out.append(("kw" if word in reserved else "name", word, start, i))
            continue
        if c.isdigit() or (c == "." and i + 1 < n and code[i + 1].isdigit()):
            start = i
            while i < n and (code[i].isalnum() or code[i] in "._"):
                i += 1
            out.append(("num", code[start:i], start, i))
            continue
        out.append(("op", c, i, i + 1))
        i += 1
    return out


def scopes(tokens):
    found = []
    stack = []
    waiting = False
    for ti, tok in enumerate(tokens):
        if tok[0] != "kw":
            continue
        w = tok[1]
        if w in ("for", "while"):
            waiting = True
            stack.append((ti, False, ti))
        elif w == "do":
            if waiting:
                waiting = False
            else:
                stack.append((ti, False, ti))
        elif w in ("function", "repeat"):
            stack.append((ti, False, ti))
        elif w == "if":
            stack.append((ti, True, ti))
        elif w in ("elseif", "else"):
            if stack and stack[-1][1]:
                openti, isif, branchstart = stack.pop()
                found.append((branchstart, ti))
                stack.append((openti, True, ti))
        elif w in ("end", "until"):
            if stack:
                openti, isif, branchstart = stack.pop()
                found.append((branchstart, ti))
    return found


def rename(code):
    tokens = chop(code)
    n = len(tokens)
    if n == 0:
        return code

    found = scopes(tokens)
    found.sort()
    starts = [s[0] for s in found]

    def endof(ti):
        pos = bisect.bisect_right(starts, ti) - 1
        while pos >= 0:
            s, e = found[pos]
            if e > ti:
                return e
            pos -= 1
        return n

    used = set()
    for ti in range(n - 1):
        if tokens[ti][0] == "kw" and tokens[ti][1] == "local":
            if tokens[ti + 1][0] == "name":
                used.add(tokens[ti + 1][1])

    plans = []
    ti = 0
    while ti < n - 1:
        tok = tokens[ti]
        if tok[0] == "kw" and tok[1] == "local":
            nametok = tokens[ti + 1]
            if nametok[0] == "name" and ti + 2 < n:
                eqtok = tokens[ti + 2]
                if eqtok[0] == "op" and eqtok[1] == "=":
                    oldname = nametok[1]
                    if not oldname.startswith("_"):
                        exprstart = eqtok[3]
                        lineend = code.find("\n", exprstart)
                        if lineend == -1:
                            lineend = len(code)
                        exprtext = code[exprstart:lineend]
                        newname = guess(exprtext)
                        if newname and newname != oldname:
                            scopeendti = endof(ti)
                            candidate = newname
                            suffix = 2
                            while candidate in used:
                                candidate = newname + str(suffix)
                                suffix += 1
                            used.add(candidate)
                            plans.append((oldname, candidate, ti, scopeendti))
        ti += 1

    if not plans:
        return code

    lookup = {}
    for oldname, newname, declti, scopeendti in plans:
        lookup.setdefault(oldname, []).append((newname, declti, scopeendti))

    edits = []
    for ti, tok in enumerate(tokens):
        if tok[0] != "name":
            continue
        rules = lookup.get(tok[1])
        if not rules:
            continue
        bestname = None
        bestdecl = -1
        for newname, declti, scopeendti in rules:
            if declti <= ti < scopeendti and declti > bestdecl:
                bestname = newname
                bestdecl = declti
        if bestname is not None:
            edits.append((tok[2], tok[3], bestname))

    if not edits:
        return code

    edits.sort()
    out = []
    last = 0
    for start, end, newtext in edits:
        if start < last:
            continue
        out.append(code[last:start])
        out.append(newtext)
        last = end
    out.append(code[last:])
    return "".join(out)
