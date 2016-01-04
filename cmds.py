#!/usr/bin/env python
import sys
import models, trellointerface

def make_db():
    models.main()
def fill_db():
    trellointerface.main()
def test_conn():
    import settings
    from trello import TrelloClient
    trelloclient = TrelloClient(
        api_key=settings.TRELLO_API_KEY,
        api_secret=settings.TRELLO_API_SECRET,
        token=settings.TRELLO_OAUTH_TOKEN,
    )
    try:
        organization = trelloclient.get_organization(settings.TRELLO_ORGANIZATION_ID)
    except Exception, e:
        print "Connection broken: {}".format(str(e))
        sys.exit()
    print "Connection OK"
    return organization

def find_boards():
    organization = test_conn()
    for board in organization.get_boards('open'):
        print "{} ({})".format(board.name, board.id)

cmds = {
    'makedb': make_db,
    'filldb': fill_db,
    'test_conn': test_conn,
    'find_boards': find_boards,
}

if len(sys.argv) < 2:
    print "Available commands: {}".format(", ".join(cmds.keys()))
    sys.exit()

cmds[sys.argv[1]]()
