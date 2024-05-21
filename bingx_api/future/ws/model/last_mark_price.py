from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class LastMarkPrice(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    e: str = Field(description="Event type.")
    E: int = Field(description="Event time.")
    s: str = Field(description="Trading pair, e.g., BTC-USDT.")
    p: float = Field(description="Latest mark price.")


class ResponseMarkPrice(BaseModel):
    """For data_type = `<symbol>@lastPrice`

    Example:
    {
        "code": 0,
        "dataType": "FLOKI-USDT@lastPrice",
        "data": {
            "e": "lastPriceUpdate",
            "E": 1710351327012,
            "s": "FLOKI-USDT",
            "c": "0.00026882",
        },
    }
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    data_type: str
    data: LastMarkPrice

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data
