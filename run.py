#!/usr/bin/env python
# can list organization users
# can remove an organization user
# can check boards for users that shouldn't be on there
# can list organization boards
# can set task board
# can set epic board
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

if __name__ == '__main__':
    while True:
        cmd = raw_input("T (h for help, q to quit): ")
        action = ACTIONS.get(cmd)
        if action is None:
            print "Unknown action. 'h' for help"
        else:
            action.cmdfunc()