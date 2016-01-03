#!/usr/bin/env python

import urwid
from trello import TrelloClient

import models
import settings
from models import Board, get_session, TrelloList
from trellointerface import create_dbcard_and_ensure_checklist


class RemoveOrgUser(object):
    def __init__(self, parent):
        self.items = [urwid.Text("foo"), urwid.Text("bar")]

        self.main_content = urwid.SimpleListWalker(
            [urwid.AttrMap(w, None, 'reveal focus') for w in self.items])

        self.parent = parent
        self.listbox = urwid.ListBox(self.main_content)

    @property
    def widget(self):
        return urwid.AttrWrap(self.listbox, 'body')

    def handle_input(self, k):
        if k in ('u', 'U'):
            self.parent.set_view(Top)

class NoRefocusColumns(urwid.Columns):
    def keypress(self, size, key):
        return key

class NoRefocusPile(urwid.Pile):
    def keypress(self, size, key):
        return key

class TrelloCard(object):
    def __init__(self, card, trello):
        self.card = card
        self.trello = trello
        self.initialize()

    def initialize(self):
        raise NotImplementedError()

    @property
    def trellocard(self):
        return self.trello.get_card(self.card.id)

    @property
    def url(self):
        return self.trellocard.url
    @property
    def id(self):
        return self.card.id
    @property
    def name(self):
        return self.card.name


class Story(TrelloCard):
    def initialize(self):
        pass

    @property
    def meta_checklist(self):
        tc = self.trellocard
        tc.fetch(eager=True)
        return [ checklist for checklist in tc.checklists if checklist.id == self.card.magic_checklist_id ][0]

    def connect_to(self, epic):
        self.meta_checklist.add_checklist_item("Epic Connection: {}: {}".format(epic.id, epic.url))
        epic.story_checklist.add_checklist_item("{}: {}".format(self.id, self.url))
        self.card.connected_to_id = epic.id

    @property
    def more_info_area(self):
        if self.card.connected_to is None:
            return "No connection"
        else:
            epic = self.card.connected_to
            return "Connected to {}".format(epic.name)

class Epic(TrelloCard):

    def initialize(self):
        pass

    @property
    def story_checklist(self):
        tc = self.trellocard
        tc.fetch(eager=True)
        return [ checklist for checklist in tc.checklists if checklist.id == self.card.magic_checklist_id ][0]

    @property
    def more_info_area(self):
        return ""

class Panel(object):
    def __init__(self, parent, board, card_cls):
        self.db_session = parent.db_session
        self.trello = parent.trello
        self.parent = parent
        self.board = board
        self.card_list_ptr = 0
        self.card_lists = self.db_session.query(TrelloList).filter_by(board=self.board)
        self.card_cls = card_cls
        self.content = urwid.SimpleListWalker(
            [urwid.AttrMap(w, None, 'reveal focus') for w in self.items])
        self.listbox = urwid.ListBox(self.content)

    def reset_content(self):
        while self.content:
            self.content.pop()
        self.content += [ urwid.AttrMap(w, None, 'reveal focus') for w in self.items]
        if len(self.items) >2:
            self.listbox.set_focus(2)
            # TODO: this doesn't belong here exactly.
            self.parent.more_info_area.set_text(self.card.more_info_area)

    @property
    def trelloboard(self):
        return self.trello.get_board(self.board.id)

    @property
    def items(self):
        items = [urwid.Text(self.card_list.name), urwid.Text('-=-=-=-=-=-=-=-=-=-')]
        items += [urwid.Text("{}] {}".format(i, card.name)) for i, card in enumerate(self.get_cards())]
        return items

    @property
    def card_list(self):
        return self.card_lists[self.card_list_ptr]

    def get_cards(self):
        db_cards = self.db_session.query(models.Card).filter_by(trellolist=self.card_list)
        self.cards = [ self.card_cls(card, self.trello) for card in db_cards]
        return self.cards

    def set_focus(self, idx):
        self.listbox.set_focus(idx)

    @property
    def card(self):
        return self.cards[self.listbox.get_focus()[1] - 2]

    def go_left(self):
        if self.card_list_ptr > 0:
            self.card_list_ptr -= 1
            self.reset_content()

    def go_right(self):
        if self.card_list_ptr < self.card_lists.count() - 1:
            self.card_list_ptr += 1
            self.reset_content()

    def move_up(self):
        focus_widget, idx = self.listbox.get_focus()
        if idx > 2:
            idx = idx - 1
            self.listbox.set_focus(idx)
            self.parent.more_info_area.set_text(self.card.more_info_area)
    def move_down(self):
        focus_widget, idx = self.listbox.get_focus()
        if idx < len(self.content) - 1:
            idx = idx + 1
            self.listbox.set_focus(idx)
            self.parent.more_info_area.set_text(self.card.more_info_area)


