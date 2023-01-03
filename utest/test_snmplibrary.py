import pytest

from src.SnmpLibrary import SnmpLibrary

a = [
    ('.1.2.3.256', '1'),
    ('.1.2.3.257', '1'),
    ('.1.2.3.258', '1'),
    ('.1.2.3.259', '1'),
    ('.1.2.3.260', '1'),
    ('.1.2.3.261', '1'),
    ((1, 2, 3, 262), '1'),
    ((1, 2, 3, 263), '1'),
    ((1, 2, 3, 264), '1'),
    ((1, 2, 3, 265), '1'),
    ((1, 2, 3, 266), '1'),
    ((1, 2, 3, 267), '1'),
    ((1, 2, 3, 268), '1')
]

b = [
    ((1, 2, 3, 256), '0/1'),
    ((1, 2, 3, 257), '0/2'),
    ((1, 2, 3, 258), '0/3'),
    ((1, 2, 3, 259), '0/4'),
    ((1, 2, 3, 260), '0/5'),
    ((1, 2, 3, 262), '0/7'),
    ('.1.2.3.263', '0/8'),
    ('.1.2.3.264', '0/9'),
    ('.1.2.3.265', '0/10'),
    ('.1.2.3.266', '0/10'),
    ('.1.2.3.261', '0/6'),
    ('.1.2.3.268', '0/34')
]


class TestSnmpLibrary(object):
    def setup_method(self):
        self.s = SnmpLibrary()

    def test_snmplibrary_find_index(self):
        assert self.s.find_index(1, a, '1', b, '0/6') == (261, )
        assert self.s.find_index(2, a, '1', b, '0/6') == (3, 261)

    def test_snmplibrary_find_index_invalid_arguments(self):
        with pytest.raises(RuntimeError):
            self.s.find_index(1, a, '1', b)

    def test_snmplibrary_find_index_no_index_found(self):
        with pytest.raises(RuntimeError):
            self.s.find_index(1, a, '1', b, '0/55')

    def test_snmplibrary_find_index_ambiguous_match(self):
        with pytest.raises(RuntimeError):
            self.s.find_index(1, a, '1', b, '0/10')
