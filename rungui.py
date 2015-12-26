#!/usr/bin/env python

import urwid

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

class Connect(object):
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


VIEWS = {
    "Remove Organization User": RemoveOrgUser,
    "Connect Stories to Epics": Connect,

}
class Top(object):
    def __init__(self, parent):
        self.commands = [urwid.Text(text) for text in VIEWS.keys() ]

        self.main_content = urwid.SimpleListWalker(
            [urwid.AttrMap(w, None, 'reveal focus') for w in self.commands])

        self.listbox = urwid.ListBox(self.main_content)
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
            if idx > 0:
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