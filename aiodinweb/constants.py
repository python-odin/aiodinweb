import enum


class Method(str, enum.Enum):
    """
    HTTP Request Method
    """
    Get = 'GET'
    Put = 'PUT'
    Post = 'POST'
    Delete = 'DELETE'
    Options = 'OPTIONS'
    Head = 'HEAD'
    Patch = 'PATCH'


class In(str, enum.Enum):
    """
    The location of the parameter.
    """
    Query = 'query'
    Header = 'header'
    Path = 'path'
    Cookie = 'cookie'


class DataType(enum.Enum):
    """
    Primitive data types in the OAS are based on the types supported.
    """
    Integer = ('integer', 'int32')
    Long = ('integer', 'int64')
    Float = ('number', 'float')
    Double = ('number', 'double')
    String = ('string', None)
    Byte = ('string', 'byte')
    Binary = ('string', 'binary')
    Boolean = ('boolean', None)
    Date = ('string', 'date')
    DateTime = ('string', 'date-time')
    Password = ('string', 'password')

    @property
    def type(self):
        return self.value[0]

    @property
    def format(self):
        return self.value[1]
