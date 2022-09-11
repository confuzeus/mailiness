import base64
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from mailiness import g

from . import settings

debug = getattr(g, "debug", False)


def get_default_selector():
    return datetime.now().strftime("%Y%m%d")


class DKIM:
    def __init__(self, domain: str, selector: Optional[str] = None):
        if debug:
            _, self.dkim_maps_path = tempfile.mkstemp()
            self.dkim_private_key_dir = tempfile.mkdtemp()
        else:
            self.dkim_maps_path = settings.DKIM_MAPS_PATH
            self.dkim_private_key_dir = settings.DKIM_PRIVATE_KEY_DIRECTORY
        dkim_map = self.load_from_dkim_map_file()
        self.private_key = None
        if domain in dkim_map.keys():
            self.selector = dkim_map[domain]
            with (
                Path(self.dkim_private_key_dir)
                / Path(f"{self.domain}.{self.selector}.key")
            ).open("rb") as fp:
                self.private_key = serialization.load_pem_private_key(
                    fp.read(), password=None
                )
        else:
            self.generate_key()
            if selector is None:
                self.selector = get_default_selector()
            else:
                self.selector = selector

        self.domain = domain

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
            domain, selector = line.split(" ")
            result[domain] = selector
        return result

    def write_dkim_map(self, data: dict):
        shutil.copy2(self.dkim_maps_path, self.dkim_maps_path + ".bak")

        new_map = ""
        for domain, selector in data.items():
            new_map += f"{domain} {selector}\n"

        with Path(self.dkim_maps_path).open("w", encoding="utf-8") as fp:
            fp.write(new_map)

    def dns_txt_record(self) -> str:
        b64_der_pubkey = base64.b64encode(self.public_key_as_der())
        txt_record = ""
        txt_record += f"DNS TXT Record for {self.domain}\n\n\n\n"
        txt_record += f"Name:\n\n{self.selector}._domainkey\n\n\n"
        txt_record += f"Content:\n\nv=DKIM1;k=rsa;p={b64_der_pubkey.decode('utf-8')}"
        return txt_record

    def delete_key(self):
        dkim_map = self.load_from_dkim_map_file()
        del dkim_map[self.domain]
        self.write_dkim_map(dkim_map)

        key_file = Path(self.dkim_private_key_dir) / Path(
            f"{self.domain}.{self.selector}.key"
        )

        key_file.unlink(missing_ok=True)

    def load_from_dkim_map_file(self) -> dict:
        dkim_map_file = Path(self.dkim_maps_path)

        if dkim_map_file.exists():
            with dkim_map_file.open("r", encoding="utf-8") as fp:
                return self.load_dkim_map(fp.read())
        return {}

    def save_private_key(self):
        dest = Path(self.dkim_private_key_dir) / Path(
            f"{self.domain}.{self.selector}.key"
        )

        with dest.open("w", encoding="utf-8") as fp:
            fp.write(self.private_key_as_pem())

        if not debug:
            shutil.chown(str(dest), user="_rspamd", group="_rspamd")

        dkim_map = self.load_from_dkim_map_file()

        dkim_map[self.domain] = self.selector

        self.write_dkim_map(dkim_map)

        if not debug:
            subprocess.run(["systemctl", "reload", "rspamd"])
