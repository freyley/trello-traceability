#!/usr/bin/env python

import urwid
from trello import TrelloClient

import models
import settings
from models import Board, get_session, TrelloList


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
        import ipdb; ipdb.set_trace()

    def connect_to(self, epic):
        self.meta_checklist.add_checklist_item("Epic Connection: {}: {}".format(epic.id, epic.url))
        epic.story_checklist.add_checklist_item("{}: {}".format(self.id, self.url))

    @property
    def connected_to(self):
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
        import ipdb; ipdb.set_trace()

class Connect(object):
    def __init__(self, parent):
        self.db_session = get_session()()
        self.mid_cmd = self.old_focus = None
        self.parent = parent
        self.get_trello_lists()
        self.set_left_content()
        self.set_right_content()
        self.left_content = urwid.SimpleListWalker(
            [urwid.AttrMap(w, None, 'reveal focus') for w in self.left_items])
        self.right_content = urwid.SimpleListWalker(
            [urwid.AttrMap(w, None, 'reveal focus') for w in self.right_items])
        self.left_listbox = urwid.ListBox(self.left_content)
        self.right_listbox = urwid.ListBox(self.right_content)
        self.left_listbox.set_focus(2)

        self.columns = NoRefocusColumns([self.left_listbox, self.right_listbox], focus_column=0)
        self.more_info_area = urwid.Text(self.story.connected_to)
        self.command_area = urwid.Edit(caption="")
        self.edit_area_listbox = urwid.ListBox([urwid.Text("-=-=-=-=-=-=-=-"), self.more_info_area, self.command_area])
            #urwid.AttrMap(self.command_area, "notfocus", "focus")])
        self.frame = NoRefocusPile([self.columns, self.edit_area_listbox], focus_item=0)

    def set_left_content(self, reset=False):
        self.left_items = [urwid.Text(self.story_list.name), urwid.Text('-=-=-=-=-=-=-=-=-=-')]
        self.left_items += [urwid.Text(story.name) for story in self.get_stories()]
        if reset:
            while self.left_content:
                self.left_content.pop()
            self.left_content += [ urwid.AttrMap(w, None, 'reveal focus') for w in self.left_items]
            if len(self.left_items):
                self.left_listbox.set_focus(2)
                self.more_info_area.set_text(self.story.connected_to)


    def set_right_content(self, reset=False):
        self.right_items = [urwid.Text(self.epic_list.name), urwid.Text('-=-=-=-=-=-=-=-=-=-')]
        self.right_items += [urwid.Text("{}] {}".format(i, epic.name)) for i, epic in enumerate(self.get_epics())]
        if reset:
            while self.right_content:
                self.right_content.pop()
            self.right_content += self.right_items

    @property
    def widget(self):
        return urwid.AttrWrap(self.frame, 'body')

    @property
    def trello(self):
        return self.parent.trelloclient

    def get_trello_lists(self):
        self.story_board = self.db_session.query(Board).filter_by(story_board=True).first()
        self.epic_board = self.db_session.query(Board).filter_by(epic_board=True).first()
        self.story_lists = self.db_session.query(TrelloList).filter_by(board=self.story_board)
        self.epic_lists = self.db_session.query(TrelloList).filter_by(board=self.epic_board)
        self.epic_list_ptr = self.story_list_ptr = 0

    @property
    def story_list(self):
        return self.story_lists[self.story_list_ptr]
    @property
    def epic_list(self):
        return self.epic_lists[self.epic_list_ptr]

    def get_stories(self):
        cards = self.db_session.query(models.Card).filter_by(trellolist=self.story_list)
        self.stories = [ Story(card, self.trello) for card in cards]
        return self.stories

    def get_epics(self):
        cards = self.db_session.query(models.Card).filter_by(trellolist=self.epic_list)
        self.epics = [ Epic(card, self.trello) for card in cards ]
        return self.epics

    @property
    def story(self):
        return self.stories[self.left_listbox.get_focus()[1] - 2]

    def handle_input(self, k):
        if self.mid_cmd:
            if k == 'esc':
                self.mid_cmd = False
                self.left_listbox.set_focus(self.old_focus)
                self.frame.set_focus(0)
            if k == 'enter':
                self.mid_cmd = False
                self.left_listbox.set_focus(self.old_focus)
                self.frame.set_focus(0)
                output = int(self.command_area.get_edit_text())
                self.command_area.set_edit_text("")
                self.story.connect_to(self.epics[output])
            else:
                self.command_area.keypress([0], k)
            return
        if k in ('u', 'U'):
            self.parent.set_view(Top)
        if k == 'c':
            self.frame.set_focus(1)
            self.command_area.set_edit_pos(0)
            self.mid_cmd = True
            self.old_focus = self.left_listbox.get_focus()[1]
        # navigation
        elif k == 'j':
            if self.epic_list_ptr > 0:
                self.epic_list_ptr -= 1
                self.set_right_content(reset=True)
        elif k == 'l':
            if self.epic_list_ptr < self.epic_lists.count()-1:
                self.epic_list_ptr += 1
                self.set_right_content(reset=True)
        elif k == 'a':
            if self.story_list_ptr > 0:
                self.story_list_ptr -= 1
                self.set_left_content(reset=True)
        elif k == 'd':
            if self.story_list_ptr < self.story_lists.count()-1:
                self.story_list_ptr += 1
                self.set_left_content(reset=True)
        elif k == 'up':
            focus_widget, idx = self.left_listbox.get_focus()
            if idx > 2:
                idx = idx - 1
                self.left_listbox.set_focus(idx)
                self.more_info_area.set_text(self.story.connected_to)

        elif k == 'down':
            focus_widget, idx = self.left_listbox.get_focus()
            if idx < len(self.left_content) - 1:
                idx = idx + 1
                self.left_listbox.set_focus(idx)
                self.more_info_area.set_text(self.story.connected_to)


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