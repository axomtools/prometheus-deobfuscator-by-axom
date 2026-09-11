class node:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)
