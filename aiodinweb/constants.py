import datetime
import enum
import odin

from odin.fields.base import BaseField


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
    Integer = 'integer', 'int32', int, odin.IntegerField
    Long = 'integer', 'int64', int, odin.IntegerField
    Float = 'number', 'float', float, odin.FloatField
    Double = 'number', 'double', float, odin.FloatField
    String = 'string', None, str, odin.StringField
    Byte = 'string', 'byte', bytes, None
    Binary = 'string', 'binary', bytes, None
    Boolean = 'boolean', None, bool, odin.BooleanField
    Date = 'string', 'date', datetime.date, odin.DateField
    Time = 'string', 'time', datetime.time, odin.TimeField
    DateTime = 'string', 'date-time', datetime.datetime, odin.DateTimeField
    Email = 'string', 'email', str, odin.EmailField
    IPv4 = 'string', 'ipv4', str, odin.IPv4Field
    IPv6 = 'string', 'ipv6', str, odin.IPv6Field
    Uri = 'string', 'uri', str, odin.UrlField
    Regex = 'string', 'regex', str, odin.StringField
    Password = 'string', 'password', str, odin.StringField

    def __new__(cls, type_: str, format_: str, native_type: type, odin_field: BaseField) -> 'DataType':
        instance = object.__new__(cls)
        instance._value_ = f"{type_}:{format_}" if format_ else type_
        instance.type = type_
        instance.format = format_
        instance.native_type = native_type
        instance.odin_field = odin_field
        return instance

    def __str__(self):
        return self.type
