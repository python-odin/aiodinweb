import pytest

from aiodinweb import data_structures


class TestParameter:
    pass


class TestUrlPath:
    def test_init(self):
        target = data_structures.UrlPath('api', 'path')

        assert ('api', 'path') == target

    def test_add__valid(self):
        left = data_structures.UrlPath('a', 'b', 'c')
        right = data_structures.UrlPath('d', 'e', 'f')

        actual = left + right

        assert ('a', 'b', 'c', 'd', 'e', 'f') == actual

    def test_add__other_type(self):
        left = data_structures.UrlPath('a', 'b', 'c')
        right = 'd'

        with pytest.raises(TypeError):
            left + right

    def test_add__right_absolute(self):
        left = data_structures.UrlPath.parse('a/b/c')
        right = data_structures.UrlPath.parse('/d/e/f')

        with pytest.raises(ValueError):
            left + right

    @pytest.mark.parametrize('left_path, right_path, expected', (
            (('a', 'b', 'c'), ('d', 'e', 'f'))
    ))
    def __add__(self, left_path, right_path, expected):
        target = data_structures.UrlPath('')

    def test_div(self):
        pass
