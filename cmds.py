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

def _identify_list_from_identifiers(action_list, identify_mechanisms):
    for key, value in identify_mechanisms.items():
        if isinstance(value, list) or isinstance(value, tuple):
            for item in value:
                if action_list[key] == item:
                    return True
        else:
            if action_list[key] == value:
                return True
    return False

def _going_to_a_done_list(action):
    import settings
    action_list = action['data']['listAfter']
    return _identify_list_from_identifiers(action_list, settings.IDENTIFY_DONE_LIST)

def _going_to_a_started_list(action):
    import settings
    action_list = action['data']['listAfter']
    return _identify_list_from_identifiers(action_list, settings.IDENTIFY_STARTING_LIST)

def _parse_date_or_ipdb(datey):
    try:
        return dateutil.parser.parse(datey)
    except Exception, e:
        import ipdb; ipdb.set_trace()

def close_complete():
    import settings
    from trello import TrelloClient
    trelloclient = TrelloClient(
        api_key=settings.TRELLO_API_KEY,
        api_secret=settings.TRELLO_API_SECRET,
        token=settings.TRELLO_OAUTH_TOKEN,
    )
    MOST_RECENT_DATE_FILENAME = 'most_recent_date'
    try:
        most_recent_date = pickle.load(open(MOST_RECENT_DATE_FILENAME))
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
                item_name = action['data']['checkItem']['name']
                if item_name.startswith('Epic Connection'):
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
    pickle.dump(new_newest_date, open(MOST_RECENT_DATE_FILENAME, 'wb+'))

def find_cycle_times():
    import settings
    from trello import TrelloClient
    trelloclient = TrelloClient(
        api_key=settings.TRELLO_API_KEY,
        api_secret=settings.TRELLO_API_SECRET,
        token=settings.TRELLO_OAUTH_TOKEN,
    )
    CYCLE_TIME_IDENTIFIER = 'Cycle time:::'
    FINISHED_IDENTIFIER = 'Finished:::'
    STARTED_IDENTIFIER = 'Started:::'
    cycle_time_file = open(settings.CYCLE_TIMES_CSV_LOCATION, 'a')
    for board_id in [settings.CURRENT_STORY_BOARD, settings.FUTURE_STORY_BOARD]:
        board = trelloclient.get_board(board_id)

        board.fetch_actions("updateCard:idList")
        actions = board.actions
        for action in actions:
            action_date = dateutil.parser.parse(action['date'])
            if _going_to_a_started_list(action):
                card = trelloclient.get_card(action['data']['card']['id'])
                card.fetch(eager=True)
                for checklist in card.checklists:
                    if checklist.name == 'Meta':
                        checklist.found_started = False
                        for item in checklist.items:
                            if item['name'].startswith(STARTED_IDENTIFIER):
                                checklist.found_started = True
                        if not checklist.found_started:
                            checklist.add_checklist_item('{} {}'.format(STARTED_IDENTIFIER, action['date']))
            elif _going_to_a_done_list(action):
                card = trelloclient.get_card(action['data']['card']['id'])
                card.fetch(eager=True)
                for checklist in card.checklists:
                    if checklist.name == 'Meta':
                        checklist.found_done = False
                        checklist.started_time = checklist.finished_time = checklist.cycle_time = None
                        for item in checklist.items:
                            if item['name'].startswith(FINISHED_IDENTIFIER):
                                checklist.found_done = True
                                checklist.finished_time = _parse_date_or_ipdb(item['name'].split(FINISHED_IDENTIFIER)[1])
                            if item['name'].startswith(STARTED_IDENTIFIER):
                                checklist.started_time = _parse_date_or_ipdb(item['name'].split(STARTED_IDENTIFIER)[1])
                            if item['name'].startswith(CYCLE_TIME_IDENTIFIER):
                                checklist.cycle_time = int(item['name'].split(CYCLE_TIME_IDENTIFIER)[1])
                        if not checklist.found_done:
                            checklist.add_checklist_item('{} {}'.format(FINISHED_IDENTIFIER, action['date']))
                        if checklist.started_time and checklist.finished_time:
                            cycle_time = (action_date - checklist.started_time).total_seconds() / (60*60)
                            cycle_time_string = '{} {}'.format(CYCLE_TIME_IDENTIFIER, cycle_time)
                            if checklist.cycle_time is None:
                                checklist.add_checklist_item(cycle_time_string)
                                cycle_time_file.writelines(["{card.name},{card.id},{card.url},{cycle_time}".format(card=card, cycle_time=cycle_time)])
                            print "Found cycle time for {}: {}".format(card.name, cycle_time_string)



cmds = {
    'makedb': make_db,
    'filldb': fill_db,
    'test_conn': test_conn,
    'find_boards': find_boards,
    'complete': close_complete,
    'cycletimes': find_cycle_times,
}

if len(sys.argv) < 2:
    print "Available commands: {}".format(", ".join(cmds.keys()))
    sys.exit()

cmds[sys.argv[1]]()
