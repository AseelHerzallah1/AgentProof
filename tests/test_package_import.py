"""Smoke test that the installable package imports."""


def test_import_agentproof() -> None:
    import agentproof

    assert agentproof.__version__ == "0.0.0"
