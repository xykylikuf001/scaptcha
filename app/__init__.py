from typing import Optional


class Bcolors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(
        text: str,
        start_color: str,
        end_color: Optional[str] = Bcolors.ENDC,
        end: Optional[str] = '\n'
):
    print('%s%s%s' % (start_color, text, end_color), end=end)


def input_colored(text: str, start_color: str, end_color: Optional[str] = Bcolors.ENDC):
    return input("%s%s%s" % (start_color, text, end_color))
