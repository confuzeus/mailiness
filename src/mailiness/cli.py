import argparse
from typing import Optional, Sequence

from mailiness import g

from . import commands, dkim, handlers

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
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Don't print keys to stdout.",
    )
    dkim_keygen.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="Save private key to configure directory (default: no)",
    )
    dkim_keygen.set_defaults(func=handlers.handle_dkim_keygen, func_args=True)

    dkim_show = dkim_subparsers.add_parser("show", help="display a domain's DKIM key")
    dkim_show.add_argument("domain", help="The domain whose key to show")
    dkim_show.set_defaults(func=handlers.handle_dkim_show, func_args=True)


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
    domain_delete.add_argument(
        "--yes",
        "-y",
        action="store_true",
        default=False,
        help="Assume yes on all choices.",
    )
    domain_delete.set_defaults(func=handlers.handle_domain_delete, func_args=True)

    domain_list = domain_subparsers.add_parser("list", help="List domain names")
    domain_list.set_defaults(func=handlers.handle_domain_list, func_args=True)


def add_user_parser(parser):
    user_parser = parser.add_parser("user", help="user commands")
    user_parser.set_defaults(func=user_parser.print_help, func_args=False)
    user_subparsers = user_parser.add_subparsers()

    user_add = user_subparsers.add_parser("add", help="Add a user")
    user_add.add_argument("email", type=str, help="john@smith.com")
    user_add.add_argument("quota", help="The user's disk quota in GB.", type=int)
    user_add_password_group = user_add.add_mutually_exclusive_group()
    user_add_password_group.add_argument(
        "password",
        type=str,
        nargs="?",
        help="The user's password. Will be prompted if not provided",
    )
    user_add_password_group.add_argument(
        "--random-password",
        action="store_true",
        default=False,
        help="Set the user's password to a random value.",
    )
    user_add.set_defaults(func=handlers.handle_user_add, func_args=True)

    user_edit = user_subparsers.add_parser("edit", help="Edit a user")
    user_edit.add_argument("email", help="The target's current email address")
    user_edit.add_argument(
        "--new-email", "-e", help="Change the user's email address to this new one."
    )
    user_edit_password_group = user_edit.add_mutually_exclusive_group()
    user_edit_password_group.add_argument(
        "--password", "-p", help="Set the user's password to this value"
    )
    user_edit_password_group.add_argument(
        "--random-password",
        action="store_true",
        default=False,
        help="Set the user's password to a random value.",
    )
    user_edit_password_group.add_argument(
        "--password-prompt",
        action="store_true",
        default=False,
        help="Prompt for the user's new password",
    )
    user_edit.add_argument("--quota", "-q", type=int, help="Set the user's quota in GB")
    user_edit.set_defaults(func=handlers.handle_user_edit, func_args=True)

    user_list = user_subparsers.add_parser("list", help="List users")
    user_list.add_argument("--domain", "-d", help="List users for this domain only.")
    user_list.set_defaults(func=handlers.handle_user_list, func_args=True)

    user_delete = user_subparsers.add_parser("delete", help="Delete a user.")
    user_delete.add_argument("email", help="The target's email address.")
    user_delete.add_argument(
        "--mail",
        "-m",
        action="store_true",
        help="Delete the user's existing emails as well.",
    )
    user_delete.set_defaults(func=handlers.handle_user_delete, func_args=True)


def add_alias_parser(parser):
    alias_parser = parser.add_parser("alias", help="alias commands")
    alias_subparsers = alias_parser.add_subparsers()

    alias_add = alias_subparsers.add_parser("add", help="Add an alias")
    alias_add.add_argument("from_address", help="From address.")
    alias_add.add_argument("to_address", help="To address.")
    alias_add.set_defaults(func=handlers.handle_alias_add, func_args=True)

    alias_list = alias_subparsers.add_parser(
        "list", help="List all addresses pointing to this address."
    )
    alias_list.add_argument(
        "to_address", help="The address other addresses are pointing to."
    )
    alias_list.set_defaults(func=handlers.handle_alias_list, func_args=True)

    alias_edit = alias_subparsers.add_parser("edit", help="Edit an alias.")
    alias_edit.add_argument("from_address", help="The target from_address.")
    alias_edit.add_argument(
        "--new-from", "-f", help="Change the from address to this one."
    )
    alias_edit.add_argument("--to", "-t", help="Change the to address to this one.")
    alias_edit.set_defaults(func=handlers.handle_alias_edit, func_args=True)

    alias_delete = alias_subparsers.add_parser("delete", help="Delete an alias")
    alias_delete.add_argument("from_address", help="The from address.")
    alias_delete.set_defaults(func=handlers.handle_alias_delete, func_args=True)


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

    add_user_parser(subparsers)

    add_alias_parser(subparsers)

    return parser


def main(args: Optional[Sequence] = None):

    parser = get_parser()

    args = parser.parse_args(args=args)

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
