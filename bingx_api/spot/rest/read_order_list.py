from datetime import datetime
from time import sleep
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
from robot_one.api.bingx.spot.rest.url import SPOT_V1_TRADE_HISTORY_ORDERS

__all__ = [
    "Data",
    "EndpointResponse",
    "OrderUpdate",
    "query_order_list_full",
    "query_order_list",
    "QueryOrderList",
    "request_order_list",
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


class QueryOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    end_time: int | None = Field(default=None, description="End timestamp, Unit: ms")
    page_index: int = Field(default=1)
    page_size: int = Field(
        default=100,
        description="Page number, must >0,If not specified, it defaults to 1.",
    )
    order_id: int | None = Field(
        default=None,
        description="If orderId is set, orders >= orderId. Otherwise, the most recent orders will be returned.",
    )
    start_time: int | None = Field(
        default=None, description="Start timestamp, Unit: ms"
    )
    symbol: str | None = Field(default=None, description="Trading pair, e.g., BTC-USDT")
    type: OrderType | None = Field(
        default=None,
        description="order type: MARKET/LIMIT/TAKE_STOP_LIMIT/TAKE_STOP_MARKET/TRIGGER_LIMIT/TRIGGER_MARKET",
    )
    status: StatusType | None = Field(
        default=None,
        description="status: FILLED (fully filled) CANCELED: (canceled) FAILED: (failed)",
    )


def request_order_list(
    query: QueryOrderList,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SPOT_V1_TRADE_HISTORY_ORDERS
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


def query_order_list(query: QueryOrderList) -> list[OrderUpdate]:
    """Query the user's historical orders (order status is completed or canceled)."""

    response = request_order_list(query=query)
    response.raise_for_status()
    endpoint_response = EndpointResponse.model_validate_json(response.text)

    return endpoint_response.data.orders


def query_order_list_full(
    query: QueryOrderList,
    sleep_s: float = 0,
) -> list[OrderUpdate]:
    order_list_full = []

    while True:
        order_list = query_order_list(query=query)
        order_list_full.extend(order_list)

        if order_list and len(order_list) == query.page_size:
            query.page_index = query.page_index + 1
        else:
            break

        if sleep_s:
            sleep(sleep_s)

    return order_list_full


def query_order_list_full_by_order_id(
    start_order_id: int,
    page_size: int = 100,
    sleep_s: float = 0,
    symbol: str | None = None,
) -> list[OrderUpdate]:
    order_list_full = []
    page_index = 1

    if 1 > page_size > 100:
        raise ValueError("page_size should be: 1 <= page_size <= 100")

    while True:
        order_list = query_order_list(
            query=QueryOrderList(
                order_id=start_order_id,
                page_size=page_size,
                page_index=page_index,
                symbol=symbol,
            ),
        )
        page_index += 1
        order_list_full.extend(order_list)

        if order_list and len(order_list) > 1:
            order_id_list = [order.order_id for order in order_list]
            start_order_id = max(order_id_list)
        else:
            break

        if sleep_s:
            sleep(sleep_s)

    return order_list_full


if __name__ == "__main__":
    _order_list = query_order_list(
        query=QueryOrderList(
            end_time=int(datetime.now().timestamp() * 1000),
            page_size=100,
            start_time=int(datetime.now().timestamp() * 1000) - 10 * 3600 * 1000,
            # symbol="BTC-USDT",
        ),
    )
    print("result:", _order_list, len(_order_list))

    # _order_list_full = query_order_list_full_by_order_id(
    #     start_order_id=1777961517182779392,
    #     symbol="BTC-USDT",
    # )
    # print("result:", len(_order_list_full), _order_list_full)

    # _order_list_full = query_order_list_full(
    #     query=QueryOrderList(
    #         end_time=int(datetime.now().timestamp()) * 1000,
    #         start_time=int(datetime.now().timestamp() * 1000) - 36 * 3600 * 1000,
    #         symbol="CKB-USDT",
    #     ),
    # )
    # print("result:", len(_order_list_full), _order_list_full)
