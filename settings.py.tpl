TRELLO_API_KEY=''
TRELLO_API_SECRET=''
TRELLO_OAUTH_TOKEN=''

TRELLO_ORGANIZATION_ID = ''

CURRENT_STORY_BOARD = ''
CURRENT_EPIC_BOARD = ''
FUTURE_STORY_BOARD = ''
TRELLO_DB_CONNECTION_STRING = 'sqlite:///trello.db'

# identifiers for calculating cycle time - you can identify starting lists and finishing lists by either id or name
IDENTIFY_STARTING_LIST = {'id': 'FILLMEIN'}
IDENTIFY_DONE_LIST = {'name': ['Ready for Release', 'Done']}
IDENTIFY_ANY_DONE_LIST = {'name': ['develop', 'Ready for QA']}
IDENTIFY_CURRENTLY_DOING_LIST = {'name__startswith': ['feature', 'release'], 'id': 'FILLMEIN' }
CYCLE_TIMES_CSV_LOCATION = '/bar/bin/bash'
