import pytest

from aiodinweb import constants


class TestMethod:
    @pytest.mark.parametrize('left, right, expected', (
        ('GET', constants.Method.GET, True),
        ('Get', constants.Method.GET, False),
        ('GET', constants.Method.POST, False),
        ('POST', constants.Method.GET, False),
        (constants.Method.GET, 'GET', True),
        (constants.Method.DELETE, constants.Method.DELETE, True),
        (constants.Method.DELETE, constants.Method.HEAD, False),
    ))
    def test_eq(self, left, right, expected):
        actual = left == right
        assert expected == actual

    def test_hash(self):
        values = {constants.Method.GET, constants.Method.POST, 'GET', 'DELETE'}

        assert 3 == len(values)
        assert constants.Method.GET in values
        assert constants.Method.HEAD not in values

