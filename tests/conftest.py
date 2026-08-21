from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def pdf_fixtures() -> Path:
    return Path("examples").resolve()
