from domain.common.language import DEFAULT_LANGUAGE, Language


def test_languages_are_romanian_default_and_english():
    assert [lang.value for lang in Language] == ["ro", "en"]
    assert DEFAULT_LANGUAGE is Language.RO


def test_language_compares_equal_to_its_code():
    assert Language("en") == "en"
