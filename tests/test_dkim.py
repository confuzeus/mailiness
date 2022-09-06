from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from unittest import TestCase

from mailiness.dkim import DKIM

class DKIMTest(TestCase):

    def setUp(self):
        self.selector = "20220906"
        self.domain = "example.com"
        self.dkim = DKIM(self.selector, self.domain)

    def test_new_dkim_instance_has_correct_attributes_set(self):
        self.assertIsNone(self.dkim.private_key)
        self.assertIsNone(self.dkim.public_key)
        self.assertEqual(self.dkim.selector, self.selector)
        self.assertEqual(self.dkim.domain, self.domain)

    def test_can_generate_private_key(self):
        self.dkim.generate_key()
        self.assertIsInstance(self.dkim.private_key, RSAPrivateKey)

    def test_can_serialize_private_key_as_pem(self):
        self.dkim.generate_key()
        pem = self.dkim.private_key_as_pem()
        self.assertIsInstance(pem, str)
        self.assertIn("BEGIN PRIVATE KEY", pem)
