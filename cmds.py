#!/usr/bin/env python
import pickle
import sys
from datetime import timedelta, datetime

import dateutil
import pytz

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

def close_complete():
    import settings
    from trello import TrelloClient
    trelloclient = TrelloClient(
        api_key=settings.TRELLO_API_KEY,
        api_secret=settings.TRELLO_API_SECRET,
        token=settings.TRELLO_OAUTH_TOKEN,
    )
    try:
        most_recent_date = pickle.load(open('most_recent_date'))
    except IOError:
        utc = pytz.timezone("UTC")
        most_recent_date = datetime.now(utc) - timedelta(100)

    new_newest_date = most_recent_date
    for board_id in [settings.CURRENT_STORY_BOARD, settings.FUTURE_STORY_BOARD]:
        board = trelloclient.get_board(board_id)
        board.fetch_actions('updateCheckItemStateOnCard')
        actions = board.actions
        for action in actions:
            action_date = dateutil.parser.parse(action['date'])
            if action_date > new_newest_date:
                new_newest_date = action_date
            if action_date <= most_recent_date:
                break
            if action['data']['checklist']['name'] == 'Meta':
                epic_connection = action['data']['checkItem']['name']
                epic_card_id = epic_connection.split(':')[1].strip()
                card_id = action['data']['card']['id']
                card_name = action['data']['card']['name']
                epic = trelloclient.get_card(epic_card_id)
                epic.fetch(eager=True)
                for checklist in epic.checklists:
                    if checklist.name == 'Stories':
                        for item in checklist.items:
                            if item['name'].startswith(card_id):
                                print "Completing {} on epic {}".format(card_name, epic.name)
                                checklist.set_checklist_item(item['name'], checked=True)

    pickle.dump(new_newest_date, open('most_recent_date', 'wb+'))

cmds = {
    'makedb': make_db,
    'filldb': fill_db,
    'test_conn': test_conn,
    'find_boards': find_boards,
    'complete': close_complete,
}

if len(sys.argv) < 2:
    print "Available commands: {}".format(", ".join(cmds.keys()))
    sys.exit()

cmds[sys.argv[1]]()
