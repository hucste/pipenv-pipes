#-*-coding:utf-8-*-

"""
Modified from https://github.com/wong2/pick/
Pick - create curses based interactive selection list in the terminal
LICENSE MIT
"""

import sys
import curses

__all__ = ['Picker', 'pick']


# COLOR
TRANSPARENT = -1
BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7

class Picker(object):
    """The :class:`Picker <Picker>` object

    :param options: a list of options to choose from
    :param default_index: (optional) set this if the default selected option is not the first one
    :param options_map_func: (optional) a mapping function to pass each option through before displaying
    """

    def __init__(self, options, default_index=0, options_map_func=None):

        if len(options) == 0:
            raise ValueError('options should not be an empty list')

        if default_index >= len(options):
            raise ValueError('default_index should be smaller than options')

        if options_map_func and not callable(options_map_func):
            raise ValueError('options_map_func must be a callable function')


        self.options = options
        self.options_map_func = options_map_func

        self.query = []
        self.indicator = '●'
        self.all_selected = []

        self.index = default_index
        self.custom_handlers = {}

    def register_custom_handler(self, key, func):
        self.custom_handlers[key] = func

    def config_curses(self):
        # use the default colors of the terminal
        curses.use_default_colors()
        # hide the cursor

        curses.curs_set(0)
        curses.init_pair(1, RED, TRANSPARENT)
        curses.init_pair(2, GREEN, TRANSPARENT)
        curses.init_pair(3, YELLOW, TRANSPARENT)
        curses.init_pair(4, BLUE, TRANSPARENT)
        curses.init_pair(5, MAGENTA, TRANSPARENT)
        curses.init_pair(6, CYAN, TRANSPARENT)
        curses.init_pair(7, WHITE, TRANSPARENT)


    def _start(self, screen):
        self.screen = screen
        self.config_curses()
        return self.run_loop()

    def start(self):
        return curses.wrapper(self._start)

    def move_up(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.options) - 1

    def move_down(self):
        self.index += 1
        if self.index >= len(self.options):
            self.index = 0

    def get_selected(self):
        """return the current selected option as a tuple: (option, index)
           or as a list of tuples (in case multi_select==True)
        """
        return self.options[self.index], self.index

    def get_option_lines(self):
        lines = []
        for index, option in enumerate(self.options):
            # pass the option through the options map of one was passed in
            if self.options_map_func:
                option = self.options_map_func(option)

            if index == self.index:
                prefix = self.indicator
            else:
                prefix = len(self.indicator) * ' '

            if index == self.index:
                color = curses.color_pair(3)
            else:
                color = curses.color_pair(7)
            text = '{0} {1}'.format(prefix, option)
            line = (text, color)
            lines.append(line)

        return lines

    def get_lines(self):
        title_lines = [
            ('  ===================', curses.color_pair(2)),
            ('  Pipenv Environments', curses.color_pair(2)),
            ('  ===================', curses.color_pair(2)),
            ('\n', 0)
        ]
        option_lines = self.get_option_lines()
        lines = title_lines + option_lines
        current_line = self.index + len(title_lines) + 1
        return lines, current_line


    def draw(self):
        """draw the curses ui on the screen, handle scroll if needed"""
        self.screen.clear()

        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()
        max_rows = max_y - y  # the max rows we can draw

        lines, current_line = self.get_lines()

        # calculate how many lines we should scroll, relative to the top
        scroll_top = getattr(self, 'scroll_top', 0)
        if current_line <= scroll_top:
            scroll_top = 0
        elif current_line - scroll_top > max_rows:
            scroll_top = current_line - max_rows
        self.scroll_top = scroll_top

        lines_to_draw = lines[scroll_top:scroll_top + max_rows]

        for n, line in enumerate(lines_to_draw):
            if type(line) is tuple:
                self.screen.addnstr(y, x, line[0], max_x-2, line[1])
            else:
                self.screen.addnstr(y, x, line, max_x-2)
            y += 1

            # Adde space before Exit
            if n == len(lines_to_draw) - 2:
                y += 1

        query = '$ {}'.format(''.join(self.query))
        self.screen.addnstr(y + 2, x + 2, query, max_x-2, curses.color_pair(2))
        self.screen.refresh()

    def run_loop(self):
        from curses import ascii
        KEYS_UP = (curses.KEY_UP, )
        KEYS_DOWN = (curses.KEY_DOWN, )
        KEYS_ENTER = (
            curses.KEY_ENTER,
            curses.KEY_RIGHT,
            ord('\n'),             # MacOs Enter
            ord('\r'),
            32,                     # Space
            )
        KEYS_CLEAR = (
            curses.KEY_DC,         # MacOs Delete
            ascii.DEL,             # MacOs Backpace
            curses.KEY_BACKSPACE,  # MacOs fn + del
            )
        KEYS_ESCAPE = (
            21,                    # MacOs Escape
            5
            )

        while True:
            self.draw()
            c = self.screen.getch()
            # Key Debug
            # self.options[0] = str(chr(c) + '|' + str(c))
            # self.draw()
            if c in KEYS_UP:
                self.query = []
                self.move_up()
            elif c in KEYS_DOWN:
                self.query = []
                self.move_down()
            elif c in KEYS_ENTER:
                return self.get_selected()
            elif c in self.custom_handlers:
                ret = self.custom_handlers[c](self)
                if ret:
                    return ret
            elif c == curses.KEY_HOME:
                self.query = []
                self.index = 0
            elif c == curses.KEY_END:
                self.query = []
                self.index = len(self.options) - 2
            elif c in KEYS_CLEAR:
                self.query = []
            elif c in KEYS_ESCAPE:
                sys.exit(0)
            else:
                self.query.append(chr(c))
                for n, option in enumerate(self.options):
                    if option.startswith(''.join(self.query)):
                        self.index = n

