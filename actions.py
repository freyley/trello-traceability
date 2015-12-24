import sys

from connect import CONNECT_ACTIONS
from runner import _choose_from_list


def quit(*args, **kwargs):
    sys.exit(0)

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


def connect(trello, settings, org):
    task_board = trello.get_board(settings.CURRENT_TASK_BOARD)
    task_lists = task_board.get_lists('open')
    epic_board = trello.get_board(settings.CURRENT_EPIC_BOARD)
    epic_lists = epic_board.get_lists('open')
    from runner import runner
    connection_settings = dict()
    runner(
        CONNECT_ACTIONS, "Connect (h for help, u for up): ",
        back_action='u',
        task_lists=task_lists, epic_lists=epic_lists,
        connection_settings=connection_settings,
        trello=trello, settings=settings, org=org
    )


# TODO: clear screen at beginning of each step and show action title at top
