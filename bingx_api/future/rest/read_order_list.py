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

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_TRADE_ALL_ORDERS


__all__ = [
    "Data",
    "EndpointResponse",
    "OrderUpdate",
    "query_order_list_full_by_order_id",
    "query_order_list_full_by_start_time",
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
    "PARTIALLYFILLED",
    "PENDING",
    "WORKING",
]
OrderType = Literal[
    "LIMIT",
    "MARKET",
    "STOP_MARKET",
    "STOP",
    "TAKE_PROFIT_MARKET",
    "TAKE_PROFIT",
    "TRAILING_STOP_MARKET",
    "TRIGGER_LIMIT",
    "TRIGGER_MARKET",
]


class TakeProfit(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="allow",
        populate_by_name=True,
    )

    price: int
    quantity: int
    stop_guaranteed: str
    stop_price: int
    type: str
    working_type: str


class StopLoss(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="allow",
        populate_by_name=True,
    )

    price: int
    quantity: int
    stop_guaranteed: str
    stop_price: int
    type: str
    working_type: str


class OrderUpdate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="allow",
        populate_by_name=True,
    )

    advance_attr: float
    avg_price: float
    client_order_id: str
    commission: float
    cum_quote: float
    executed_qty: float
    leverage: str
    only_one_position: bool
    order_id: int
    order_type: str = Field(description="Seems unused.")
    orig_qty: float
    position_id: int = Field(alias="positionID")
    position_side: str
    post_only: bool
    price: float
    profit: float
    reduce_only: bool
    side: SideType
    status: StatusType
    stop_guaranteed: bool
    stop_loss_entrust_price: float
    stop_loss: StopLoss | None = Field(default=None)
    stop_price: str
    symbol: str
    take_profit_entrust_price: float
    take_profit: TakeProfit | None = Field(default=None)
    time: int
    trailing_stop_distance: float
    trailing_stop_rate: float
    trigger_order_id: int
    type: OrderType
    update_time: int
    working_type: str


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

    end_time: int | None = Field(default=None)
    limit: int
    order_id: int | None = Field(default=None)
    start_time: int | None = Field(default=None)
    symbol: str | None = Field(default=None)


def request_order_list(
    query: QueryOrderList,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_ALL_ORDERS
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
    """Query the user's historical orders (order status is canceled or filled)."""

    response = request_order_list(query=query)
    response.raise_for_status()
    endpoint_response = EndpointResponse.model_validate_json(response.text)

    return endpoint_response.data.orders


def query_order_list_full_by_order_id(
    start_order_id: int,
    limit: int = 1000,
    sleep_s: float = 0,
    symbol: str | None = None,
) -> list[OrderUpdate]:
    """Starts after an `start_order_id` not included in the result."""

    order_list_full = []

    while True:
        order_list = query_order_list(
            query=QueryOrderList(
                order_id=start_order_id,
                limit=limit,
                symbol=symbol,
            ),
        )
        order_list_full.extend(order_list)

        if order_list and len(order_list) == limit:
            order_id_list = [order.order_id for order in order_list]
            start_order_id = max(order_id_list)
        else:
            break

        if sleep_s:
            sleep(sleep_s)

    return order_list_full


def query_order_list_full_by_start_time(
    start_time: int,
    sleep_s: float = 0,
    symbol: str | None = None,
) -> list[OrderUpdate]:
    order_list_full = []
    order_list = query_order_list(
        query=QueryOrderList(
            limit=1,
            start_time=start_time,
            symbol=symbol,
        ),
    )

    order_list_full.extend(order_list)

    if order_list:
        start_order_id = order_list[0].order_id

        order_list = query_order_list_full_by_order_id(
            start_order_id=start_order_id,
            limit=1000,
            sleep_s=sleep_s,
            symbol=symbol,
        )

        order_list_full.extend(order_list)

    return order_list_full


if __name__ == "__main__":
    from datetime import datetime, timedelta

    # _order_list = query_order_list(
    #     query=QueryOrderList(
    #         end_time=int(datetime.now().timestamp()) * 1000,
    #         limit=100,
    #         start_time=int(datetime.now().timestamp() * 1000) - 40 * 3600 * 1000,
    #         # symbol="BTC-USDT",
    #     ),
    # )
    # print("result:", _order_list, len(_order_list))

    minimum_delta = timedelta(minutes=5)
    _start_time = int(
        (datetime.now().timestamp() - minimum_delta.total_seconds()) * 1000
    )
    _order_list_full = query_order_list_full_by_start_time(
        # start_time=int((datetime.now().timestamp() - minimum_delta.total_seconds()) * 1000),
        start_time=_start_time,
        symbol="BTC-USDT",
    )

    print("result:", _order_list_full, len(_order_list_full))
