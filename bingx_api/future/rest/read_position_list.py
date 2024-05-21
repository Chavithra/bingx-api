from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_USER_POSITIONS


class Position(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    position_id: int
    symbol: str
    currency: str
    position_amt: float
    available_amt: float
    position_side: str
    isolated: bool
    avg_price: float
    initial_margin: float
    leverage: int
    unrealized_profit: float
    realised_profit: float
    liquidation_price: float


class ResponsePosition(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    msg: str
    data: list[Position]

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryPosition(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str | None = Field(default=None)
    recvWindow: int = Field(default=0)


def request_position_list(
    query: QueryPosition | None = None,
    session: Session | None = None,
) -> Response:
    query = query or QueryPosition()
    session = session or build_session()

    url = SWAP_V2_USER_POSITIONS
    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="GET",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)
    prepped = get_signed_request(prepared_request=prepped)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def query_position_list(query: QueryPosition | None = None) -> list[Position]:
    response = request_position_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponsePosition.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    order_list = query_position_list(
        query=QueryPosition(),
    )

    print("result:", order_list)
