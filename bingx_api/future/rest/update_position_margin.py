from enum import IntEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_TRADE_POSITION_MARGIN

SideType = Literal[
    "LONG",
    "SHORT",
]


class PositionType(IntEnum):
    INCREASE = 1
    DECREASE = 2


class ResponseUpdatePositionMargin(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    amount: float
    type: PositionType

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryUpdatePositionMargin(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    amount: float
    position_side: SideType
    recvWindow: int = Field(default=0)
    symbol: str
    type: PositionType


def request_update_position_margin(
    query: QueryUpdatePositionMargin,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_POSITION_MARGIN
    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="POST",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)
    prepped = get_signed_request(prepared_request=prepped)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def query_update_position_margin(query: QueryUpdatePositionMargin) -> ResponseUpdatePositionMargin:
    response = request_update_position_margin(query=query)
    response.raise_for_status()
    model = ResponseUpdatePositionMargin.model_validate_json(response.text)

    return model


if __name__ == "__main__":
    result = query_update_position_margin(
        query=QueryUpdatePositionMargin(
            amount=10,
            symbol="NEAR-USDT",
            type=PositionType.DECREASE,
            position_side="LONG",
        ),
    )

    print("result:", result)
