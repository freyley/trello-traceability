#!/usr/bin/env python

from trello import TrelloClient
import settings
from runner import runner
import actions
from base_action import Action

trelloclient = TrelloClient(
    api_key=settings.TRELLO_API_KEY,
    api_secret=settings.TRELLO_API_SECRET,
    token=settings.TRELLO_OAUTH_TOKEN,
)
org = trelloclient.get_organization(settings.TRELLO_ORGANIZATION_ID)

ACTIONS = {}

def register_action(cmdstring, cmdfunc, description):
    ACTIONS[cmdstring] = Action(cmdstring, cmdfunc, description)

register_action('q', actions.quit, 'Quit')
register_action('ru', actions.remove_organization_user, 'Remove a user from the organization')
register_action('co', actions.connect, 'Connect tasks and epics')


if __name__ == '__main__':
    runner(
        ACTIONS, "T (h for help, q to quit): ",
        trello=trelloclient, settings=settings, org=org
    )
