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
from robot_one.api.bingx.future.rest.url import (
    SWAP_V2_TRADE_ORDER,
)

__all__ = [
    "CreatedOrder",
    "DataCreateOrder",
    "OrderType",
    "PositionSideType",
    "QueryCreateOrder",
    "ResponseCreateOrder",
    "SideType",
    "StopLoss",
    "TakeProfit",
    "TimeInForceType",
    "WorkingType",
]

SideType = Literal["BUY", "SELL"]
OrderType = Literal[
    "LIMIT",
    "MARKET",
    "STOP_MARKET",
    "TAKE_PROFIT_MARKET",
    "STOP",
    "TAKE_PROFIT",
    "TRIGGER_LIMIT",
    "TRIGGER_MARKET",
    "TRAILING_STOP_MARKET",
    "TRAILING_TP_SL",
]
PositionSideType = Literal["LONG", "SHORT"]
TimeInForceType = Literal[
    "PostOnly",
    "GTC",
    "IOC",
    "FOK",
]
WorkingType = Literal[
    "MARK_PRICE",
    "CONTRACT_PRICE",
    "INDEX_PRICE",
]


class QueryCreateOrder(BaseModel):
    """
    Differents fields are available according to the order type.

    Fields when type == MARKET | STOP_MARKET:
        position_side (PositionSideType): Long or short.
        quantity (float): Amount in coins.
        side (SideType): Buy or sell.

    Fields when type == LIMIT:
        position_side (PositionSideType): Long or short.
        price (float): Bidded/Asked price.
        quantity (float): Amount in coins.
        side (SideType): Buy or sell.

    Fields when type == TRAILING_STOP_MARKET | TRAILING_TP_SL:
        activation_price (float, optional): Order triggering price.
        position_side (PositionSideType): Long or short.
        price (float, optional): It's the trailing distance is usdt.
            Need either `price` or `price_rate`.
        price_rate (float, optional): It's the trailing distance rate (%).
            Need either `price` or `price_rate`.
        quantity (float): Amount in coins.
        side (SideType): Buy or sell.

    Attributes:
        price : trailing stop distance in usdt for `trailing_stop_market` and `trailing_tp_sl`
        quantity : in `coin`` only not in `usdt``
        reduce_only : makes sure this order gets the market maker discount
        working_type : default is `mark_price`
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    activation_price: float | None = Field(default=None)
    client_order_id: str | None = Field(
        default=None,
        max_length=40,
        validation_alias="clientOrderID",
    )
    close_position: str | None = Field(default=None)
    position_side: PositionSideType = Field(default="LONG")
    price_rate: float | None = Field(default=None, ge=0, le=1)
    price: float | None = Field(default=None)
    quantity: float
    recv_window: int | None = Field(default=None)
    reduce_only: str | None = Field(default=None)
    side: SideType
    stop_guaranteed: bool | None = Field(default=None)
    stop_loss: str | None = Field(default=None)
    stop_price: float | None = Field(default=None)
    symbol: str
    take_profit: str | None = Field(default=None)
    time_in_force: TimeInForceType | None = Field(default=None)
    type: OrderType
    working_type: WorkingType | None = Field(default=None)

    @staticmethod
    def helper_required_for_order_type(
        data: Any,
        field_name: str,
        required_type_set: set[OrderType],
    ):
        if data.get(field_name) is None and data.get("type") in required_type_set:
            raise ValueError(
                f"`{field_name}` is required for the following order type: "
                ", ".join(literal_value for literal_value in required_type_set)
            )

        if (
            data.get(field_name) is not None
            and data.get("type") not in required_type_set
        ):
            raise ValueError(
                f"`{field_name}` should be used with for the following order type: "
                ", ".join(literal_value for literal_value in required_type_set)
            )

    @staticmethod
    def helper_available_for_order_type(
        data: Any,
        field_name: str,
        required_type_set: set[OrderType],
    ):
        if (
            data.get(field_name) is not None
            and data.get("type") not in required_type_set
        ):
            raise ValueError(
                f"`{field_name}` should be used with for the following order type: "
                ", ".join(literal_value for literal_value in required_type_set)
            )

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_price(cls, data: Any) -> Any:
        if data.get("price") is not None and data.get("price_rate") is not None:
            raise ValueError("`price_rate` can't be used in conjunction with `price`.")

        if data.get("price_rate") is None:
            cls.helper_required_for_order_type(
                data=data,
                field_name="price",
                required_type_set={
                    "LIMIT",
                    "TRAILING_STOP_MARKET",
                    "TRAILING_TP_SL",
                    "TRIGGER_LIMIT",
                    "STOP",
                    "TAKE_PROFIT",
                },
            )

        return data

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_price_rate(cls, data: Any) -> Any:
        if data.get("price") is not None and data.get("price_rate") is not None:
            raise ValueError("`price_rate` can't be used in conjunction with `price`.")

        if data.get("price") is None:
            cls.helper_required_for_order_type(
                data=data,
                field_name="price_rate",
                required_type_set={
                    "TRAILING_STOP_MARKET",
                    "TRAILING_TP_SL",
                },
            )

        return data

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_stop_price(cls, data: Any) -> Any:
        cls.helper_required_for_order_type(
            data=data,
            field_name="stop_price",
            required_type_set={
                "TRIGGER_LIMIT",
                "STOP",
                "TAKE_PROFIT",
                "STOP_MARKET",
                "TAKE_PROFIT_MARKET",
                "TRIGGER_MARKET",
            },
        )

        return data

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_activation_price(cls, data: Any) -> Any:
        cls.helper_available_for_order_type(
            data=data,
            field_name="activation_price",
            required_type_set={
                "TRAILING_STOP_MARKET",
                "TRAILING_TP_SL",
            },
        )

        return data


class StopLoss(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    price: float
    stop_guaranteed: bool | None = Field(default=None)
    stop_price: float
    type: OrderType
    working_type: WorkingType  # DEFAULT IS `MARK_PRICE`


class TakeProfit(StopLoss):
    pass


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
    order_id: int
    position_side: PositionSideType = Field(default="LONG")
    reduce_only: bool | None = Field(default=None)
    price: float
    quantity: float
    side: SideType
    symbol: str
    type: OrderType
    working_type: WorkingType | None = Field(default=None)  # DEFAULT IS `MARK_PRICE`


class DataCreateOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    order: CreatedOrder


class ResponseCreateOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: DataCreateOrder

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

    url = SWAP_V2_TRADE_ORDER
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

    return endpoint_response.data.order


if __name__ == "__main__":
    created_order = query_create_order(
        query=QueryCreateOrder(
            quantity=0.001,
            price=61200,
            side="BUY",
            symbol="BTC-USDT",
            type="LIMIT",
        ),
    )

    print("result:", created_order)
