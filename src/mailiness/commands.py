import mailiness
import base64
from rich.console import Console
from rich.table import Table
from . import dkim

console = Console()


def print_version():
    print(f"Mailiness - {mailiness.__version__}")
