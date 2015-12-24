class Action(object):
    def __init__(self, cmdstring, cmdfunc, description):
        self.cmdstring = cmdstring
        self.cmdfunc = cmdfunc
        self.description = description
