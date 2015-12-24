import sys

def quit():
    sys.exit(0)

def help():
    for action in ACTIONS.values():
        print "{}: {}".format(action.cmdstring, action.description)

class Action(object):
    def __init__(self, cmdstring, cmdfunc, description):
        self.cmdstring = cmdstring
        self.cmdfunc = cmdfunc
        self.description = description

ACTIONS = {}
def register_action(cmdstring, cmdfunc, description):
    ACTIONS[cmdstring] = Action(cmdstring, cmdfunc, description)

register_action('q', quit, 'Quit')
register_action('h', help, 'Help')
