
class TabCompleter:
    """
    A tab completer that can either complete from
    the filesystem or from a list.
    """
    def pathCompleter(self, text, state):
        """
        This is the tab completer for systems paths.
        Only tested on *nix systems
        """
        line = readline.get_line_buffer().split()
        return [x for x in glob.glob(text + '*')][state]

    def createListCompleter(self, ll):
        """
        This is a closure that creates a method that autocompletes from the given list.
        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the listCompleter function with a list to complete
        from.
        """
        def listCompleter(text, state):
            line = readline.get_line_buffer()

            if not line:
                return [c + " " for c in ll][state]

            else:
                return [c + " " for c in ll if c.startswith(line)][state]
        self.listCompleter = listCompleter