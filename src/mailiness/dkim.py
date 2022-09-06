from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from . import settings


class DKIM:
    def __init__(self, selector: str, domain: str):
        self.private_key = None
        self.selector = selector
        self.domain = domain

    def generate_key(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=settings.RSA_PUBLIC_EXPONENT,
            key_size=settings.DKIM_KEY_SIZE,
        )

    def private_key_as_pem(self) -> str:
        if self.private_key is None:
            self.generate_key()

        as_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return as_bytes.decode("utf-8")
