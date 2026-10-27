import pytest

import vektorflow.agents as agents


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch):
    """Never touch a real Supabase project during tests."""

    for name in (
        "HACKATHON_SUPABASE_URL",
        "HACKATHON_SUPABASE_KEY",
        "HACKATHON_SUPABASE_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)
    agents.reset_state()
    yield
    agents.reset_state()
