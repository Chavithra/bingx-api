from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_TRADE_OPEN_ORDERS
from robot_one.api.bingx.future.rest.read_order_list import OrderUpdate

__all__ = [
    "Data",
    "OrderUpdate",
    "query_open_order_list",
    "QueryOpenOrderList",
    "request_open_order_list",
    "ResponseOpenOrderList",
]


class Data(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    orders: list[OrderUpdate]


class ResponseOpenOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: Data


class QueryOpenOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    recv_window: int | None = Field(default=None)
    symbol: str | None = Field(default=None)


def request_open_order_list(
    query: QueryOpenOrderList,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_OPEN_ORDERS
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


def query_open_order_list(query: QueryOpenOrderList) -> list[OrderUpdate]:
    response = request_open_order_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseOpenOrderList.model_validate_json(response.text)

    return endpoint_response.data.orders


if __name__ == "__main__":
    open_order_list = request_open_order_list(
        query=QueryOpenOrderList(
            symbol="CKB-USDT",
        ),
    )

    print("result:", open_order_list)
