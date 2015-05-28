from nose.tools import raises
from SnmpLibrary import utils

def test_parse_idx():
    assert utils.parse_idx('1.2.3') == (1, 2, 3)
    assert utils.parse_idx(1) == (1,)
    assert utils.parse_idx([1, 2, 3]) == (1, 2, 3)
    assert utils.parse_idx((1, '2', 3)) == (1, 2, 3)
