"""Tests for iil-learnfw settings."""

import pytest

from iil_learnfw.settings import get_setting


def test_should_return_default_setting():
    value = get_setting("ENROLLMENT_MODE")
    assert value == "self_enroll"


def test_should_return_overridden_setting(settings):
    settings.IIL_LEARNFW = {"ENROLLMENT_MODE": "admin_only"}
    value = get_setting("ENROLLMENT_MODE")
    assert value == "admin_only"


def test_should_raise_for_unknown_setting():
    with pytest.raises(KeyError, match="Unknown"):
        get_setting("NONEXISTENT_KEY")
