from base_action import Action
from runner import _choose_from_list

CONNECT_ACTIONS = {}

def register_action(cmdstring, cmdfunc, description):
    CONNECT_ACTIONS[cmdstring] = Action(cmdstring, cmdfunc, description)

def choose_tasklist(task_lists, connection_settings, **kwargs):
    connection_settings['tasklist'] = _choose_from_list(task_lists, lambda x: x.name)

def choose_epiclist(epic_lists, connection_settings, **kwargs):
    connection_settings['epiclist'] = _choose_from_list(epic_lists, lambda x: x.name)

def go(connection_settings, trello, settings, org, **kwargs):
    if 'tasklist' not in connection_settings or 'epiclist' not in connection_settings:
        print "Must choose tasklist and epiclist first"
        return
    import ipdb; ipdb.set_trace()
    for card in connection_settings['tasklist'].list_cards():
        _connect_card(card, connection_settings, trello, settings, org)

register_action('tl', choose_tasklist, 'Choose Task list')
register_action('el', choose_epiclist, 'Choose Epic list')
register_action('go', go, 'Connect cards')

def _connect_card(card, connection_settings, trello, settings, org):
    meta_checklist = None
    if card.checklists:
        for checklist in card.checklists:
            if checklist.name == 'Meta':
                meta_checklist = checklist
    if not meta_checklist:
        meta_checklist = card.add_checklist('Meta', [])
    for item in meta_checklist.items:
        if item.startswith('Epic Connection:'):
            epic_id = item.split(':')[1].strip()
            epic = trello.get_card(epic_id)
            print "{} connected to epic {}".format(card.name, epic.name)

    # list the card and look for a Meta checklist
    # if you find a meta checklist, find the card attached to the meta checklist
    # print out the card's name and see if this is right
    # if there's no meta checklist
    #   make a meta checklist
    #   list out the possible cards in On Deck and choose one
    #   or create one
    import ipdb; ipdb.set_trace()