class Connect(object):
    def __init__(self, parent):
        self.db_session = get_session()()
        self.mid_cmd = self.old_focus = None
        self.parent = parent
        self.story_board = self.db_session.query(Board).filter_by(story_board=True).first()
        self.epic_board = self.db_session.query(Board).filter_by(epic_board=True).first()
        self.future_story_board = self.db_session.query(Board).filter_by(future_story_board=True).first()
        self.left_panel = self.current_story_panel = Panel(self, board=self.story_board, card_cls=Story)
        self.future_story_panel = Panel(self, board=self.future_story_board, card_cls=Story)
        self.right_panel = Panel(self, board=self.epic_board, card_cls=Epic)
        self.left_panel.set_focus(2)

        self.columns = NoRefocusColumns([self.left_panel.listbox, self.right_panel.listbox], focus_column=0)
        self.more_info_area = urwid.Text(self.left_panel.card.more_info_area)
        self.command_area = urwid.Edit(caption="")
        self.edit_area_listbox = urwid.ListBox([urwid.Text("-=-=-=-=-=-=-=-"), self.more_info_area, self.command_area])
            #urwid.AttrMap(self.command_area, "notfocus", "focus")])
        self.frame = NoRefocusPile([self.columns, self.edit_area_listbox], focus_item=0)

    @property
    def widget(self):
        return urwid.AttrWrap(self.frame, 'body')

    @property
    def trello(self):
        return self.parent.trelloclient

    def _complete(self):
        self.command_area.set_edit_text("")
        self.mid_cmd = False
        self.left_panel.listbox.set_focus(self.old_focus)
        self.frame.set_focus(0)

    def complete_n(self):
        output = self.command_area.get_edit_text().strip()
        card_list = self.right_panel.card_list
        trello_list = self.right_panel.trelloboard.get_list(card_list.id)
        card = trello_list.add_card(output)
        db_card = create_dbcard_and_ensure_checklist(self.db_session, card, prefetch_checklists=True)
        self.db_session.commit()
        self.db_session = get_session()()
        self.left_panel.card.connect_to(Epic(db_card, self.trello))
        self.right_panel.reset_content()
        self._complete()

    def complete_c(self):
        output = int(self.command_area.get_edit_text())
        self._complete()
        self.left_panel.card.connect_to(self.right_panel.cards[output])
        self.db_session.commit()

    def switch_story_boards(self):
        if self.left_panel == self.current_story_panel:
            self.left_panel = self.future_story_panel
        else:
            self.left_panel = self.current_story_panel
        self.columns.widget_list = [self.left_panel.listbox, self.right_panel.listbox]
        self.columns.set_focus(0)
        self.left_panel.listbox.set_focus(2)

    def handle_input(self, k):
        if self.mid_cmd:
            if k == 'esc':
                self._complete()
            if k == 'enter':
                if self.mid_cmd == 'n':
                    self.complete_n()
                elif self.mid_cmd == 'c':
                    self.complete_c()
            else:
                self.command_area.keypress([0], k)
            return
        if k in ('u', 'U'):
            self.parent.set_view(Top)
        if k == 's':
            self.switch_story_boards()
        if k == 'c':
            self.frame.set_focus(1)
            self.command_area.set_edit_pos(0)
            self.mid_cmd = 'c'
            self.old_focus = self.left_panel.listbox.get_focus()[1]
        if k == 'n':
            self.frame.set_focus(1)
            self.command_area.set_edit_pos(0)
            self.mid_cmd = 'n'
            self.old_focus = self.left_panel.listbox.get_focus()[1]
        # navigation
        elif k == 'j':
            self.right_panel.go_left()
        elif k == 'l':
            self.right_panel.go_right()
        elif k == 'a':
            self.left_panel.go_left()
        elif k == 'd':
            self.left_panel.go_right()
        elif k == 'up':
            self.left_panel.move_up()
        elif k == 'down':
            self.left_panel.move_down()

