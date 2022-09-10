import base64
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from mailiness.dkim import DKIM


class DKIMTest(TestCase):
    def setUp(self):
        self.selector = "20220906"
        self.domain = "example.com"
        self.dkim = DKIM(self.domain, self.selector)

    def test_new_dkim_instance_has_correct_attributes_set(self):
        self.assertEqual(self.dkim.selector, self.selector)
        self.assertEqual(self.dkim.domain, self.domain)

    def test_can_generate_private_key(self):
        self.assertIsInstance(self.dkim.private_key, RSAPrivateKey)

    def test_can_serialize_private_key_as_pem(self):
        pem = self.dkim.private_key_as_pem()
        self.assertIsInstance(pem, str)
        self.assertIn("BEGIN PRIVATE KEY", pem)

    def test_private_key_is_serialized_correctly(self):
        pem = self.dkim.private_key_as_pem()
        loaded = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
        self.assertIsInstance(loaded, RSAPrivateKey)

        loaded_private_numbers = loaded.private_numbers()
        loaded_p = loaded_private_numbers.p
        loaded_q = loaded_private_numbers.q

        instance_private_numbers = self.dkim.private_key.private_numbers()
        instance_p = instance_private_numbers.p
        instance_q = instance_private_numbers.q

        self.assertEqual(loaded_p, instance_p)
        self.assertEqual(loaded_q, instance_q)

    def test_can_serialize_public_key_as_der(self):
        self.assertIsInstance(self.dkim.public_key_as_der(), bytes)

    def test_private_key_is_saved(self):
        with patch("mailiness.dkim.debug") as mock_debug:
            mock_debug = True  # noqa: F841
            _, self.dkim.dkim_maps_path = tempfile.mkstemp()
            self.dkim.dkim_private_key_dir = tempfile.mkdtemp()
            key_path = Path(self.dkim.dkim_private_key_dir) / Path(
                f"{self.dkim.domain}.{self.dkim.selector}.key"
            )
            self.dkim.save_private_key()
            self.assertTrue(key_path.exists())

            expected_content = self.dkim.private_key_as_pem()
            with key_path.open("r", encoding="utf-8") as fp:
                data = fp.read()
                self.assertIn(expected_content, data)

            expected_pair = f"{self.dkim.domain} {self.dkim.selector}"
            with Path(self.dkim.dkim_maps_path).open("r", encoding="utf-8") as fp:
                data = fp.read()
                self.assertIn(expected_pair, data)

    def test_dns_txt_record_contains_correct_data(self):
        txt_record = self.dkim.dns_txt_record()
        self.assertIsInstance(txt_record, str)
        self.assertIn(f"{self.selector}._domainkey", txt_record)
        b64_der_pubkey = base64.b64encode(self.dkim.public_key_as_der())
        self.assertIn(b64_der_pubkey.decode("utf-8"), txt_record)

    def test_delete_dkim_removes_from_map_and_deletes_keyfile(self):
        with patch("mailiness.dkim.debug") as mock_debug:
            mock_debug = True  # noqa: F841
            _, self.dkim.dkim_maps_path = tempfile.mkstemp()
            self.dkim.dkim_private_key_dir = tempfile.mkdtemp()
            self.dkim.save_private_key()

            dkim_map = self.dkim.load_from_dkim_map_file()
            self.assertIn(self.domain, dkim_map.keys())

            key_file = Path(self.dkim.dkim_private_key_dir) / Path(f"{self.dkim.domain}.{self.dkim.selector}.key")

            self.assertTrue(key_file.exists())

            self.dkim.delete_key()
            dkim_map = self.dkim.load_from_dkim_map_file()
            self.assertNotIn(self.domain, dkim_map.keys())
            self.assertFalse(key_file.exists())
