from SnmpLibrary.utils import parse_oid, parse_idx, format_oid
from nose.tools import eq_

def test_parse_oid():
    eq_(parse_oid('.1.2.3'), (1, 2, 3))
    eq_(parse_oid('sysDescr.0'), (('','sysDescr'),0))
    eq_(parse_oid('SNMPv2-MIB::sysDescr.0'), (('SNMPv2-MIB','sysDescr'),0))
    eq_(parse_oid('.iso.org.6'), ('iso', 'org', 6))

def test_format_oid():
    eq_(format_oid((1,2,3)), '.1.2.3')
    eq_(format_oid((1,'iso','org',3)), '.1.iso.org.3')

def test_parse_idx():
    eq_(parse_idx('1.2.3'), (1, 2, 3))
    eq_(parse_idx(1), (1,))
    eq_(parse_idx([1, 2, 3]), (1, 2, 3))
    eq_(parse_idx((1, '2', 3)), (1, 2, 3))
