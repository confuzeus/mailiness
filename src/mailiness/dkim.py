from cryptography.hazmat.primitives.asymmetric import rsa
from . import settings


class DKIM:
    def __init__(self, selector: str, domain: str):
        self.private_key = None
        self.public_key = None
        self.selector = selector
        self.domain = domain

    def generate_key(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=settings.RSA_PUBLIC_EXPONENT,
            key_size=settings.DKIM_KEY_SIZE,
        )
