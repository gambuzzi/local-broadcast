from local_broadcast import init
import asyncio
from curses import ERR, KEY_F9, curs_set, wrapper
import curses
import signal
from random import randint

async def display_main(stdscr):  
    done = False

    curs_set(2)
    stdscr.nodelay(True)

    status_bar = " Press 'F9' to exit"

    stdscr.erase()

    # Create top window
    top_win = stdscr.subwin(curses.LINES - 3, curses.COLS, 0, 0)
    top_win.scrollok(True)

    # Create input window

    input_win = stdscr.subwin(1, curses.COLS, curses.LINES - 2, 0)

    # Create status window
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    
    status_win = stdscr.subwin(1, curses.COLS, curses.LINES - 1, 0)
    status_win.bkgd(" ", curses.color_pair(1))
    status_win.addstr(0, 0, status_bar, curses.color_pair(1))

    stdscr.refresh()

    input_win.move(0, 0)
    input_win.refresh()

    def resize_display(signal, frame):
        # Resize and move the windows
        top_win.resize(curses.LINES - 3, curses.COLS)
        top_win.mvwin(0, 0)
        input_win.resize(1, curses.COLS)
        input_win.mvwin(curses.LINES - 2, 0)
        status_win.resize(1, curses.COLS)
        status_win.mvwin(curses.LINES - 1, 0)
        top_win.refresh()
        input_win.refresh()
        status_win.refresh()

        input_win.move(0, 0)

        stdscr.refresh()

    signal.signal(signal.SIGWINCH, resize_display)

    def draw_buffer(buffer):
        input_win.erase()
        input_win.addstr(0, 0, buffer)
        input_win.move(0, len(buffer))
        input_win.refresh()

    async def top_win_addstr(string):
        top_win.addstr(f"{string}\n")
        top_win.refresh()

    async def set_status(msg):
        status_win.addstr(
            0, 0, f"{status_bar} - current host: {msg}", curses.color_pair(1)
        )
        status_win.refresh()


    # create a task to run the zeroconf service
    # asyncio.create_task(zeroconf_init(top_win_addstr))
    send_string, deinit = await init("chat", top_win_addstr, set_status)

    buffer = ""
    while not done:
        try:
            char = stdscr.get_wch()
        except curses.error:
            char = ERR

        if char == ERR:
            await asyncio.sleep(0.1)
        elif char == KEY_F9:
            done = True
        elif char == "\n":
            await send_string(buffer)
            buffer = ""
            draw_buffer(buffer)
        elif (char == "\x7f" or char == 263 ) and buffer:
            buffer = buffer[:-1]
            draw_buffer(buffer)
        elif isinstance(char, str) and char.isprintable():
            buffer += char
            draw_buffer(buffer)
        else:
            status_win.addstr(0, curses.COLS // 2, f"Unknown key: {char!r}")
            status_win.refresh()

    await deinit()

def main(stdscr) -> None:
    return asyncio.run(display_main(stdscr))

if __name__ == "__main__":
    wrapper(main)