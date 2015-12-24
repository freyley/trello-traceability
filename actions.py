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

def _choose_from_list(elements, print_func):
    for i, element in enumerate(elements):
        print "{})".format(i) + print_func(element)
    cmd = ""
    while True:
        cmd = raw_input("Select one? (b to go back)")
        if cmd == 'b':
            return
        try:
            cmd = int(cmd)
        except ValueError:
            continue
        return elements[cmd]


def remove_organization_user(trello, settings, org):
    members = org.get_members()
    while True:
        member = _choose_from_list(members, lambda x: "{} ({})".format(x.full_name, x.username))
        if member is None:
            return
        print "removing {}".format(member.full_name)
        import ipdb; ipdb.set_trace()

def cleanup_old_members_from_boards(trello, settings, org):
    # TODO
    # what this should do is go through the org boards looking for folks who aren't members and offer to remove them from the board
    pass

def remove_members_from_a_board(trello, settings, org):
    # TODO
    pass

def connect_list(ls, trello, settings, org):
    cards = ls.list_cards()
    while True:
        card = _choose_from_list(cards, lambda card: "{}".format(card.name))
        if card is None:
            return
        connect_card(card, trello, settings, org)

def connect_card(card, trello, settings, org):
    # for card in the to tailboard column
    # list the card and look for a Meta checklist
    # if you find a meta checklist, find the card attached to the meta checklist
    # print out the card's name and see if this is right
    # if there's no meta checklist
    #   make a meta checklist
    #   list out the possible cards in On Deck and choose one
    #   or create one
    import ipdb; ipdb.set_trace()


def connect(trello, settings, org):
    board = trello.get_board(settings.CURRENT_TASK_BOARD)
    lists = board.get_lists('open')
    while True:
        ls = _choose_from_list(lists, lambda x: x.name)
        if ls is None:
            return
        connect_list(ls, trello, settings, org)

register_action('q', quit, 'Quit')
register_action('h', help, 'Help')
register_action('ru', remove_organization_user, 'Remove a user from the organization')
register_action('co', connect, 'Connect tasks and epics')