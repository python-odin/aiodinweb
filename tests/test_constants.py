import pytest

from aiodinweb import constants


class TestMethod:
    @pytest.mark.parametrize('left, right, expected', (
        ('GET', constants.Method.Get, True),
        ('Get', constants.Method.Get, False),
        ('GET', constants.Method.Post, False),
        ('POST', constants.Method.Get, False),
        (constants.Method.Get, 'GET', True),
        (constants.Method.Delete, constants.Method.Delete, True),
        (constants.Method.Delete, constants.Method.Head, False),
    ))
    def test_eq(self, left, right, expected):
        actual = left == right
        assert expected == actual

    def test_hash(self):
        values = {constants.Method.Get, constants.Method.Post, 'GET', 'DELETE'}

        assert 3 == len(values)
        assert constants.Method.Get in values
        assert constants.Method.Head not in values
