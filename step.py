from node import node

def walk(tree, visit):
    if isinstance(tree, node):
        visit(tree)
        for key, val in tree.__dict__.items():
            if key == 'kind':
                continue
            if isinstance(val, node):
                walk(val, visit)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, node):
                        walk(item, visit)
                    elif isinstance(item, tuple):
                        for part in item:
                            if isinstance(part, node):
                                walk(part, visit)


def swap(tree, build):
    for key, val in tree.__dict__.items():
        if key == 'kind':
            continue
        if isinstance(val, node):
            setattr(tree, key, build(val))
        elif isinstance(val, list):
            fresh = []
            for item in val:
                if isinstance(item, node):
                    fresh.append(build(item))
                elif isinstance(item, tuple):
                    fresh.append(tuple(build(x) if isinstance(x, node) else x for x in item))
                else:
                    fresh.append(item)
            setattr(tree, key, fresh)
    return tree
