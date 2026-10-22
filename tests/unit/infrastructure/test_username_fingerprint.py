import re

from infrastructure.persistence.audit.fingerprint import username_fingerprint


def test_fingerprint_is_short_hex_and_deterministic():
    first, second = username_fingerprint("ghost"), username_fingerprint("ghost")

    assert re.fullmatch(r"[0-9a-f]{8}", first)
    assert first == second


def test_different_inputs_give_different_fingerprints():
    assert username_fingerprint("ghost") != username_fingerprint("ghost2")


def test_fingerprint_is_keyed_by_the_secret_key(settings):
    before = username_fingerprint("ghost")
    settings.SECRET_KEY = "another-secret-key-for-this-test"

    assert username_fingerprint("ghost") != before


def test_fingerprint_does_not_contain_the_input():
    assert "secret" not in username_fingerprint("secret")
