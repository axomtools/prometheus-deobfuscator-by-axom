from node import node

words = {
    'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for',
    'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or',
    'repeat', 'return', 'then', 'true', 'until', 'while', 'continue',
}

symbols = [
    '...', '..', '==', '~=', '<=', '>=', '::', '//', '<<', '>>',
    '+', '-', '*', '/', '%', '^', '#', '<', '>', '=',
    '(', ')', '{', '}', '[', ']', ';', ':', ',', '.',
    '|', '&', '~',
]

def unescape(text):
    out = []
    i = 0
    size = len(text)
    while i < size:
        c = text[i]
        if c != '\\':
            out.append(c)
            i += 1
            continue
        i += 1
        if i >= size:
            break
        c = text[i]
        if c == 'n':
            out.append('\n'); i += 1
        elif c == 'r':
            out.append('\r'); i += 1
        elif c == 't':
            out.append('\t'); i += 1
        elif c == 'a':
            out.append('\a'); i += 1
        elif c == 'b':
            out.append('\b'); i += 1
        elif c == 'f':
            out.append('\f'); i += 1
        elif c == 'v':
            out.append('\v'); i += 1
        elif c == '\\':
            out.append('\\'); i += 1
        elif c == '"':
            out.append('"'); i += 1
        elif c == "'":
            out.append("'"); i += 1
        elif c == '\n':
            out.append('\n'); i += 1
        elif c == 'z':
            i += 1
            while i < size and text[i] in ' \t\r\n':
                i += 1
        elif c == 'x':
            i += 1
            h = ''
            while i < size and len(h) < 2 and text[i] in '0123456789abcdefABCDEF':
                h += text[i]; i += 1
            if h:
                out.append(chr(int(h, 16)))
        elif c.isdigit():
            d = ''
            while i < size and len(d) < 3 and text[i].isdigit():
                d += text[i]; i += 1
            out.append(chr(int(d)))
        else:
            out.append(c); i += 1
    return ''.join(out)


def unbracket(text):
    if text.startswith('[['):
        inner = text[2:-2]
    else:
        eq = 0
        i = 1
        while i < len(text) and text[i] == '=':
            eq += 1
            i += 1
        inner = text[i + 1:-(eq + 2)]
    if inner.startswith('\n'):
        inner = inner[1:]
    return inner


def make(kind, value, line, col):
    return node('tok', kind=kind, value=value, line=line, col=col)


def scan(src):
    toks = []
    i = 0
    line = 1
    col = 1
    size = len(src)
    while i < size:
        c = src[i]
        if c in ' \t\r':
            i += 1
            col += 1
            continue
        if c == '\n':
            i += 1
            line += 1
            col = 1
            continue
        if c == '-' and i + 1 < size and src[i + 1] == '-':
            i += 2
            col += 2
            if i < size and src[i] == '[':
                j = i + 1
                eq = 0
                while j < size and src[j] == '=':
                    eq += 1
                    j += 1
                if j < size and src[j] == '[':
                    j += 1
                    close = ']' + '=' * eq + ']'
                    k = src.find(close, j)
                    if k >= 0:
                        i = k + len(close)
                        col = 1
                        continue
            while i < size and src[i] != '\n':
                i += 1
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < size and (src[j].isalnum() or src[j] == '_'):
                j += 1
            w = src[i:j]
            kind = 'word' if w in words else 'name'
            toks.append(make(kind, w, line, col))
            col += j - i
            i = j
            continue
        if c.isdigit() or (c == '.' and i + 1 < size and src[i + 1].isdigit()):
            j = i
            if c == '0' and i + 1 < size and src[i + 1] in 'xX':
                j = i + 2
                while j < size and (src[j].isalnum() or src[j] == '.'):
                    j += 1
            else:
                while j < size and (src[j].isdigit() or src[j] == '.'):
                    j += 1
                if j < size and src[j] in 'eE':
                    j += 1
                    if j < size and src[j] in '+-':
                        j += 1
                    while j < size and src[j].isdigit():
                        j += 1
            toks.append(make('num', src[i:j], line, col))
            col += j - i
            i = j
            continue
        if c == '"' or c == "'":
            q = c
            j = i + 1
            while j < size and src[j] != q:
                if src[j] == '\\':
                    j += 1
                j += 1
            raw = src[i + 1:j]
            toks.append(make('str', unescape(raw), line, col))
            col += j - i + 1
            i = j + 1
            continue
        if c == '[':
            j = i + 1
            eq = 0
            while j < size and src[j] == '=':
                eq += 1
                j += 1
            if j < size and src[j] == '[':
                j += 1
                close = ']' + '=' * eq + ']'
                k = src.find(close, j)
                if k >= 0:
                    raw = src[i:k + len(close)]
                    toks.append(make('str', unbracket(raw), line, col))
                    col += k + len(close) - i
                    i = k + len(close)
                    continue
        hit = None
        for op in symbols:
            if src.startswith(op, i):
                hit = op
                break
        if hit is not None:
            toks.append(make('sym', hit, line, col))
            i += len(hit)
            col += len(hit)
            continue
        i += 1
        col += 1
    toks.append(make('eof', '', line, col))
    return toks
