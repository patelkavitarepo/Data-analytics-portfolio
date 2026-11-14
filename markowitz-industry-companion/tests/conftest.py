from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import socket
import pytest

@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def blocked(*args,**kwargs):raise AssertionError('Synthetic-only tests must not contact any network endpoint')
    monkeypatch.setattr(socket,'create_connection',blocked)
    monkeypatch.setattr(socket.socket,'connect',blocked)
