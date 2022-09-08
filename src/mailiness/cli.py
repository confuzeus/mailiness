import argparse

from mailiness import g

from . import commands, handlers, dkim

selector_timestamp = dkim.get_default_selector()


def add_dkim_parser(parser):
    dkim_parser = parser.add_parser("dkim", help="dkim commands")
    dkim_parser.set_defaults(func=dkim_parser.print_help, func_args=False)
    dkim_subparsers = dkim_parser.add_subparsers()
    dkim_keygen = dkim_subparsers.add_parser("keygen", help="Generate dkim key pair")
    dkim_keygen.add_argument("domain", type=str, help="example.com")
    dkim_keygen.add_argument(
        "selector",
        type=str,
        default=selector_timestamp,
        help=f"Unique string to different between different dkim keys. Example: {selector_timestamp}",
        nargs="?",
    )
    dkim_keygen.add_argument(
        "--print",
        "-p",
        action="store_true",
        default=True,
        help="Print keys to stdout (default: yes)",
    )
    dkim_keygen.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="Save private key to configure directory (default: no)",
    )
    dkim_keygen.set_defaults(func=handlers.handle_dkim_keygen, func_args=True)


def add_domain_parser(parser):
    domain_parser = parser.add_parser("domain", help="domain commands")
    domain_parser.set_defaults(func=domain_parser.print_help, func_args=False)
    domain_subparsers = domain_parser.add_subparsers()

    domain_add = domain_subparsers.add_parser("add", help="Add a domain name")
    domain_add.add_argument("name", help="example.com")
    domain_add.add_argument(
        "--dkim",
        action="store_true",
        default=False,
        help="Generate and save a DKIM key pair in one fell swoop.",
    )
    domain_add.add_argument(
        "--selector", nargs="?", default=selector_timestamp, help="DKIM selector"
    )
    domain_add.set_defaults(func=handlers.handle_domain_add, func_args=True)

    domain_edit = domain_subparsers.add_parser("edit", help="Edit a domain name")
    domain_edit_subparsers = domain_edit.add_subparsers()

    domain_edit_name = domain_edit_subparsers.add_parser(
        "name", help="Change the name of a domain name"
    )
    domain_edit_name.add_argument("old_name", type=str, help="Old name")
    domain_edit_name.add_argument("new_name", type=str, help="New name")
    domain_edit_name.set_defaults(func=handlers.handle_domain_edit_name, func_args=True)

    domain_delete = domain_subparsers.add_parser(
        "delete", help="Delete a domain name and all associated users and aliases"
    )
    domain_delete.add_argument("name", help="Domain name to delete")
    domain_delete.add_argument(
        "--mailbox",
        action="store_true",
        default=False,
        help="Delete mailboxes as well.",
    )
    domain_delete.add_argument(
        "--dkim", action="store_true", default=False, help="Delete DKIM key as well."
    )
    domain_delete.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Delete domain and mailboxes, DKIM keys, etc.",
    )
    domain_delete.set_defaults(func=handlers.handle_domain_delete, func_args=True)

    domain_list = domain_subparsers.add_parser("list", help="List domain names")
    domain_list.set_defaults(func=handlers.handle_domain_list, func_args=True)


def get_parser():
    parser = argparse.ArgumentParser(description="Manage your mail server.")
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        default=False,
        help="Show version number.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Work in debug mode. Most destructive actions will be prevented.",
    )
    subparsers = parser.add_subparsers()

    add_dkim_parser(subparsers)

    add_domain_parser(subparsers)

    return parser


def main():

    parser = get_parser()

    args = parser.parse_args()

    g.debug = args.debug

    if args.version:
        commands.print_version()

    if getattr(args, "func", None):
        if args.func_args:
            args.func(args)
        else:
            args.func()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
