import re

from typing import Union, Sequence, Iterable, Callable, Dict, Any

from . import constants
from .utils.sequences import dict_filter


class Parameter:
    """
    Describes a single operation parameter.

    A unique parameter is defined by a combination of a name and location.
    """
    def __init__(self, name: str, in_: constants.In, *,
                 description: str=None,
                 required: bool=None,
                 allow_empty: bool=None,
                 data_type: constants.DataType=None):
        """
        :param name: The name of the parameter
        :param in_: The location of the parameter
        :param description: A brief description of the parameter.
        :param required: Determines whether this parameter is mandatory.
        :param allow_empty: Sets the ability to pass empty-valued parameters.
        """
        self.name = name
        self.in_ = in_
        self.description = description
        self.required = required
        self.allow_empty = allow_empty
        self.data_type = data_type

    def __hash__(self):
        return hash(self.name + str(self.in_))

    def __eq__(self, other: 'Parameter') -> bool:
        """
        Determine if parameters are the same. This is based on the combination
        of `name` and `in_` attributes
        """
        if isinstance(other, Parameter):
            return self.name == other.name and self.in_ == other.in_
        return NotImplemented

    def __str__(self) -> str:
        return f"{{{self.name}}}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self.in_!r})"

    def to_openapi(self) -> Dict[str, Any]:
        """
        Generate OpenAPI documentation
        """
        return dict_filter({
            'name': self.name,
            'in': self.in_,
            'description': self.description,
            'required': True if self.in_ == constants.In.Path else self.required,
            'allow_empty': self.allow_empty if self.in_ == constants.In.Query else None,
            'schema': dict_filter({'type': self.data_type.type, 'format': self.data_type.format}),
        })


# Name scheme that follows Python names rules for variables
PATH_PARAM_RE = re.compile(r'^{([a-zA-Z_]\w*)(?::([a-zA-Z_]\w*))?(?::([-^$+*:\w\\\[\]|]+))?}$')


class UrlPath(tuple):
    """
    URL Path object.
    """
    __slots__ = ()

    Atoms = Union['UrlPath', str, Sequence[Union[str, Parameter]]]

    @classmethod
    def from_object(cls, obj: Atoms) -> 'UrlPath':
        if isinstance(obj, UrlPath):
            return obj

        if isinstance(obj, str):
            return UrlPath.parse(obj)

        if isinstance(obj, Parameter):
            if obj.in_ != constants.In.Path:
                raise ValueError("Only path parameters can be used in a UrlPath object.")
            return UrlPath(obj)

        if isinstance(obj, (tuple, list)):
            if any(not isinstance(a, (str, Parameter)) for a in obj):
                raise TypeError("Only str and Parameter objects can be used in a UrlPath")
            return UrlPath(*obj)

        raise TypeError(f"Unable to convert object to UrlPath: {obj!r}")

    @classmethod
    def parse(cls, url_path: str) -> 'UrlPath':
        """
        Parse a string into a URL path
        """
        if not url_path:
            return cls()

        atoms = []
        for atom in url_path.rstrip('/').split('/'):
            # Identify parameters
            if '{' in atom or '}' in atom:
                m = PATH_PARAM_RE.match(atom)
                if not m:
                    raise ValueError(f"Invalid path param: {atom}")

                # Parse out name and type
                name, param_type, param_arg = m.groups()
                try:
                    data_type = constants.DataType[param_type]
                except KeyError:
                    if param_type is not None:
                        raise ValueError(f"Unknown param type `{param_type}` in: {atom}")
                    data_type = constants.DataType.String

                atoms.append(Parameter(name, constants.In.Path, required=True, data_type=data_type))
            else:
                atoms.append(atom)

        return cls(*atoms)

    def __new__(cls, *atoms: Union[str, Parameter]) -> 'UrlPath':
        return super().__new__(cls, atoms)

    def __init__(self, *atoms: Union[str, Parameter]) -> None:
        super().__init__()

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            ', '.join(repr(a) for a in self)
        )

    def __hash__(self) -> int:
        return hash(self.format())

    def __add__(self, other: 'UrlPath') -> 'UrlPath':
        if isinstance(other, UrlPath):
            if other and other.is_absolute:
                raise ValueError("Right argument cannot be absolute")
            return UrlPath(*tuple.__add__(self, other))
        return NotImplemented

    def __div__(self, other: Union[str, 'UrlPath', Parameter]) -> 'UrlPath':
        if isinstance(other, UrlPath):
            return self + other
        if isinstance(other, str):
            return self + UrlPath.parse(other)
        if isinstance(other, Parameter):
            if other.in_ != constants.In.Path:
                raise ValueError("Right argument must be a path Parameter")
            return self + UrlPath(other)
        return NotImplemented

    __truediv__ = __div__

    def __getitem__(self, item: Union[int, slice]) -> Union[str, 'UrlPath']:
        if isinstance(item, slice):
            return UrlPath(*tuple.__getitem__(self, item))
        else:
            return tuple.__getitem__(self, item)

    def startswith(self, other: Atoms) -> bool:
        """
        Return True if this path starts with the other path.
        """
        try:
            other = UrlPath.from_object(other)
        except ValueError:
            raise TypeError('startswith first arg must be UrlPath, str, PathParam, not {}'.format(type(other)))
        else:
            return self[:len(other)] == other

    @property
    def is_absolute(self) -> bool:
        """
        Is an absolute URL
        """
        return len(self) and self[0] == ''

    @property
    def parameters(self) -> Iterable[Parameter]:
        """
        All parameters in this URL path
        """
        return (a for a in self if isinstance(a, Parameter))

    @staticmethod
    def default_parameter_formatter(parameter: Parameter) -> str:
        """
        Format a parameter to be consumable by the `UrlPath.parse`.
        """
        args = [parameter.name]
        if parameter.data_type:
            args.append(parameter.data_type.name)
        # if path_node.type_args:
        #     args.append(path_node.type_args)
        return "{{{}}}".format(':'.join(args))

    def format(self, parameter_formatter: Callable[[Parameter], str]=None, separator: str='/') -> str:
        """
        Format a URL path.

        An optional function can be supplied for converting a `Parameter`
        into a string.

        """
        if self == ('',):
            return separator
        else:
            parameter_formatter = parameter_formatter or self.default_parameter_formatter
            return separator.join(parameter_formatter(a) if isinstance(a, Parameter) else a for a in self)


EmptyPath = UrlPath()
RootPath = UrlPath('')
