class node:
    def __init__(self, tag, **kw):
        self.kind = tag
        self.__dict__.update(kw)
