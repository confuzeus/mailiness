from rich.console import Console
import base64
from argparse import Namespace

from . import repo
from . import dkim

console = Console()

def handle_dkim_keygen(args: Namespace):
    key = dkim.DKIM(domain=args.domain, selector=args.selector)

    b64_der_pubkey = base64.b64encode(key.public_key_as_der())
    print(key.private_key_as_pem())
    output = ""
    output += f"DNS TXT Record for {args.domain}\n\n\n\n"
    output += f"Name:\n\n{args.selector}._domainkey\n\n\n"
    output += f"Content:\n\nv=DKIM1;k=rsa;p={b64_der_pubkey.decode('utf-8')}"
    if args.print:
        print(output)

    if args.save:
        key.save_private_key()


def handle_domain_add(args: Namespace):
    print("Adding domain")


def handle_domain_edit_name(args: Namespace):
    print("Domain changed")


def handle_domain_delete(args: Namespace):
    print("Domain deleted")


def handle_domain_list(args: Namespace):
    domain_repo = repo.DomainRepository()
    tbl = domain_repo.index()
    console.print(tbl)
