from nose.tools import raises
from SnmpLibrary import utils

def test_parse_idx():
    idx = "10.20.30"
    t = utils.parse_idx(idx)
    assert isinstance(t, tuple)
    assert t == (10, 20, 30)

    idx = 10
    t = utils.parse_idx(idx)
    assert isinstance(t, tuple)
    assert t == (10,)

    idx = [10, 20, 30]
    t = utils.parse_idx(idx)
    assert isinstance(t, tuple)
    assert t == (10, 20, 30)

    idx = (10, 20, 30)
    t = utils.parse_idx(idx)
    assert isinstance(t, tuple)
    assert t == (10, 20, 30)