VIEWS = {
    "Remove Organization User": RemoveOrgUser,
    "Connect Stories to Epics": Connect,

}
class Top(object):
    def __init__(self, parent):
        self.commands = [urwid.Text(text) for text in VIEWS.keys() ]

        self.main_content = urwid.SimpleListWalker(
            [urwid.Text('Commands'),
             urwid.Text('-=-=-=-=-=-=-=-=-=-')]+
            [urwid.AttrMap(w, None, 'reveal focus') for w in self.commands])

        self.listbox = urwid.ListBox(self.main_content)
        self.listbox.set_focus(2)
        self.parent = parent

    @property
    def widget(self):
        return urwid.AttrWrap(self.listbox, 'body')

    def enter_command(self):
        focus_widget, idx = self.listbox.get_focus()
        item = self.main_content[idx].original_widget.text
        view = VIEWS[item]
        self.parent.set_view(view)

        # focus_widget, idx = self.listbox.get_focus()
        # item = self.main_content[idx].original_widget.text
        # new_item = urwid.Text(item)
        # self.commands.append(new_item)
        # self.main_content.append(urwid.AttrMap(new_item, None, 'reveal focus'))

    def handle_input(self, k):
        if k == 'up':
            focus_widget, idx = self.listbox.get_focus()
            if idx > 2:
                idx = idx - 1
                self.listbox.set_focus(idx)

        elif k == 'down':
            focus_widget, idx = self.listbox.get_focus()
            if idx < len(self.main_content) - 1:
                idx = idx + 1
                self.listbox.set_focus(idx)

        elif k == 'enter':
            self.enter_command()


class TrelloTraceability:
    palette = [
        ('body', 'black', 'light gray'),
        ('focus', 'light gray', 'dark blue', 'standout'),
        ('head', 'yellow', 'black', 'standout'),
        ('foot', 'light gray', 'black'),
        ('key', 'light cyan', 'black','underline'),
        ('title', 'white', 'black', 'bold'),
        ('flag', 'dark gray', 'light gray'),
        ('error', 'dark red', 'light gray'),
        ]

    cmdstrings = [
        ('title', "Commands"), "    ",
        ('key', "Q"), ' ',
        ('key', 'U')
        ]

    def __init__(self):
        self.current_view = Top(self)
        # header and footer
        self.header = urwid.Text( "Trello Traceability" )

        self.cmds = urwid.AttrWrap(urwid.Text(self.cmdstrings),
            'foot')
        self.view = urwid.Frame(
            self.current_view.widget,
            header=urwid.AttrWrap(self.header, 'head' ),
            footer=self.cmds )

        self.trelloclient = TrelloClient(
            api_key=settings.TRELLO_API_KEY,
            api_secret=settings.TRELLO_API_SECRET,
            token=settings.TRELLO_OAUTH_TOKEN,
        )
        self.organization = self.trelloclient.get_organization(settings.TRELLO_ORGANIZATION_ID)

    def set_view(self, cls):
        self.current_view = cls(self)
        self.view.body = self.current_view.widget

    def main(self):
        """Run the program."""

        self.loop = urwid.MainLoop(self.view, self.palette,
            unhandled_input=self.unhandled_input)
        self.loop.run()

    def unhandled_input(self, k):
        if k in ('q','Q'):
            raise urwid.ExitMainLoop()
        else:
            self.current_view.handle_input(k)


def main():
    TrelloTraceability().main()


if __name__=="__main__":
    main()