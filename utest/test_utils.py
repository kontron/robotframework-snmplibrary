from SnmpLibrary.utils import parse_oid, parse_idx
from nose.tools import eq_

def test_parse_idx():
    eq_(parse_idx('1.2.3'), (1, 2, 3))
    eq_(parse_idx(1), (1,))
    eq_(parse_idx([1, 2, 3]), (1, 2, 3))
    eq_(parse_idx((1, '2', 3)), (1, 2, 3))
