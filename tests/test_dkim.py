from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from unittest import TestCase

from mailiness.dkim import DKIM


class DKIMTest(TestCase):
    def setUp(self):
        self.selector = "20220906"
        self.domain = "example.com"
        self.dkim = DKIM(self.selector, self.domain)

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
