import re

reserved = {
    "and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "if", "in", "local", "nil", "not", "or", "repeat",
    "return", "then", "true", "until", "while", "continue", "self",
}

libnames = {
    "math.random": "MathRandom", "math.floor": "MathFloor", "math.ceil": "MathCeil",
    "math.abs": "MathAbs", "math.clamp": "MathClamp", "math.min": "MathMin",
    "math.max": "MathMax", "math.rad": "MathRad", "math.deg": "MathDeg",
    "math.sqrt": "MathSqrt", "math.sin": "MathSin", "math.cos": "MathCos",
    "math.tan": "MathTan", "math.log": "MathLog", "math.exp": "MathExp",
    "math.noise": "MathNoise", "math.round": "MathRound", "math.sign": "MathSign",
    "math.fmod": "MathFmod", "math.pow": "MathPow", "math.atan2": "MathAtan2",
    "math.asin": "MathAsin", "math.acos": "MathAcos", "math.atan": "MathAtan",
    "math.sinh": "MathSinh", "math.cosh": "MathCosh", "math.tanh": "MathTanh",
    "math.modf": "MathModf", "math.huge": "MathHuge", "math.pi": "MathPi",
    "math.nan": "MathNaN",
    "table.insert": "TableInsert", "table.remove": "TableRemove", "table.concat": "TableConcat",
    "table.find": "TableFind", "table.sort": "TableSort", "table.unpack": "TableUnpack",
    "table.pack": "TablePack", "table.create": "TableCreate", "table.clear": "TableClear",
    "table.clone": "TableClone", "table.freeze": "TableFreeze", "table.isfrozen": "TableIsFrozen",
    "table.maxn": "TableMaxN", "table.move": "TableMove",
    "string.format": "StringFormat", "string.sub": "StringSub", "string.upper": "StringUpper",
    "string.lower": "StringLower", "string.rep": "StringRep", "string.split": "StringSplit",
    "string.gsub": "StringGsub", "string.match": "StringMatch", "string.find": "StringFind",
    "string.gmatch": "StringGmatch", "string.len": "StringLen", "string.byte": "StringByte",
    "string.char": "StringChar", "string.reverse": "StringReverse", "string.pack": "StringPack",
    "string.unpack": "StringUnpack", "string.packsize": "StringPackSize",
    "task.wait": "TaskWait", "task.spawn": "TaskSpawn", "task.delay": "TaskDelay",
    "task.defer": "TaskDefer", "task.cancel": "TaskCancel", "task.synchronize": "TaskSync",
    "task.desynchronize": "TaskDesync",
    "coroutine.create": "CoroutineCreate", "coroutine.resume": "CoroutineResume",
    "coroutine.yield": "CoroutineYield", "coroutine.status": "CoroutineStatus",
    "coroutine.wrap": "CoroutineWrap", "coroutine.running": "CoroutineRunning",
    "coroutine.isyieldable": "CoroutineIsYieldable", "coroutine.close": "CoroutineClose",
    "os.time": "OsTime", "os.date": "OsDate", "os.clock": "OsClock",
    "os.difftime": "OsDiffTime", "os.getenv": "OsGetEnv",
    "utf8.char": "Utf8Char", "utf8.codepoint": "Utf8CodePoint", "utf8.len": "Utf8Len",
    "utf8.offset": "Utf8Offset", "utf8.codes": "Utf8Codes", "utf8.graphemes": "Utf8Graphemes",
    "bit32.band": "Bit32Band", "bit32.bor": "Bit32Bor", "bit32.bxor": "Bit32Bxor",
    "bit32.bnot": "Bit32Bnot", "bit32.lshift": "Bit32LShift", "bit32.rshift": "Bit32RShift",
    "bit32.arshift": "Bit32ArShift", "bit32.lrotate": "Bit32LRotate", "bit32.rrotate": "Bit32RRotate",
    "bit32.btest": "Bit32BTest", "bit32.extract": "Bit32Extract", "bit32.replace": "Bit32Replace",
    "debug.traceback": "DebugTraceback", "debug.info": "DebugInfo", "debug.getinfo": "DebugGetInfo",
    "debug.profilebegin": "DebugProfileBegin", "debug.profileend": "DebugProfileEnd",
    "debug.getmemorycategory": "DebugGetMemoryCategory",
    "debug.setmemorycategory": "DebugSetMemoryCategory",
    "debug.resetmemorycategory": "DebugResetMemoryCategory",
}

