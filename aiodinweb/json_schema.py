"""
JSON Schema
~~~~~~~~~~~

Generate a JSON Schema from an Odin resource.

"""
from odin.fields.base import BaseField
from odin.fields.future import EnumField
from odin.fields.virtual import VirtualField
from odin.resources import ResourceBase, ResourceOptions
from odin.utils import getmeta
from typing import Type, Dict, Tuple, Any

from .constants import DataType
from .utils.sequences import dict_filter


FIELD_RESOLUTION_ORDER = [
    DataType.Long,
    DataType.Float,
    DataType.Email,
    DataType.IPv4,
    DataType.IPv6,
    DataType.Uri,
    DataType.String,
    DataType.Boolean,
    DataType.Time,
    DataType.Date,
    DataType.DateTime,
]


def resolve_data_type(field: BaseField) -> DataType:
    """
    Resolve field to DataType
    """
    for dt in FIELD_RESOLUTION_ORDER:
        if isinstance(field, dt.odin_field):
            return dt


def field_schema(field: BaseField, meta: ResourceOptions) -> Dict[str, Any]:
    """
    Generate a JSON Schema based on an Odin field.
    """
    schema = {
        'title': field.verbose_name,
        'description': field.doc_text or None
    }

    data_type = resolve_data_type(field)
    if data_type:
        schema['type'] = data_type.type
        if data_type.format:
            schema['format'] = data_type.format

    if isinstance(field, VirtualField) or field in meta.readonly_fields:
        schema['readOnly'] = True

    if isinstance(field, EnumField):
        schema['enum'] = [str(e) for e in field.enum]
    elif hasattr(field, 'choices') and field.choices:
        schema['enum'] = [c[0] for c in field.choices]

    return dict_filter(schema)


def resource_schema(resource: Type[ResourceBase]) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a JSON Schema based on an Odin resource.
    """
    meta = getmeta(resource)

    # Process fields to build schema elements
    required = []
    properties = {}
    for field in meta.fields:
        if not field.null:
            required.append(field.name)

        properties[field.name] = field_schema(field, meta)

    return meta.name, dict_filter(
        type='object',
        title=meta.verbose_name,
        description=(resource.__doc__ or '').strip(),
        required=required,
        properties=properties,
    )
