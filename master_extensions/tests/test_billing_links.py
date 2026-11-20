"""The WHMCS link is navigation, NOT an authentication delegation."""
import unittest

from master_extensions.billing_links import trusted_billing_admin_url


class BillingLinkTests(unittest.TestCase):
    def test_unconfigured_fails_closed(self):
        self.assertIsNone(trusted_billing_admin_url(""))

    def test_owned_domain_https(self):
        self.assertEqual(
            trusted_billing_admin_url("https://billing.hooshedigital.ir/private-admin/"),
            "https://billing.hooshedigital.ir/private-admin/",
        )

    def test_external_lookalike_and_unsafe_links_denied(self):
        for value in [
            "http://billing.hooshedigital.ir/admin/",
            "https://billing.hooshedigital.ir.attacker.example/admin/",
            "https://attacker.example@billing.hooshedigital.ir/admin/",
            "https://billing.hooshedigital.ir:8090/admin/",
            "https://billing.hooshedigital.ir/admin/?access_token=secret",
            "https://billing.hooshedigital.ir/admin/#secret",
            "javascript:alert(1)",
            "https://billing.hooshedigital.ir//evil",
            "https://billing.hooshedigital.ir\\@attacker.example/",
            " https://billing.hooshedigital.ir/",
        ]:
            with self.subTest(url=value):
                self.assertIsNone(trusted_billing_admin_url(value))


if __name__ == "__main__":
    unittest.main()
