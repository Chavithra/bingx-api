from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import (
    SWAP_V2_TRADE_ALL_OPEN_ORDERS,
)


class TakeProfit(BaseModel):
    type: str
    quantity: int
    stopPrice: int
    price: int
    workingType: str


class StopLoss(BaseModel):
    type: str
    quantity: int
    stopPrice: int
    price: int
    workingType: str


class DeletedOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    advanceAttr: int
    avgPrice: str
    clientOrderId: str
    commission: str
    cumQuote: str
    executedQty: str
    leverage: str
    orderId: int
    orderType: str
    origQty: str
    positionID: int
    positionSide: str
    price: str
    profit: str
    side: str
    status: str
    stopLoss: StopLoss
    stopLossEntrustPrice: int
    stopPrice: str | None = Field(default=None)
    symbol: str
    takeProfit: TakeProfit
    takeProfitEntrustPrice: int
    time: int
    type: str
    updateTime: int
    workingType: str


class QueryDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    recv_window: int | None = Field(default=None)


class DataDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    success: list[DeletedOrder] | None = Field(default=None)
    failed: list[DeletedOrder] | None = Field(default=None)


class ResponseDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    msg: str
    data: DataDeleteOrder

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


def request_delete_all_open_order(
    query: QueryDeleteOrder,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_ALL_OPEN_ORDERS
    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="DELETE",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)
    prepped = get_signed_request(prepared_request=prepped)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def query_delete_all_open_order(query: QueryDeleteOrder) -> ResponseDeleteOrder:
    response = request_delete_all_open_order(query=query)
    response.raise_for_status()
    endpoint_response = ResponseDeleteOrder.model_validate_json(response.text)

    return endpoint_response


if __name__ == "__main__":
    order = query_delete_all_open_order(
        query=QueryDeleteOrder(
            symbol="BTC-USDT",
        ),
    )

    print("result:", order)
