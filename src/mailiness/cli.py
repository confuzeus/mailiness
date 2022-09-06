from . import handlers
from datetime import datetime
import argparse

from . import commands


def main():
    parser = argparse.ArgumentParser(description="Manage your mail server.")
    parser.add_argument("--version", "-v", action="store_true", default=False)

    subparsers = parser.add_subparsers()

    dkim_parser = subparsers.add_parser("dkim", help="dkim commands")
    dkim_subparsers = dkim_parser.add_subparsers()
    dkim_keygen = dkim_subparsers.add_parser("keygen", help="Generate dkim key pair")
    dkim_keygen.add_argument("domain", type=str, help="example.com")
    selector_timestamp = datetime.now().strftime("%Y%m%d")
    dkim_keygen.add_argument(
        "selector",
        type=str,
        help=f"Unique string to different between different dkim keys. Example: {selector_timestamp}",
    )
    dkim_keygen.add_argument("--print", "-p", action="store_true", default=True, help="Print keys to stdout (default: yes)")
    dkim_keygen.add_argument("--save", action="store_true", default=False, help="Save private key to configure directory (default: no)")
    dkim_keygen.set_defaults(func=handlers.handle_dkim_keygen)

    args = parser.parse_args()
    args.func(args)

    if args.version:
        commands.print_version()


if __name__ == "__main__":
    main()
