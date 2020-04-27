# -*- coding: utf-8 -*-
"""
:codeauthor: :email:`Herbert Buurman <herbert.buurman@ogd.nl>`
"""
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import errno
import shutil
import tempfile
import textwrap
import os
import sys

# Import Salt Testing libs
import salt.utils.versions
import salt.utils.path
import salt.utils.platform
from tests.support.case import ModuleCase
from tests.support.unit import skipIf
from tests.support.runtests import RUNTIME_VARS

# pylint: disable=incompatible-py3-code

try:
    import gnupg

    GPG_VERSION = ".".join(map(str, gnupg.GPG().version))
    HAS_GPG = True
except ImportError:
    HAS_GPG = False


def _delete_errorhandler(func, path, exc):
    """
    Helper function to ignore "No such file or directory"-errors
    when cleaning up.
    """
    if exc[1].errno != errno.ENOENT:
        raise exc[1]


@skipIf(not salt.utils.platform.is_linux(), "These tests can only be run on linux")
@skipIf(not salt.utils.path.which("gpg"), "GPG not installed. Skipping")
@skipIf(not HAS_GPG, "GPG Module Unavailable")
class GpgTestCase(ModuleCase):
    """
    Test cases for salt.modules.gpg

    Forced order execution implementation from
    https://stackoverflow.com/questions/5387299/python-unittest-testcase-execution-order/5387956#5387956
    """

    @classmethod
    def setUpClass(cls):
        cls.top_pillar = os.path.join(RUNTIME_VARS.TMP_PILLAR_TREE, "top.sls")
        cls.minion_pillar = os.path.join(RUNTIME_VARS.TMP_PILLAR_TREE, "gpg.sls")
        with salt.utils.files.fopen(cls.top_pillar, "w") as wfh:
            wfh.write(
                textwrap.dedent(
                    """\
                base:
                  '*':
                    - gpg
                """
                )
            )
        with salt.utils.files.fopen(cls.minion_pillar, "w") as wfh:
            wfh.write("secret_password: foo")

        cls.gnupghome = tempfile.mkdtemp(prefix="saltgpg")
        cls.secret_key = textwrap.dedent(
            """\
            -----BEGIN PGP PRIVATE KEY BLOCK-----

            lQIGBF1j4XwBBADVcoGjgf3ZGym6GYL6wLztZtMzDvQXUD4OS0qFBVp80d/k4Wdw
            PJAt2xngvHhFgMTe3+8XRI2MgpkSfNzcTntcyGhcCjNQI3d7GlrFpMzu6G3SQkwT
            BqPzELZuGhXJVyj5tSGbDU1hJpcIQ5RRH2HATg7S6xrVatVIDcDrGG6RCwARAQAB
            /gcDAthKJmnqBvV0/lD2KesI3lVcbRfJdmgbWE1pO0tSaWs6e0nOVMYjS4yZOWZp
            alRJ98wv0CSJoU1jG+ZBtjHSVOQEgCKLNJ51iN+gi4khqC9Bqr/aPkFLEs7RijUo
            PSAsHSLU/OcoT0Vpbup/x9w3IYdWurWUB+x0zZKcSx0KEQD2y/DvGQb7ngc7Ir3e
            0qp7F32dNGHNWyJ282Mlv7i7VV9nPP9q42T7v+y0BqPl6AjIa8TurvbM5X++FxoJ
            hxSJKI9OL6+Z6GIojm3w45zpgsHmj6FrRL8ZBO3Qc0CoxU9+gV6cTnOcOp/sX3sj
            BhKkxP6Vtthl4HVeQjQIRh8tIQu79xE8RhqgsaG6on9qVq0uWioU5yNMsmmzZ8ma
            2E91TVwXhCOQcoUTI4dKzBd13DNPDTbmcz4q+Wud9Tf3G5X6nDBI7RcxqaCec+OF
            4s1mYBv9Mg6Gt1whQ7fMMPtcEN9IhcV62Qybv2NU0UvKZrB74+hfD2q0P0F1dG9n
            ZW5lcmF0ZWQgS2V5IChHZW5lcmF0ZWQgYnkgU2FsdFN0YWNrKSA8c2FsdEBzYWx0
            c3RhY2suY29tPojOBBMBCgA4FiEEG1IoG/FZhWynagT1hXyG/Pij+xEFAl1j4XwC
            Gy8FCwkIBwIGFQoJCAsCBBYCAwECHgECF4AACgkQhXyG/Pij+xGVjgP/QlCbLQXw
            wdrYpdy93b5aF6aNiT29R9oEUJNjX4a/f1hhl7wrU3eCFanAfMehrAhorB4Ex9ck
            urt+cR7IEdZgOIXjmJzBM9kgEMd3iCmVECcOHPmUVzM37fsouHNQsAHJU+5kpvnO
            MHLCCQqOaivEoEIH9SoNwy3wrIZPvq7FtT8=
            =WPfN
            -----END PGP PRIVATE KEY BLOCK-----
            """
        )
        # Keyspec for GPG 2.0 and older (v1)
        cls.gpg20_secret_key_spec = {
            "keyid": "857C86FCF8A3FB11",
            "fingerprint": "1B52281BF159856CA76A04F5857C86FCF8A3FB11",
            "uids": ["Autogenerated Key (Generated by SaltStack) <salt@saltstack.com>"],
            "created": "2019-08-26",
            "keyLength": "1024",
        }
        cls.gpg21_secret_key_spec = {
            "keyid": "857C86FCF8A3FB11",
            "fingerprint": "1B52281BF159856CA76A04F5857C86FCF8A3FB11",
            "uids": ["Autogenerated Key (Generated by SaltStack) <salt@saltstack.com>"],
            "created": "2019-08-26",
            "keyLength": "1024",
            "ownerTrust": "Unknown",
            "trust": "Unknown",
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.gnupghome, onerror=_delete_errorhandler)
        del cls.gnupghome
        del cls.gpg20_secret_key_spec
        del cls.gpg21_secret_key_spec
        del cls.secret_key
        salt.utils.files.remove(cls.top_pillar)
        salt.utils.files.remove(cls.minion_pillar)
        del cls.top_pillar
        del cls.minion_pillar

    def _steps(self):
        for name in dir(self):
            if name.startswith("step"):
                yield name, getattr(self, name)

    def test_steps(self):
        self.run_function("saltutil.refresh_pillar", timeout=30)
        verbose = "-v" in sys.argv or "--verbose" in sys.argv
        for name, step in self._steps():
            if verbose:
                print("\n{} ({}) ... ".format(name, str(self)), end="")
            step()
            if verbose:
                print("ok", end="")
            else:
                print(".", end="")
        if verbose:
            print()

    def step_01_create_key(self):
        """
        Test creation of a key.
        Note: This actually causes GPG to generate a key, which might drain the
        random pool.
        """
        step_1_gnupghome = tempfile.mkdtemp(prefix="saltgpg")
        self.addCleanup(shutil.rmtree, step_1_gnupghome, _delete_errorhandler)
        expected_result = {
            "message": "GPG key pair successfully generated.",
            "result": True,
        }
        res = self.run_function(
            "gpg.create_key",
            gnupghome=step_1_gnupghome,
            passphrase="foo",
            name_email="salt@saltstack.com",
        )
        self.assertIn("fingerprint", res)
        del res["fingerprint"]
        self.assertEqual(res, expected_result)

    def step_02_import_key(self):
        """
        Test gpg.import_key
        """
        res = self.run_function(
            "gpg.import_key", text=self.secret_key, gnupghome=self.gnupghome
        )
        self.assertTrue(res["result"])
        self.assertEqual(res["message"], "Successfully imported key(s).")

    def step_02f_import_key(self):
        """
        Test gpg.import_key with incorrect data
        """
        res = self.run_function(
            "gpg.import_key", text="gargleblaster", gnupghome=self.gnupghome
        )
        self.assertFalse(res["result"])
        self.assertEqual(res["message"], "Unable to import key: No valid data found")

    def step_03a_list_keys(self):
        """
        Test gpg.list_keys, list key imported in step_2
        """
        res = self.run_function("gpg.list_keys", gnupghome=self.gnupghome)
        self.assertEqual(res, [self.gpg21_secret_key_spec])

    def step_03b_list_secret_keys(self):
        """
        Test gpg.list_secret_keys, list key imported in step_2
        """
        res = self.run_function("gpg.list_secret_keys", gnupghome=self.gnupghome)
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            self.assertEqual(res, [self.gpg21_secret_key_spec])
        else:
            self.assertEqual(res, [self.gpg20_secret_key_spec])

    def step_04a_get_key(self):
        """
        Test gpg.get_key, get key imported in step_2
        """
        # Test getting by keyid
        res = self.run_function(
            "gpg.get_key", keyid="857C86FCF8A3FB11", gnupghome=self.gnupghome
        )
        self.assertEqual(res, self.gpg21_secret_key_spec)
        # Test getting by fingerprint
        res = self.run_function(
            "gpg.get_key",
            fingerprint="1B52281BF159856CA76A04F5857C86FCF8A3FB11",
            gnupghome=self.gnupghome,
        )
        self.assertEqual(res, self.gpg21_secret_key_spec)

    def step_04b_get_secret_key(self):
        """
        Test gpg.get_secret_key, get key imported in step 2
        """
        # Test getting by keyid
        res = self.run_function(
            "gpg.get_secret_key", keyid="857C86FCF8A3FB11", gnupghome=self.gnupghome
        )
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            self.assertEqual(res, self.gpg21_secret_key_spec)
        else:
            self.assertEqual(res, self.gpg20_secret_key_spec)
        # Test getting by fingerprint
        res = self.run_function(
            "gpg.get_secret_key",
            fingerprint="1B52281BF159856CA76A04F5857C86FCF8A3FB11",
            gnupghome=self.gnupghome,
        )
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            self.assertEqual(res, self.gpg21_secret_key_spec)
        else:
            self.assertEqual(res, self.gpg20_secret_key_spec)

    def step_05a_export_key(self):
        """
        Test gpg.export_key to export public key.
        """
        res = self.run_function(
            "gpg.export_key", keyids="857C86FCF8A3FB11", gnupghome=self.gnupghome
        )
        self.assertTrue(
            res["message"].startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")
        )
        self.assertTrue(res["message"].endswith("-----END PGP PUBLIC KEY BLOCK-----\n"))

    def step_05b_export_secret_key(self):
        """
        Test gpg.export_key to export private key.
        """
        res = self.run_function(
            "gpg.export_key",
            keyids="857C86FCF8A3FB11",
            gnupghome=self.gnupghome,
            secret=True,
            passphrase="foo",
        )
        self.assertTrue(
            res["message"].startswith("-----BEGIN PGP PRIVATE KEY BLOCK-----")
        )
        self.assertTrue(
            res["message"].endswith("-----END PGP PRIVATE KEY BLOCK-----\n")
        )

    def step_05f_export_secret_key(self):
        """
        Test gpg.export_key to export private key, failing to provide passphrase in GPG >=2.1
        """
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            res = self.run_function(
                "gpg.export_key",
                keyids="857C86FCF8A3FB11",
                gnupghome=self.gnupghome,
                secret=True,
            )
            self.assertTrue(res.startswith("The minion function caused an exception:"))
            self.assertTrue(
                res.endswith(
                    "ValueError: For GnuPG >= 2.1, exporting secret keys needs a passphrase to be provided\n"
                )
            )

    def step_06a_trust_key_by_fingerprint(self):
        """
        Test gpg.trust_key by fingerprint
        """
        res = self.run_function(
            "gpg.trust_key",
            fingerprint="1B52281BF159856CA76A04F5857C86FCF8A3FB11",
            gnupghome=self.gnupghome,
            trust_level="marginally",
        )
        self.assertTrue(res["result"])
        self.assertEqual(res["message"], "Setting ownership trust to Marginally")

    def step_06b_trust_key_by_keyid(self):
        """
        Test gpg.trust_key by keyid
        """
        res = self.run_function(
            "gpg.trust_key",
            keyid="857C86FCF8A3FB11",
            gnupghome=self.gnupghome,
            trust_level="ultimately",
        )
        self.assertTrue(res["result"])
        self.assertEqual(
            res["message"], "Setting ownership trust to Ultimately Trusted"
        )

    def step_06f_trust_key(self):
        """
        Test failing gpg.trust_key
        """
        if salt.utils.versions.version_cmp(gnupg.__version__, "0.4.2") >= 0:
            res = self.run_function(
                "gpg.trust_key",
                keyid="foobar",
                gnupghome=self.gnupghome,
                trust_level="unknown",
            )
            self.assertFalse(res["result"])
            self.assertEqual(
                res["message"], "KeyID or fingerprint foobar not in GPG keychain"
            )
        res = self.run_function(
            "gpg.trust_key",
            fingerprint="1234567890123456789012345678901234567890",
            gnupghome=self.gnupghome,
            trust_level="ultimately",
        )
        self.assertFalse(res["result"])
        self.assertEqual(
            res["message"],
            "KeyID or fingerprint 1234567890123456789012345678901234567890 not in GPG keychain",
        )

    def step_07f_sign_message(self):
        """
        Test signing a test message but failing because no passphrase is supplied.
        """
        res = self.run_function(
            "gpg.sign",
            keyid="857C86FCF8A3FB11",
            text="sign here",
            gnupghome=self.gnupghome,
        )
        self.assertFalse(res["result"])
        self.assertEqual(
            res["message"], "Failed to sign data. Check minion log for details."
        )

    def step_07g_sign_message(self):
        """
        Test signing a test message. Note that this test caches the passphrase and as such needs to run after 7f.
        """
        res = self.run_function(
            "gpg.sign",
            keyid="857C86FCF8A3FB11",
            text="sign here",
            gnupghome=self.gnupghome,
            passphrase="foo",
        )
        self.assertTrue(res["result"])
        self.assertTrue(
            res["message"].startswith("-----BEGIN PGP SIGNED MESSAGE-----\n")
        )
        self.assertTrue(
            "Hash: " in res["message"]
            and "\n\nsign here\n-----BEGIN PGP SIGNATURE-----\n" in res["message"]
        )
        self.assertTrue(res["message"].endswith("\n-----END PGP SIGNATURE-----\n"))

    def step_07h_sign_file(self):
        """
        Test signing a file.
        """
        plaintext_file = os.path.join(RUNTIME_VARS.TMP, "07h_file_to_sign.txt")
        self.addCleanup(salt.utils.files.remove, plaintext_file)
        with salt.utils.files.fopen(plaintext_file, "wb") as fp:
            fp.write(salt.utils.stringutils.to_bytes("Statement of authority."))
        res = self.run_function(
            "gpg.sign",
            keyid="857C86FCF8A3FB11",
            filename=plaintext_file,
            gnupghome=self.gnupghome,
            passphrase="foo",
        )
        self.assertTrue(res["result"])
        self.assertTrue(
            res["message"].startswith("-----BEGIN PGP SIGNED MESSAGE-----\n")
        )
        self.assertTrue(
            "Hash: " in res["message"]
            and "\n\nStatement of authority.\n-----BEGIN PGP SIGNATURE-----\n"
            in res["message"]
        )
        self.assertTrue(res["message"].endswith("\n-----END PGP SIGNATURE-----\n"))

    def step_07i_sign_message(self):
        """
        Test signing a test message, using passphrase_pillar.
        Unfortunately, the correct password has been cached in step 7g, so even
        providing an incorrect password in the pillar (line 50) will correctly
        sign the message.
        """
        res = self.run_function(
            "gpg.sign",
            keyid="857C86FCF8A3FB11",
            text="sign here",
            gnupghome=self.gnupghome,
            passphrase_pillar="secret_password",
        )
        self.assertTrue(res["result"])
        self.assertTrue(
            res["message"].startswith("-----BEGIN PGP SIGNED MESSAGE-----\n")
        )
        self.assertTrue(
            "Hash: " in res["message"]
            and "\n\nsign here\n-----BEGIN PGP SIGNATURE-----\n" in res["message"]
        )
        self.assertTrue(res["message"].endswith("\n-----END PGP SIGNATURE-----\n"))

    def step_07j_sign_verify_detached_signature(self):
        """
        Test signing and verifying a test message, outputting the signature to a separate file.
        """
        # Setup
        signature_file = os.path.join(RUNTIME_VARS.TMP, "07j_signature.asc")
        self.addCleanup(salt.utils.files.remove, signature_file)
        plaintext_file = os.path.join(RUNTIME_VARS.TMP, "07j_file_to_sign.txt")
        self.addCleanup(salt.utils.files.remove, plaintext_file)
        with salt.utils.files.fopen(plaintext_file, "wb") as fp:
            fp.write(salt.utils.stringutils.to_bytes("Statement of authority."))

        # Sign file
        res = self.run_function(
            "gpg.sign",
            keyid="857C86FCF8A3FB11",
            filename=plaintext_file,
            gnupghome=self.gnupghome,
            passphrase="foo",
            detach=True,
            output=signature_file,
        )
        with salt.utils.files.fopen(signature_file, "rb") as fp:
            signature = salt.utils.stringutils.to_unicode(fp.read())
        self.assertTrue(signature.startswith("-----BEGIN PGP SIGNATURE-----\n"))
        self.assertTrue(signature.endswith("\n-----END PGP SIGNATURE-----\n"))

        # Verification
        res = self.run_function(
            "gpg.verify",
            filename=plaintext_file,
            gnupghome=self.gnupghome,
            signature=signature_file,
        )
        self.assertEqual(
            res,
            {
                "result": True,
                "message": "The signature is verified.",
                "username": "Autogenerated Key (Generated by SaltStack) <salt@saltstack.com>",
                "key_id": "857C86FCF8A3FB11",
                "trust_level": "Ultimate",
            },
        )

    def step_08_verify_message(self):
        """
        Test verification of a signed message.
        """
        signed_message = self.run_function(
            "gpg.sign",
            keyid="857C86FCF8A3FB11",
            text="sign here",
            gnupghome=self.gnupghome,
            passphrase="foo",
        )["message"]
        res = self.run_function(
            "gpg.verify", text=signed_message, gnupghome=self.gnupghome
        )
        self.assertEqual(
            res,
            {
                "result": True,
                "username": "Autogenerated Key (Generated by SaltStack) <salt@saltstack.com>",
                "key_id": "857C86FCF8A3FB11",
                "trust_level": "Ultimate",  # This is actually caused by test 6b
                "message": "The signature is verified.",
            },
        )

    def step_09_encrypt_decrypt_message(self):
        """
        Test encrypting and decrypting a message.
        """
        encrypt = self.run_function(
            "gpg.encrypt",
            text="secret",
            recipients="salt@saltstack.com",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(encrypt["result"])
        self.assertTrue(encrypt["message"].startswith("-----BEGIN PGP MESSAGE-----\n"))
        self.assertTrue(encrypt["message"].endswith("\n-----END PGP MESSAGE-----\n"))

        # Encrypt with bare output
        encrypted_message = self.run_function(
            "gpg.encrypt",
            text="secret",
            recipients="salt@saltstack.com",
            gnupghome=self.gnupghome,
            bare=True,
        )
        self.assertTrue(encrypted_message.startswith("-----BEGIN PGP MESSAGE-----\n"))
        self.assertTrue(encrypted_message.endswith("\n-----END PGP MESSAGE-----\n"))

        decrypt = self.run_function(
            "gpg.decrypt",
            text=encrypted_message,
            passphrase="foo",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(decrypt["result"])
        self.assertEqual(decrypt["message"], "secret")

    def step_09b_encrypt_decrypt_message_symmetric(self):
        """
        Test encrypting and decrypting a message with symmetric password.
        """
        encrypt = self.run_function(
            "gpg.encrypt",
            text="secret",
            symmetric=True,
            passphrase="kensentme",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(encrypt["result"])
        self.assertTrue(encrypt["message"].startswith("-----BEGIN PGP MESSAGE-----\n"))
        self.assertTrue(encrypt["message"].endswith("\n-----END PGP MESSAGE-----\n"))

        decrypt = self.run_function(
            "gpg.decrypt",
            text=encrypt["message"],
            passphrase="kensentme",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(decrypt["result"])
        self.assertEqual(decrypt["message"], "secret")

        # Try decrypting with invalid password
        decrypt = self.run_function(
            "gpg.decrypt",
            text=encrypt["message"],
            passphrase="nothatsnotit",
            gnupghome=self.gnupghome,
        )
        self.assertFalse(decrypt["result"])
        self.assertEqual(
            decrypt["message"],
            "decryption failed.\nPlease check the salt-minion log for further details.",
        )

    def step_09c_encrypt_decrypt_file(self):
        """
        Test encrypting and decrypting a file.
        """
        plaintext_file = os.path.join(RUNTIME_VARS.TMP, "09c_secret_data.txt")
        self.addCleanup(salt.utils.files.remove, plaintext_file)
        encrypted_file = os.path.join(RUNTIME_VARS.TMP, "09c_secret_data.asc")
        self.addCleanup(salt.utils.files.remove, encrypted_file)
        decrypted_file = os.path.join(RUNTIME_VARS.TMP, "09c_decrypted_data.txt")
        self.addCleanup(salt.utils.files.remove, decrypted_file)
        with salt.utils.files.fopen(plaintext_file, "wb") as fp:
            fp.write(salt.utils.stringutils.to_bytes("Very big secret! Hush"))
        # Encrypt to returned string
        encrypt = self.run_function(
            "gpg.encrypt",
            filename=plaintext_file,
            recipients="salt@saltstack.com",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(encrypt["result"])
        self.assertTrue(encrypt["message"].startswith("-----BEGIN PGP MESSAGE-----\n"))
        self.assertTrue(encrypt["message"].endswith("\n-----END PGP MESSAGE-----\n"))
        # Encrypt to new file
        encrypt = self.run_function(
            "gpg.encrypt",
            filename=plaintext_file,
            output=encrypted_file,
            recipients="salt@saltstack.com",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(encrypt["result"])
        self.assertEqual(
            encrypt["message"],
            "Encrypted data has been written to {}".format(encrypted_file),
        )

        # Decrypt from file, to returned string
        decrypt = self.run_function(
            "gpg.decrypt",
            filename=encrypted_file,
            passphrase="foo",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(decrypt["result"])
        self.assertEqual(decrypt["message"], "Very big secret! Hush")

        # Decrypt from file, to file
        decrypt = self.run_function(
            "gpg.decrypt",
            filename=encrypted_file,
            output=decrypted_file,
            passphrase="foo",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(decrypt["result"])
        with salt.utils.files.fopen(decrypted_file, "rb") as fp:
            decrypted_data = salt.utils.stringutils.to_unicode(fp.read())
        self.assertEqual(decrypted_data, "Very big secret! Hush")

    def step_09c_encrypt_and_sign_decrypt_and_verify(self):
        """
        Test encrypting and signing input data and decrypting and verifying the signature.
        """
        encrypt = self.run_function(
            "gpg.encrypt",
            text="secret",
            passphrase="foo",
            sign=True,
            recipients="salt@saltstack.com",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(encrypt["result"])
        self.assertTrue(encrypt["message"].startswith("-----BEGIN PGP MESSAGE-----\n"))
        self.assertTrue(encrypt["message"].endswith("\n-----END PGP MESSAGE-----\n"))

        decrypt = self.run_function(
            "gpg.decrypt",
            text=encrypt["message"],
            passphrase="foo",
            gnupghome=self.gnupghome,
        )
        self.assertIn("signature_id", decrypt)
        del decrypt["signature_id"]
        self.assertEqual(
            decrypt,
            {
                "result": True,
                "message": "secret",
                "username": "Autogenerated Key (Generated by SaltStack) <salt@saltstack.com>",
                "key_id": "857C86FCF8A3FB11",
                "fingerprint": "1B52281BF159856CA76A04F5857C86FCF8A3FB11",
                "trust_level": 4,
                "trust_text": "TRUST_ULTIMATE",
            },
        )

    def step_09d_encrypt_and_sign_decrypt_and_verify_file(self):
        """
        Test encrypting and signing, then decrypting and verifying a file.
        """
        plaintext_file = os.path.join(RUNTIME_VARS.TMP, "09d_secret_data.txt")
        self.addCleanup(salt.utils.files.remove, plaintext_file)
        encrypted_file = os.path.join(RUNTIME_VARS.TMP, "09d_encrypted_data.txt")
        self.addCleanup(salt.utils.files.remove, encrypted_file)
        decrypted_file = os.path.join(RUNTIME_VARS.TMP, "09d_decrypted_data.txt")
        self.addCleanup(salt.utils.files.remove, decrypted_file)
        with salt.utils.files.fopen(plaintext_file, "wb") as fp:
            fp.write(salt.utils.stringutils.to_bytes("Also very big secret! Hush"))
        encrypt = self.run_function(
            "gpg.encrypt",
            filename=plaintext_file,
            output=encrypted_file,
            passphrase="foo",
            sign=True,
            recipients="salt@saltstack.com",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(encrypt["result"])
        self.assertEqual(
            encrypt["message"],
            "Encrypted data has been written to {}".format(encrypted_file),
        )

        decrypt = self.run_function(
            "gpg.decrypt",
            filename=encrypted_file,
            output=decrypted_file,
            passphrase="foo",
            gnupghome=self.gnupghome,
        )
        self.assertIn("signature_id", decrypt)
        del decrypt["signature_id"]
        self.assertEqual(
            decrypt,
            {
                "result": True,
                "message": "Decrypted data has been written to {}".format(
                    decrypted_file
                ),
                "username": "Autogenerated Key (Generated by SaltStack) <salt@saltstack.com>",
                "key_id": "857C86FCF8A3FB11",
                "fingerprint": "1B52281BF159856CA76A04F5857C86FCF8A3FB11",
                "trust_level": 4,
                "trust_text": "TRUST_ULTIMATE",
            },
        )
        with salt.utils.files.fopen(decrypted_file, "rb") as fp:
            decrypted_data = salt.utils.stringutils.to_unicode(fp.read())
        self.assertEqual(decrypted_data, "Also very big secret! Hush")

    @skipIf(True, "This test polls an online server")
    # This test polls an online server (pool) and running this
    # in all testsuites could be considered a DDOS.
    def test_search_keys(self):
        """
        Test searching for a key
        """
        res = self.run_function(
            "gpg.search_keys",
            text="754A1A7AE731F165D5E6D4BD0E08A149DE57BFBE",
            gnupghome=self.gnupghome,
        )
        # Keyserver pool sometimes returns either the short or the long key
        # and sometimes, nothing at all
        if res:
            self.assertTrue(res[0]["keyid"].endswith("0E08A149DE57BFBE"))
            del res[0]["keyid"]
            self.assertEqual(
                res,
                [
                    {
                        "uids": ["SaltStack Packaging Team <packaging@saltstack.com>"],
                        "created": "2014-06-24",
                        "keyLength": "2048",
                    }
                ],
            )

    @skipIf(True, "This test polls an online server")  # Idem as for test_search_keys
    def test_receive_keys(self):
        """
        Test receiving a key from a keyserver.
        """
        res = self.run_function(
            "gpg.receive_keys",
            keys="754A1A7AE731F165D5E6D4BD0E08A149DE57BFBE",
            gnupghome=self.gnupghome,
        )
        self.assertTrue(res["result"])
        self.assertEqual(
            res["message"],
            "Key 754A1A7AE731F165D5E6D4BD0E08A149DE57BFBE added to keychain",
        )

    def test_fail_receive_keys(self):
        """
        Test receive keys failures.
        """
        res = self.run_function(
            "gpg.receive_keys",
            keyserver="non.existing.domain.local",
            keys=["0123456789ABCDEF"],
            gnupghome=self.gnupghome,
        )
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            gpg_response = "Unable to receive key: Other failure"
        else:
            gpg_response = "Unable to receive key: No valid data found"
        self.assertEqual(res, {"result": False, "message": gpg_response})

    def step_10_delete_key(self):
        """
        Test deleting a key.
        """
        # Verify the key exists in the keychain first
        res = self.run_function(
            "gpg.get_key", keyid="857C86FCF8A3FB11", gnupghome=self.gnupghome,
        )
        self.assertEqual(res["fingerprint"], "1B52281BF159856CA76A04F5857C86FCF8A3FB11")

        # Test that deleting a private key before deleting a public key fails.
        res = self.run_function(
            "gpg.delete_key", keyid="857C86FCF8A3FB11", gnupghome=self.gnupghome,
        )
        self.assertFalse(res["result"])
        self.assertEqual(
            res["message"],
            "Secret key exists, delete first or pass delete_secret=True.",
        )

        # Test deleting secret key requires passphrase
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            res = self.run_function(
                "gpg.delete_key",
                keyid="857C86FCF8A3FB11",
                delete_secret=True,
                gnupghome=self.gnupghome,
            )
            self.assertTrue(
                res.endswith(
                    "ValueError: For GnuPG >= 2.1, deleting "
                    "secret keys needs a passphrase to be provided\n"
                )
            )

        # Deleting private/secret keys was broken in 0.4.4, do not run this test there.
        if salt.utils.versions.version_cmp(gnupg.__version__, "0.4.5") >= 0:
            res = self.run_function(
                "gpg.delete_key",
                keyid="857C86FCF8A3FB11",
                delete_secret=True,
                passphrase="foo",
                gnupghome=self.gnupghome,
            )
            self.assertTrue(res["result"])
            self.assertEqual(
                res["message"],
                (
                    "Secret key 1B52281BF159856CA76A04F5857C86FCF8A3FB11 deleted.\n"
                    "Public key 1B52281BF159856CA76A04F5857C86FCF8A3FB11 deleted"
                ),
            )

    def test_get_fingerprint_from_data(self):
        res = self.run_function(
            "gpg.get_fingerprint_from_data", keydata=self.secret_key,
        )
        if salt.utils.versions.version_cmp(GPG_VERSION, "2.1") >= 0:
            self.assertEqual(res, "1B52281BF159856CA76A04F5857C86FCF8A3FB11")
        else:
            self.assertEqual(res, "'gpg.get_fingerprint_from_data' is not available.")
