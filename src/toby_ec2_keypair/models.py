# DO NOT modify this file by hand, changes will be overwritten
import sys
from dataclasses import dataclass
from inspect import getmembers, isclass
from typing import (
    AbstractSet,
    Any,
    Generic,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from cloudformation_cli_python_lib.interface import (
    BaseModel,
    BaseResourceHandlerRequest,
)
from cloudformation_cli_python_lib.recast import recast_object
from cloudformation_cli_python_lib.utils import deserialize_list

T = TypeVar("T")


def set_or_none(value: Optional[Sequence[T]]) -> Optional[AbstractSet[T]]:
    if value:
        return set(value)
    return None


@dataclass
class ResourceHandlerRequest(BaseResourceHandlerRequest):
    # pylint: disable=invalid-name
    desiredResourceState: Optional["ResourceModel"]
    previousResourceState: Optional["ResourceModel"]


@dataclass
class ResourceModel(BaseModel):
    KeyName: Optional[str]
    PublicKeys: Optional[Sequence["_Key"]]
    Fingerprint: Optional[str]

    @classmethod
    def _deserialize(
        cls: Type["_ResourceModel"],
        json_data: Optional[Mapping[str, Any]],
    ) -> Optional["_ResourceModel"]:
        if not json_data:
            return None
        dataclasses = {n: o for n, o in getmembers(sys.modules[__name__]) if isclass(o)}
        recast_object(cls, json_data, dataclasses)
        return cls(
            KeyName=json_data.get("KeyName"),
            PublicKeys=deserialize_list(json_data.get("Key"), Key),
            Fingerprint=json_data.get("Fingerprint"),
        )


# work around possible type aliasing issues when variable has same name as a model
_ResourceModel = ResourceModel


@dataclass
class Key(BaseModel):
    keymaterial: Optional[str]

    @classmethod
    def _deserialize(
        cls: Type["_Key"],
        json_data: Optional[Mapping[str, Any]],
    ) -> Optional["_Key"]:
        if not json_data:
            return None
        return cls(
            keymaterial=json_data.get("keymaterial"),
        )


# work around possible type aliasing issues when variable has same name as a model
_Key = Key


