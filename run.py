#!/usr/bin/env python
# can list organization users
# can remove an organization user
# can check boards for users that shouldn't be on there
# can list organization boards
# can set task board
# can set epic board

from actions import ACTIONS

if __name__ == '__main__':
    while True:
        cmd = raw_input("T (h for help, q to quit): ")
        action = ACTIONS.get(cmd)
        if action is None:
            print "Unknown action. 'h' for help"
        else:
            action.cmdfunc()