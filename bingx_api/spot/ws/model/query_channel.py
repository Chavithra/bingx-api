from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ReqType(str, Enum):
    SUB = "sub"
    UNSUB = "unsub"


class QueryChannel(BaseModel):
    """
    Example:
    {
        "id": "id1",
        "reqType": "sub",
        "dataType": "BTC-USDT@lastPrice",
    }
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str = Field(description="An identifier that service will send back.")
    req_type: ReqType
    data_type: str = Field(
        description="(Un)subscribed data type, e.g., BTC-USDT@lastPrice",
    )
