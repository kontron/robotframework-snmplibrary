from nose.tools import eq_, raises
from SnmpLibrary import SnmpLibrary

a = [
    ((1,2,3,256), '1'),
    ((1,2,3,257), '1'),
    ((1,2,3,258), '1'),
    ((1,2,3,259), '1'),
    ((1,2,3,260), '1'),
    ((1,2,3,261), '1'),
    ((1,2,3,262), '1'),
    ((1,2,3,263), '1'),
    ((1,2,3,264), '1'),
    ((1,2,3,265), '1'),
    ((1,2,3,266), '1'),
    ((1,2,3,267), '1'),
    ((1,2,3,268), '1')
]

b = [
    ((1,2,3,256), '0/1'),
    ((1,2,3,257), '0/2'),
    ((1,2,3,258), '0/3'),
    ((1,2,3,259), '0/4'),
    ((1,2,3,260), '0/5'),
    ((1,2,3,262), '0/7'),
    ((1,2,3,263), '0/8'),
    ((1,2,3,264), '0/9'),
    ((1,2,3,265), '0/10'),
    ((1,2,3,266), '0/10'),
    ((1,2,3,261), '0/6'),
    ((1,2,3,268), '0/34')
]

class TestSnmpLibrary(object):
    def setup(self):
        self.s = SnmpLibrary()

    def test_snmplibrary_find_index(self):
        eq_(self.s.find_index(1, a, '1', b, '0/6'), (261, ))
        eq_(self.s.find_index(2, a, '1', b, '0/6'), (3, 261))

    @raises(RuntimeError)
    def test_snmplibrary_find_index_invalid_arguments(self):
        self.s.find_index(1, a, '1', b)

    @raises(RuntimeError)
    def test_snmplibrary_find_index_no_index_found(self):
        self.s.find_index(1, a, '1', b, '0/55')

    @raises(RuntimeError)
    def test_snmplibrary_find_index_ambiguous_match(self):
        self.s.find_index(1, a, '1', b, '0/10')

