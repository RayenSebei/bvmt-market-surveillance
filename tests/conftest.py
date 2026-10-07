import socket

import pytest


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def denied(*_args, **_kwargs):
        raise AssertionError("network access is disabled in tests")

    monkeypatch.setattr(socket, "create_connection", denied)
