import json


log = []


class ghost:
    def __init__(self, kind, name=None):
        self.kind = kind
        self.name = name or kind
        self.props = {}
        self.parent = None
        for m in ('Wait', 'Connect', 'Once', 'Destroy', 'Clone', 'GetChildren',
                  'GetDescendants', 'FindFirstChild', 'WaitForChild',
                  'FindFirstChildOfClass', 'FindFirstChildWhichIsA',
                  'GetPropertyChangedSignal', 'GetAttributeChangedSignal',
                  'GetAttribute', 'SetAttribute', 'IsA', 'AddTag', 'RemoveTag',
                  'HasTag', 'GetTags', 'GetFullName', 'GetDebugId',
                  'SetPrimaryPartCFrame', 'PivotTo', 'MoveTo', 'LoadCharacter',
                  'LoadCharacterWithHumanoidDescription', 'Kick', 'GetMouse',
                  'GetPlayers', 'GetRankInGroup', 'GetRoleInGroup', 'IsInGroup',
                  'IsFriendsWith', 'GetFriendsAsync', 'GetUserIdFromNameAsync',
                  'GetNameFromUserIdAsync', 'GetUserThumbnailAsync',
                  'GetProductInfo', 'UserOwnsGamePassAsync',
                  'PromptGamePassPurchase', 'PromptProductPurchase',
                  'PromptPurchase', 'GetDeveloperProductsAsync', 'GetStorePages',
                  'GetDataStore', 'GetOrderedDataStore', 'GetGlobalDataStore',
                  'CreatePath', 'Create', 'JSONEncode', 'JSONDecode',
                  'HttpGetAsync', 'HttpPostAsync', 'GetAsync', 'SetAsync',
                  'UpdateAsync', 'IncrementAsync', 'Fire', 'Invoke',
                  'Emit', 'Trigger', 'GetService', 'FindService'):
            setattr(self, m, method(m, self))

    def get(self, key):
        if key in self.props:
            return self.props[key]
        if key == 'Name':
            return self.name
        if key == 'ClassName':
            return self.kind
        if key == 'Parent':
            return self.parent
        if key == 'Position':
            return ghost('Vector3', 'Position')
        if key == 'Size':
            return ghost('Vector2', 'Size')
        if key == 'CFrame':
            return ghost('CFrame', 'CFrame')
        if key == 'Velocity':
            return ghost('Vector3', 'Velocity')
        if key == 'Anchored':
            return False
        if key == 'Transparency':
            return 0
        if key == 'Visible':
            return True
        if key == 'Value':
            return ghost('Value', 'Value')
        if key == 'Text':
            return ''
        if key == 'LocalPlayer':
            return ghost('Player', 'LocalPlayer')
        if key == 'PlayerGui':
            return ghost('PlayerGui', 'PlayerGui')
        if key == 'Character':
            return ghost('Model', 'Character')
        if key == 'Humanoid':
            return ghost('Humanoid', 'Humanoid')
        if key == 'Backpack':
            return ghost('Backpack', 'Backpack')
        if key == 'Camera':
            return ghost('Camera', 'Camera')
        if key == 'Workspace':
            return ghost('Workspace', 'Workspace')
        child = ghost(key, key)
        child.parent = self
        self.props[key] = child
        return child

    def set(self, key, val):
        self.props[key] = val
        if key == 'Name' and isinstance(val, str):
            self.name = val
        short_val = short(val)
        text = path(self) + '.' + key + ' = ' + short_val
        log.append(text)

    def raw(self):
        return dict(self.props)


class method:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner

    def __call__(self, args):
        items = list(args)
        receiver = None
        if items and items[0] is self.owner:
            receiver = self.owner
            items = items[1:]
        chain = path(self.owner) + ':' + self.name
        args_text = ', '.join(short(a) for a in items)
        log.append(chain + '(' + args_text + ')')
        if self.name in ('GetService', 'FindService'):
            kind = items[0] if items else 'Service'
            return ghost(kind, kind)
        if self.name == 'new':
            kind = items[0] if items else 'Instance'
            return ghost(kind, kind)
        if self.name == 'fromExisting':
            return ghost('Instance', 'Cloned')
        if self.name in ('WaitForChild', 'FindFirstChild', 'FindFirstChildOfClass', 'FindFirstChildWhichIsA'):
            kind = items[0] if items else 'Child'
            return ghost(kind, kind)
        if self.name in ('GetChildren', 'GetDescendants'):
            return []
        if self.name in ('Connect', 'Once'):
            return ghost('Connection', 'Connection')
        if self.name == 'IsA':
            return self.owner.kind == (items[0] if items else '')
        if self.name == 'GetFullName':
            return path(self.owner)
        if self.name == 'GetAsync' or self.name == 'GetDataStore':
            return ghost('Value', 'Value')
        if self.name == 'Clone':
            return ghost(self.owner.kind, self.owner.name)
        if self.name == 'Create':
            return ghost('Instance', 'Created')
        if self.name == 'GetMouse':
            return ghost('Mouse', 'Mouse')
        if self.name == 'GetPlayers':
            return []
        if self.name == 'JSONEncode':
            try:
                return json.dumps(items[0]) if items else '{}'
            except Exception:
                return '{}'
        if self.name == 'JSONDecode':
            try:
                return json.loads(items[0]) if items else {}
            except Exception:
                return {}
        return ghost('Return', 'Return')


