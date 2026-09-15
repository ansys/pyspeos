# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for shared pytest configuration."""

import pytest

from tests.conftest import _feature_version


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("271", 271),
        ("2027.1.0.42487-beta", 271),
        ("2027.2.0.53548", 272),
        ("2027.2.1.58749", 272),
    ],
)
def test_feature_version(version: str, expected: int) -> None:
    """Test conversion of Speos image tags to feature-version identifiers."""
    assert _feature_version(version) == expected


def test_feature_version_rejects_invalid_value() -> None:
    """Test that unsupported version identifiers show a useful error."""
    with pytest.raises(pytest.UsageError, match="--supported-features"):
        _feature_version("unsupported")
