from rich.console import Console

import mailiness

console = Console()


def print_version():
    print(f"Mailiness - {mailiness.__version__}")
