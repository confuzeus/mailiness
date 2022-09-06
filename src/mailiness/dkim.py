import re
import tempfile
import subprocess
import shutil
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from threading import local
from . import settings
from mailiness import g

debug = getattr(g, "debug", False)


class DKIM:
    def __init__(self, selector: str, domain: str):
        self.private_key = None
        self.selector = selector
        self.domain = domain
        self.generate_key()
        if debug:
            _, self.dkim_maps_path = tempfile.mkstemp()
            self.dkim_private_key_dir = tempfile.mkdtemp()
        else:
            self.dkim_maps_path = settings.DKIM_MAPS_PATH
            self.dkim_private_key_dir = settings.DKIM_PRIVATE_KEY_DIRECTORY



    def generate_key(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=settings.RSA_PUBLIC_EXPONENT,
            key_size=settings.DKIM_KEY_SIZE,
        )

    def private_key_as_pem(self) -> str:
        as_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return as_bytes.decode("utf-8")

    def public_key_as_der(self) -> bytes:
        return self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def load_dkim_map(self, data: str) -> dict:
        result = {}
        for line in data.splitlines():
            domain, selector = line.split(' ')
            result[domain] = selector
        return result

    def write_dkim_map(self, data: dict):
        shutil.copy2(self.dkim_maps_path, self.dkim_maps_path + ".bak")

        new_map = ""
        for domain, selector in data.items():
            new_map += f"{domain} {selector}\n"

        with Path(self.dkim_maps_path).open("w", encoding="utf-8") as fp:
            fp.write(new_map)

    def save_private_key(self):
        dest = Path(self.dkim_private_key_dir) / Path(f"{self.domain}.{self.selector}.key")

        with dest.open("w", encoding="utf-8") as fp:
            fp.write(self.private_key_as_pem())

        if not debug:
            shutil.chown(str(dest), user="_rspamd", group="_rspamd")

        dkim_map_file = Path(self.dkim_maps_path)

        with dkim_map_file.open('r', encoding="utf-8") as fp:
            dkim_map = self.load_dkim_map(fp.read())

        dkim_map[self.domain] = self.selector

        self.write_dkim_map(dkim_map)

        if not debug:
            subprocess.run(["systemctl", "reload", "rspamd"])
