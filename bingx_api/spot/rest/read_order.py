from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.spot.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.spot.rest.read_order_list import OrderUpdate
from robot_one.api.bingx.spot.rest.url import SPOT_V1_TRADE_QUERY

__all__ = [
    "ResponseOrder",
    "QueryOrder",
    "request_order",
    "query_order",
]


class ResponseOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: OrderUpdate

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    client_order_id: str | None = Field(default=None, alias="clientOrderID")
    order_id: int | None = Field(default=None)
    recv_window: int | None = Field(default=None)
    symbol: str


def request_order(
    query: QueryOrder,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SPOT_V1_TRADE_QUERY

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


def query_order(query: QueryOrder) -> OrderUpdate:
    response = request_order(query=query)
    response.raise_for_status()
    endpoint_response = ResponseOrder.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    result = query_order(
        query=QueryOrder(
            order_id=1777048280941625344,
            symbol="CKB-USDT",
        ),
    )

    print("result:", result)