def path(g):
    if g.parent is None:
        return g.name
    return path(g.parent) + '.' + g.name


def short(value):
    if isinstance(value, ghost):
        return path(value)
    if isinstance(value, str):
        out = value.replace('\\', '\\\\').replace('"', '\\"')
        out = out.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + out + '"'
    if value is None:
        return 'nil'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return '{' + ', '.join(short(x) for x in value) + '}'
    if isinstance(value, dict):
        return '{' + ', '.join('%s = %s' % (k, short(v)) for k, v in value.items()) + '}'
    if isinstance(value, tuple) and value and value[0] == 'func':
        return 'function() end'
    return str(value)


def fprint(args):
    items = ', '.join(short(a) for a in args)
    log.append('print(' + items + ')')
    return None


def fwarn(args):
    items = ', '.join(short(a) for a in args)
    log.append('warn(' + items + ')')
    return None


def ferror(args):
    items = ', '.join(short(a) for a in args)
    log.append('error(' + items + ')')
    raise RuntimeError(items)


def fassert(args):
    if args and not args[0]:
        raise RuntimeError(short(args[1]) if len(args) > 1 else 'assertion failed')
    return args[0] if args else None


def fwait(args):
    n = args[0] if args else 0
    log.append('wait(' + short(n) + ')')
    return n


def fspawn(args):
    log.append('spawn(...)')
    return None


def fdelay(args):
    log.append('delay(...)')
    return None


def ftick(args):
    return 0


def ftime(args):
    return 0


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
        if i >= len(t):
            return None
        s['i'] = i + 1
        return (i + 1, s['t'][i])

    return (iterfn, state, None)


def fpcall(args):
    fn = args[0]
    rest = list(args[1:])
    if callable(fn):
        try:
            return (True, fn(rest))
        except Exception:
            return (False, 'error')
    if isinstance(fn, tuple) and fn and fn[0] == 'func':
        return (True, None)
    return (False, 'error')


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
    if isinstance(v, ghost):
        return 'userdata'
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
    if isinstance(v, ghost):
        return path(v)
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


def frequire(args):
    log.append('require(' + short(args[0] if args else '') + ')')
    return ghost('Module', 'Module')


def fidentify(args):
    return 'deobf'


def fgetgenv(args):
    return {}


def fgetrenv(args):
    return {}


def fgethui(args):
    return ghost('Hui', 'gethui')


def floadstring(args):
    return ghost('Function', 'LoadedFunction')


def fload(args):
    return ghost('Function', 'LoadedFunction')


def fnop(args):
    return None


seedmap = {
    'print': fprint,
    'warn': fwarn,
    'error': ferror,
    'assert': fassert,
    'wait': fwait,
    'spawn': fspawn,
    'delay': fdelay,
    'tick': ftick,
    'time': ftime,
    'pairs': fpairs,
    'ipairs': fipairs,
    'pcall': fpcall,
    'select': fselect,
    'type': ftype,
    'typeof': ftype,
    'tostring': ftostring,
    'tonumber': ftonumber,
    'require': frequire,
    'identifyexecutor': fidentify,
    'getexecutorname': fidentify,
    'getgenv': fgetgenv,
    'getrenv': fgetrenv,
    'gethui': fgethui,
    'loadstring': floadstring,
    'load': fload,
    'dofile': fload,
    'loadfile': fload,
    'newcclosure': lambda args: args[0] if args else None,
    'checkcaller': lambda args: True,
    'islclosure': lambda args: True,
    'iscclosure': lambda args: False,
    'getrawmetatable': lambda args: {},
    'setrawmetatable': fnop,
    'hookfunction': lambda args: args[0] if args else None,
    'hookmetamethod': lambda args: None,
    'getnamecallmethod': lambda args: 'Method',
    'setreadonly': fnop,
    'isreadonly': lambda args: False,
}


def attach(env):
    import math
    game = ghost('DataModel', 'game')
    inst = ghost('Instance', 'Instance')
    task = ghost('task', 'task')
    enum = ghost('Enum', 'Enum')
    workspace = ghost('Workspace', 'workspace')
    script = ghost('Script', 'script')
    env.make('game', game)
    env.make('Instance', inst)
    env.make('task', task)
    env.make('Enum', enum)
    env.make('workspace', workspace)
    env.make('script', script
