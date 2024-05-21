from enum import Enum
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
from robot_one.api.bingx.spot.rest.url import SPOT_V1_TRADE_ORDER

__all__ = [
    "CreatedOrder",
    "OrderType",
    "QueryCreateOrder",
    "ResponseCreateOrder",
    "SideType",
    "StatusType",
    "TimeInForceType",
    "WorkingType",
]


OrderType = Literal[
    "LIMIT",
    "MARKET",
    "TAKE_STOP_LIMIT",
    "TAKE_STOP_MARKET",
    "TRIGGER_LIMIT",
    "TRIGGER_MARKET",
]

WorkingType = Literal[
    "MARK_PRICE",
    "CONTRACT_PRICE",
    "INDEX_PRICE",
]

TimeInForceType = Literal[
    "PostOnly",
    "GTC",
    "IOC",
    "FOK",
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


class QueryCreateOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    new_client_order_id: str | None = Field(default=None, max_length=40)
    price: float | None = Field(default=None)
    quantity: float
    quote_order_qty: float | None = Field(default=None)
    recv_window: int | None = Field(default=None)
    side: SideType
    stop_price: float | None = Field(default=None)
    symbol: str
    time_in_force: TimeInForceType | None = Field(default=None)
    type: OrderType


class CreatedOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    client_order_id: str = Field(
        default="",
        max_length=40,
        validation_alias="clientOrderID",
    )
    cummulative_quote_qty: float
    executed_qty: float
    order_id: int
    orig_client_order_id: str = Field(default="")
    orig_qty: float
    price: float
    side: SideType
    status: StatusType
    symbol: str
    transact_time: int
    type: OrderType


class ResponseCreateOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    debug_msg: str
    data: CreatedOrder

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


def request_create_order(
    query: QueryCreateOrder,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SPOT_V1_TRADE_ORDER
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


def query_create_order(query: QueryCreateOrder) -> CreatedOrder:
    response = request_create_order(query=query)
    endpoint_response = ResponseCreateOrder.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    created_order = query_create_order(
        query=QueryCreateOrder(
            price=110.54,
            quantity=0.05,
            side="BUY",
            symbol="AAVE-USDT",
            type="LIMIT",
            # new_client_order_id="id3",
        ),
    )

    print("result:", created_order)
