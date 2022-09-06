from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from unittest import TestCase

from mailiness.dkim import DKIM

class DKIMTest(TestCase):

    def setUp(self):
        self.selector = "20220906"
        self.domain = "example.com"

    def test_new_dkim_instance_has_correct_attributes_set(self):
        dkim = DKIM(self.selector, self.domain)
        self.assertIsNone(dkim.private_key)
        self.assertIsNone(dkim.public_key)
        self.assertEqual(dkim.selector, self.selector)
        self.assertEqual(dkim.domain, self.domain)

    def test_can_generate_private_key(self):
        dkim = DKIM(self.selector, self.domain)
        dkim.generate_key()
        self.assertIsInstance(dkim.private_key, RSAPrivateKey)
