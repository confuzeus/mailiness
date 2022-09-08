from argparse import Namespace

from rich.console import Console

from . import dkim, repo

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


def handle_domain_edit_name(args: Namespace):
    print("Domain changed")


def handle_domain_delete(args: Namespace):
    print("Domain deleted")


def handle_domain_list(args: Namespace):
    domain_repo = repo.DomainRepository()
    tbl = domain_repo.index()
    console.print(tbl)