globals = {
    "pcall": "PcallOk", "xpcall": "XpcallOk", "assert": "Asserted",
    "type": "TypeName", "typeof": "TypeName", "tostring": "ToString",
    "tonumber": "ToNumber", "ipairs": "IPairsIterator", "pairs": "PairsIterator",
    "next": "NextItem", "select": "Selected", "unpack": "Unpacked",
    "rawget": "RawValue", "rawset": "RawTable", "rawequal": "RawEqual",
    "rawlen": "RawLength", "getmetatable": "Metatable", "setmetatable": "WithMetatable",
    "newproxy": "NewProxy", "require": "Module", "collectgarbage": "Collected",
    "loadstring": "LoadedFunction", "load": "LoadedFunction", "getfenv": "Environment",
    "setfenv": "Function", "getgenv": "Environment", "error": "ErrorMessage",
    "tick": "Tick", "time": "Time", "wait": "Elapsed", "spawn": "Thread",
    "delay": "Thread", "settings": "Settings",
}

methods = {
    "Wait": "Elapsed", "Connect": "Connection", "Once": "Connection",
    "Clone": "Clone", "Destroy": "Destroyed", "ClearAllChildren": "Cleared",
    "GetChildren": "Children", "GetDescendants": "Descendants", "GetPlayers": "PlayerList",
    "GetTagged": "Tagged", "GetInstanceAddedSignal": "Signal",
    "GetInstanceRemovedSignal": "Signal", "GetDataStore": "DataStore",
    "GetOrderedDataStore": "OrderedDataStore", "GetGlobalDataStore": "GlobalDataStore",
    "GetCollisionGroupId": "GroupId", "GetCollisionGroupName": "GroupName",
    "CreatePath": "Path", "Create": "Created", "JSONEncode": "Json",
    "JSONDecode": "Decoded", "HttpGetAsync": "Response", "HttpPostAsync": "Response",
    "GetAsync": "Value", "SetAsync": "Value", "UpdateAsync": "Value",
    "IncrementAsync": "Value", "Kick": "Kicked", "GetMouse": "Mouse",
    "GetPropertyChangedSignal": "Signal", "GetAttributeChangedSignal": "Signal",
    "GetAttribute": "Value", "SetAttribute": "Attribute", "GetPivot": "Pivot",
    "PivotTo": "Pivot", "GetFullName": "FullName", "GetDebugId": "DebugId",
    "FindFirstAncestor": "Ancestor", "FindFirstAncestorOfClass": "Ancestor",
    "FindFirstAncestorWhichIsA": "Ancestor", "IsA": "IsType",
    "AddTag": "Tag", "RemoveTag": "Tag", "HasTag": "HasTag", "GetTags": "Tags",
    "WaitForChild": "Child", "FindFirstChild": "Child",
    "FindFirstChildOfClass": "Child", "FindFirstChildWhichIsA": "Child",
    "SetPrimaryPartCFrame": "Pivot", "GetPrimaryPartCFrame": "Pivot",
    "MoveTo": "Pivot", "LoadCharacter": "Character",
    "LoadCharacterWithHumanoidDescription": "Character",
    "GetRankInGroup": "Rank", "GetRoleInGroup": "Role", "IsInGroup": "IsInGroup",
    "IsFriendsWith": "IsFriend", "GetFriendsAsync": "Friends",
    "GetUserIdFromNameAsync": "UserId", "GetNameFromUserIdAsync": "UserName",
    "GetUserThumbnailAsync": "Thumbnail", "GetProductInfo": "ProductInfo",
    "UserOwnsGamePassAsync": "OwnsGamePass", "PromptGamePassPurchase": "Prompt",
    "PromptProductPurchase": "Prompt", "PromptPurchase": "Prompt",
    "GetDeveloperProductsAsync": "Products", "GetStorePages": "Pages",
}


