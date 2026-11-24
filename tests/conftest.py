"""Shared pytest options."""
from __future__ import annotations


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Rewrite tests/golden/*.json from the current results (do this on purpose, "
        "and explain the change in the PR).",
    )
