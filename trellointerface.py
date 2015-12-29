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
        self._epic_board = self.trello.get_board(self.settings.CURRENT_EPIC_BOARD)
        self.db_session.add(Board(id=self._story_board.id, name=self._story_board.name, story_board=True))
        self.db_session.add(Board(id=self._epic_board.id, name=self._epic_board.name, epic_board=True))
        self._story_lists = self._story_board.get_lists('open')
        self._epic_lists = self._epic_board.get_lists('open')
        self._get_epics_and_stories()

    def _get_epics_and_stories(self):

        def _get_checklist_future(trellocard):
            meta_checklist = None
            db_card = Card.create(self.db_session, id=trellocard.id, name=trellocard.name, trellolist_id=trellocard.list_id)
            # gotta populate those checklists
            trellocard.fetch(eager=True)
            list_name = None
            if db_card.trellolist.board.story_board:
                list_name = 'Meta'
            elif db_card.trellolist.board.epic_board:
                list_name = 'Stories'
            else:
                raise Exception("Board must be epic or stories")

            if trellocard.checklists:
                for checklist in trellocard.checklists:
                    if checklist.name == list_name:
                        meta_checklist = checklist
            if not meta_checklist:
                meta_checklist = trellocard.add_checklist(list_name, [])
            db_card.magic_checklist_id = meta_checklist.id
            if db_card.trellolist.board.story_board:
                for item in meta_checklist.items:
                    if item['name'].startswith('Epic Connection:'):
                        db_card.connected_to_id = item['name'].split(':')[1].strip()
            db_card.save()

        def _make_checklist_futures(cards):
            loop = trollius.get_event_loop()
            futures = []
            for card in cards:
                futures.append(loop.run_in_executor(None, _get_checklist_future, card))
            return futures

        def _make_trello_list(lst):
            self.db_session.add(TrelloList(id=lst.id, name=lst.name, board_id=lst.board.id))
            return lst.list_cards()

        def _make_cards():
            loop = trollius.get_event_loop()
            futures = []
            for story_list in self._story_lists:
                futures.append(loop.run_in_executor(None, _make_trello_list, story_list))
            for epic_list in self._epic_lists:
                futures.append(loop.run_in_executor(None, _make_trello_list, epic_list))
            return futures

        @trollius.coroutine
        def make_cards():
            futures = _make_cards()
            for future in futures:
                cards = yield trollius.From(future)
                new_futures = _make_checklist_futures(cards)
                for future in new_futures:
                    yield trollius.From(future)

        now = datetime.datetime.now()
        loop = trollius.get_event_loop()
        loop.run_until_complete(make_cards())
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
