from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.spot.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.spot.rest.url import SPOT_V1_TRADE_OPEN_ORDERS


__all__ = [
    "Data",
    "EndpointResponse",
    "OrderUpdate",
    "query_open_order_list",
    "QueryOpenOrderList",
    "request_open_order_list",
    "StopLoss",
    "TakeProfit",
]

SideType = Literal["BUY", "SELL"]
StatusType = Literal[
    "CANCELED",
    "CANCELLED",
    "EXPIRED",
    "FAILED",
    "FILLED",
    "NEW",
    "PARTIALLY_FILLED",
    "PENDING",
    "WORKING",
]
OrderType = Literal[
    "MARKET",
    "LIMIT",
    "TAKE_STOP_LIMIT",
    "TAKE_STOP_MARKET",
    "TRIGGER_LIMIT",
    "TRIGGER_MARKET",
]


class TakeProfit(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: str
    quantity: int
    stop_price: int
    price: int
    working_type: str


class StopLoss(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: str
    quantity: int
    stop_price: int
    price: int
    working_type: str


class OrderUpdate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    client_order_id: str = Field(alias="clientOrderID")
    cummulative_quote_qty: float
    executed_qty: float
    fee: float
    order_id: int
    orig_qty: float
    orig_quote_order_qty: float
    price: float
    side: SideType
    status: StatusType = Field(
        description="Order status: NEW, PENDING, PARTIALLY_FILLED, FILLED, CANCELED, FAILED"
    )
    stop_price: float = Field(description="trigger price", alias="StopPrice")
    symbol: str
    time: int
    type: OrderType
    update_time: int


class Data(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    orders: list[OrderUpdate]


class EndpointResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: Data

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryOpenOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str | None = Field(default=None, description="Trading pair, e.g., BTC-USDT")
    recv_window: float | None = Field(default=None)


def request_open_order_list(
    query: QueryOpenOrderList | None = None,
    session: Session | None = None,
) -> Response:
    query = query or QueryOpenOrderList()
    session = session or build_session()

    url = SPOT_V1_TRADE_OPEN_ORDERS
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


def query_open_order_list(query: QueryOpenOrderList | None = None) -> list[OrderUpdate]:
    """Query the user's historical orders (order status is completed or canceled)."""

    response = request_open_order_list(query=query)
    response.raise_for_status()
    endpoint_response = EndpointResponse.model_validate_json(response.text)

    return endpoint_response.data.orders


if __name__ == "__main__":
    _order_list = query_open_order_list(
        query=QueryOpenOrderList(
            symbol="XRP-USDT",
        ),
    )

    print("result number:", len(_order_list))

    for _order in _order_list:
        print(_order)
