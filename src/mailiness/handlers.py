import shutil
import tempfile
from argparse import Namespace
from pathlib import Path

from rich.console import Console

from . import dkim, repo, settings

console = Console()


def handle_dkim_keygen(args: Namespace):
    key = dkim.DKIM(domain=args.domain, selector=args.selector)

    print(key.private_key_as_pem())

    if args.print:
        print(key.dns_txt_record())

    if args.save:
        key.save_private_key()


def handle_domain_add(args: Namespace):
    domain_repo = repo.DomainRepository()
    tbl = domain_repo.create(args.name)
    console.print(f"{args.name} added to database")
    console.print(tbl)

    if args.dkim:
        key = dkim.DKIM(domain=args.name, selector=args.selector)
        key.save_private_key()
        print(key.dns_txt_record())


def handle_domain_edit_name(args: Namespace):
    domain_repo = repo.DomainRepository()
    tbl = domain_repo.edit("name", args.old_name, args.new_name)
    console.print(f"{args.old_name} changed to {args.new_name}")
    console.print(tbl)


def handle_domain_delete(args: Namespace):
    domain_repo = repo.DomainRepository()
    answer = input(f"Are you sure you want to delete {args.name}? (y/n)")

    while answer != "y" and answer != "n":
        answer = input(f"Are you sure you want to delete {args.name}? (y/n)")

    if answer == "y":
        domain_repo.delete(args.name)
        console.print(f"{args.name} deleted.")

        def _delete_dkim_key(domain):
            key = dkim.DKIM(domain=domain)
            key.delete_key()
            print("Private key deleted.")

        def _delete_mailbox_directory(domain):
            if args.debug:
                vmail_directory = Path(tempfile.mkdtemp())
            else:
                vmail_directory = Path(settings.VMAIL_DIRECTORY)

            shutil.rmtree(vmail_directory / domain)
            print("Mailboxes deleted.")

        if args.all:
            _delete_dkim_key(args.domain)
            _delete_mailbox_directory(args.domain)
        else:
            if args.dkim:
                _delete_dkim_key(args.domain)
            elif args.mailbox:
                _delete_mailbox_directory()
    else:
        console.print(f"{args.name} not deleted.")


def handle_domain_list(args: Namespace):
    domain_repo = repo.DomainRepository()
    tbl = domain_repo.index()
    console.print(tbl)


def handle_user_add(args: Namespace):
    print("Added user")


def handle_user_edit(args: Namespace):
    print("Editing user")


def handle_user_list(args: Namespace):
    print("Listing users")


def handle_user_delete(args: Namespace):
    print("Deleting user")
