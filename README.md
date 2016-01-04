# trello-traceability

This is awful, awful code. :)

Here's a little docs to help you out:

First, get your API key and secret from Trello. Then look in the docs/how-to-get-trello-keys.txt for how to get your OAUTH key.

Copy settings.py.tpl to settings.py and fill in those fields. Then run

`./cmds.py test_conn`

Then run

`./cmds.py find_boards` to have it print out boards and ids. Fill in your board ids in settings.py

Then run

```
./cmds.py makedb
./cmds.py filldb
```
To fill the local database of trello information

Then, to get into the gui, run

`./rungui.py`


