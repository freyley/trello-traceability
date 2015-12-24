#!/usr/bin/env python

from actions import ACTIONS

from trello import TrelloClient
import settings

trelloclient = TrelloClient(
    api_key=settings.TRELLO_API_KEY,
    api_secret=settings.TRELLO_API_SECRET,
    token=settings.TRELLO_OAUTH_TOKEN,
)
org = trelloclient.get_organization(settings.TRELLO_ORGANIZATION_ID)

if __name__ == '__main__':
    while True:
        cmd = raw_input("T (h for help, q to quit): ")
        action = ACTIONS.get(cmd)
        if action is None:
            print "Unknown action. 'h' for help"
        else:
            action.cmdfunc(trello=trelloclient, settings=settings, org=org)