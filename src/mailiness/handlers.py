import base64
from argparse import Namespace

from . import dkim


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
        # TODO: Save it
        print("Saved")
