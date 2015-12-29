#!/usr/bin/env python
import trollius
import datetime
from models import get_session, Board, TrelloList, Checklist, Card

class TrelloInterface(object):
    def __init__(self, trello, organization, settings):
        self.trello = trello
        self.organization = organization
        self.settings = settings
        self.db_session = get_session()()

    def reset(self):
        self.db_session.query(Card).delete()
        self.db_session.query(Checklist).delete()
        self.db_session.query(TrelloList).delete()
        self.db_session.query(Board).delete()

        self._story_board = self.trello.get_board(self.settings.CURRENT_TASK_BOARD)
        self.db_session.add(Board(id=self._story_board.id, name=self._story_board.name))

        self._story_lists = self._story_board.get_lists('open')

        self._epic_board = self.trello.get_board(self.settings.CURRENT_EPIC_BOARD)
        self._epic_lists = self._epic_board.get_lists('open')
        self._story_list_cards = []
        self._epic_list_cards = []
        self._get_epics_and_stories()

    def _get_epics_and_stories(self):
        def _get(lst):
            self.db_session.add(TrelloList(id=lst.id, name=lst.name, board_id=lst.board.id))
            return lst.list_cards()

        def _do_calls():
            loop = trollius.get_event_loop()
            story_futures = []
            epic_futures = []
            for story_list in self._story_lists:
                story_futures.append(loop.run_in_executor(None, _get, story_list))
            for epic_list in self._epic_lists:
                epic_futures.append(loop.run_in_executor(None, _get, epic_list))
            return (story_futures, epic_futures)

        @trollius.coroutine
        def call():
            all_futures = _do_calls()
            for futures in all_futures:
                for future in futures:
                    cards = yield trollius.From(future)
                    for card in cards:
                        self.db_session.add(Card(id=card.id, name=card.name, trellolist_id=card.list_id))
            raise trollius.Return("")

        now = datetime.datetime.now()
        loop = trollius.get_event_loop()
        loop.run_until_complete(call())
        self.db_session.commit()
        print "time elapsed: {}".format(datetime.datetime.now() - now)


if __name__ == '__main__':
    import settings
    from trello import TrelloClient
    trelloclient = TrelloClient(
        api_key=settings.TRELLO_API_KEY,
        api_secret=settings.TRELLO_API_SECRET,
        token=settings.TRELLO_OAUTH_TOKEN,
    )
    organization = trelloclient.get_organization(settings.TRELLO_ORGANIZATION_ID)
    ti = TrelloInterface(trelloclient, organization, settings)
    ti.reset()