def merge(text):
    parts = re.split(r"[\s_\-]+", text)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def valid(text):
    return bool(re.fullmatch(r"[A-Za-z_]\w*", text))


def trim(text):
    m = re.match(r'^(.*?)\s*\[[^\]]*\]\s*$', text)
    if m:
        head = m.group(1)
        if '.' in head or ':' in head:
            return head
    return text


def guess(text):
    e = re.sub(r"--.*$", "", text).strip()
    if not e:
        return None
    e = trim(e)

    m = re.match(r'^game\s*:\s*GetService\s*\(\s*["\']([^"\']+)["\']\s*\)\s*$', e)
    if m:
        n = merge(m.group(1))
        return n if valid(n) and n not in reserved else None

    m = re.match(r'^Instance\s*\.\s*new\s*\(\s*["\']([^"\']+)["\']', e)
    if m:
        n = merge(m.group(1))
        return n if valid(n) and n not in reserved else None

    m = re.match(r'^Enum\s*\.\s*([A-Za-z_]\w*)\s*\.\s*([A-Za-z_]\w*)\s*$', e)
    if m:
        t, v = m.group(1), m.group(2)
        n = (t + v) if len(v) <= 1 else v
        return n if valid(n) and n not in reserved else None

    m = re.search(r'[.:]\s*(?:WaitForChild|FindFirstChild|FindFirstChildOfClass|FindFirstChildWhichIsA)\s*\(\s*["\']([^"\']+)["\']', e)
    if m:
        n = merge(m.group(1))
        return n if valid(n) and n not in reserved else None

    m = re.match(r'^([A-Z][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_]\w*)\s*\(', e)
    if m:
        dt, method = m.group(1), m.group(2)
        if method == "new" or method.startswith("from") or method.startswith("look"):
            n = dt
        else:
            n = merge(method)
        return n if valid(n) and n not in reserved else None

    m = re.match(r'^([A-Z][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_]\w*)\s*$', e)
    if m:
        n = merge(m.group(2))
        return n if valid(n) and n not in reserved else None

    m = re.match(r'^([a-z_]\w*)\s*\.\s*([a-z_]\w*)\s*\(', e)
    if m:
        key = "%s.%s" % (m.group(1), m.group(2))
        if key in libnames:
            n = libnames[key]
            return n if valid(n) and n not in reserved else None

    m = re.match(r'^([a-z_]\w*)\s*\.\s*([a-z_]\w*)\s*$', e)
    if m:
        key = "%s.%s" % (m.group(1), m.group(2))
        if key in libnames:
            n = libnames[key]
            return n if valid(n) and n not in reserved else None

    m = re.match(r'^([a-z_]\w*)\s*\(', e)
    if m:
        fn = m.group(1)
        if fn in globals:
            n = globals[fn]
            return n if valid(n) and n not in reserved else None

    m = re.search(r'[.:]\s*([A-Za-z_]\w*)\s*\(', e)
    if m:
        method = m.group(1)
        n = methods.get(method, merge(method))
        return n if valid(n) and n not in reserved else None

    m = re.search(r"\.\s*([A-Z][A-Za-z0-9_]*)\s*$", e)
    if m:
        n = m.group(1)
        return n if valid(n) and n not in reserved else None

    m = re.search(r'\[\s*["\']([A-Z][A-Za-z0-9_]*)["\']\s*\]\s*$', e)
    if m:
        n = merge(m.group(1))
        return n if valid(n) and n not in reserved else None

    m = re.match(r'^([a-zA-Z_]\w*)\s*$', e)
    if m:
        name = m.group(1)
        if name in reserved:
            return None
        n = name[0].upper() + name[1:] if name[0].islower() else name
        return n if valid(n) and n not in reserved else None

    return None
