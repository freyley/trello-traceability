import sys

class Action(object):
    def __init__(self, cmdstring, cmdfunc, description):
        self.cmdstring = cmdstring
        self.cmdfunc = cmdfunc
        self.description = description

ACTIONS = {}

def register_action(cmdstring, cmdfunc, description):
    ACTIONS[cmdstring] = Action(cmdstring, cmdfunc, description)

def quit(*args, **kwargs):
    sys.exit(0)

def help(*args, **kwargs):
    for action in ACTIONS.values():
        print "{}: {}".format(action.cmdstring, action.description)

def remove_organization_user(trello, settings, org):
    members = org.get_members()
    for i, user in enumerate(members):
        print "{}) {} ({})".format(i, user.full_name, user.username)
    cmd = ""
    while cmd != 'q':
        cmd = raw_input("Which one do you want to remove? (q to quit)")
        try:
            cmd = int(cmd)
        except ValueError: continue
        user_to_remove = members[cmd]
        print "removing {}".format(user_to_remove.full_name)
        import ipdb; ipdb.set_trace()

def cleanup_old_members_from_boards(trello, settings, org):
    # TODO
    # what this should do is go through the org boards looking for folks who aren't members and offer to remove them from the board
    pass

def remove_members_from_a_board(trello, settings, org):
    # TODO
    pass

register_action('q', quit, 'Quit')
register_action('h', help, 'Help')
register_action('remove_user', remove_organization_user, 'Remove a user from the organization')