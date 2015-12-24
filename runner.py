
def help(actions):
    for action in actions.values():
        print "{}: {}".format(action.cmdstring, action.description)


def runner(actions, prompt, back_action=None, **kwargs):
    while True:
        cmd = raw_input(prompt)
        action = actions.get(cmd)
        if cmd == 'h':
            help(actions)
        elif cmd == back_action:
            return
        elif action is None:
            print "Unknown action. 'h' for help"
        else:
            action.cmdfunc(**kwargs)


def _choose_from_list(elements, print_func):
    for i, element in enumerate(elements):
        print "{})".format(i) + print_func(element)
    cmd = ""
    while True:
        cmd = raw_input("Select one? (b to go back)")
        if cmd == 'b':
            return
        try:
            cmd = int(cmd)
        except ValueError:
            continue
        return elements[cmd]