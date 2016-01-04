#!/usr/bin/env python
from time import sleep

import trollius
import datetime
from models import get_session, Board, TrelloList, Checklist, Card, User

def create_dbcard_and_ensure_checklist(db_session, trellocard, prefetch_checklists=False):
    if prefetch_checklists:
        trellocard.fetch(eager=True)
    meta_checklist = None
    db_card = Card.create(db_session, id=trellocard.id, name=trellocard.name, trellolist_id=trellocard.list_id)
    # gotta populate those checklists
    list_name = None
    if db_card.trellolist.board.story_board or db_card.trellolist.board.future_story_board:
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
    return db_card


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

        self._story_board = self.trello.get_board(self.settings.CURRENT_STORY_BOARD)
        self._epic_board = self.trello.get_board(self.settings.CURRENT_EPIC_BOARD)
        self._future_story_board = self.trello.get_board(self.settings.FUTURE_STORY_BOARD)
        self.db_session.add(Board(id=self._story_board.id, name=self._story_board.name, story_board=True))
        self.db_session.add(Board(id=self._epic_board.id, name=self._epic_board.name, epic_board=True))
        self.db_session.add(Board(id=self._future_story_board.id, name=self._future_story_board.name, future_story_board=True))
        self._story_lists = self._story_board.get_lists('open')
        self._epic_lists = self._epic_board.get_lists('open')
        self._future_story_lists = self._future_story_board.get_lists('open')
        self._get_epics_and_stories()

    def _get_epics_and_stories(self):

        def _ensure_checklist(trellocard):
            create_dbcard_and_ensure_checklist(self.db_session, trellocard)
        self.running_prefetches = 0

        def _prefetch_checklists(card):
            if self.running_prefetches > 3:
                sleep(8)
            self.running_prefetches += 1
            card.fetch(eager=True)
            self.running_prefetches -= 1

        def _make_checklist_futures(cards):
            loop = trollius.get_event_loop()
            futures = []
            for card in cards:
                futures.append(loop.run_in_executor(None, _prefetch_checklists, card))
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
            for future_story_list in self._future_story_lists:
                futures.append(loop.run_in_executor(None, _make_trello_list, future_story_list))

            return futures

        @trollius.coroutine
        def make_cards():
            futures = _make_cards()
            all_cards = []
            for future in futures:
                cards = yield trollius.From(future)
                all_cards += cards
                new_futures = _make_checklist_futures(cards)
                for future in new_futures:
                    yield trollius.From(future)
            raise trollius.Return(all_cards)

        now = datetime.datetime.now()
        loop = trollius.get_event_loop()
        all_cards = loop.run_until_complete(make_cards())
        for card in all_cards:
            _ensure_checklist(card)
        self.db_session.commit()
        print "time elapsed getting cards: {}".format(datetime.datetime.now() - now)

    def get_members(self):
        self.db_session = get_session()()
        for member in self.organization.get_members():
            db_user = self.db_session.query(User).filter_by(id=member.id).first()
            if db_user is None:
                db_user = User.create(self.db_session, id=member.id, username=member.username)
        self.db_session.commit()

    def clean_board_users(self):
        self.db_session = get_session()()
        for board in self.organization.get_boards('open'):
            db_board = self.db_session.query(Board).filter_by(id=board.id).first()
            if db_board is None:
                Board.create(self.db_session, id=board.id, name=board.name.replace('\xe2\x80\x99s', ''))
        self.db_session.commit()
        self.db_session = get_session()()
        for board in self.organization.get_boards('open'):
            for member in board.get_members():
                db_user = self.db_session.query(User).filter_by(id=member.id).first()
                if db_user is None:
                    print("{} is on {}".format(member.full_name, board.name))
                    # TODO: remove the member automatically
        self.db_session.commit()

def main():
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
    ti.get_members()
    ti.clean_board_users()
