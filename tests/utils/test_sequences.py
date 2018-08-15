import pytest

from aiodinweb.utils import sequences


@pytest.mark.parametrize('obj, expected', (
    (None, (None,)),
    ("abc", ("abc",)),
    (b'123', (b'123',)),
    (123, (123,)),
    (False, (False,)),
    ([1, 2], (1, 2)),
    ({'a': 1, 'b': 2, 'c': 3}, ('a', 'b', 'c')),
))
def test_force_tuple(obj, expected):
    actual = sequences.force_tuple(obj)
    assert expected == actual
