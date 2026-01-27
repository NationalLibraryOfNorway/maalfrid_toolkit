import pytest
from maalfrid_toolkit.db import db_connect

@pytest.mark.xfail(reason="Integration test")
def test_db_connect():
    conn = db_connect(connect_timeout=10)
    assert conn is not None
    conn.close()
