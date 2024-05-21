from typing import Any, Literal

from orjson import dumps
from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_TRADE_BATCH_ORDERS

__all__ = [
    "DataDeleteOrder",
    "DeletedOrder",
    "OpenedOrder",
    "query_delete_order_list",
    "QueryDeleteOrderList",
    "request_delete_order_list",
    "ResponseDeleteOrderlist",
    "ResponseDeleteOrderlist",
]

SideType = Literal["BUY", "SELL"]

class OpenedOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    symbol: str | None = Field(default=None)
    price: float | None = Field(default=None)
    time: int | None = Field(default=None)


class FailedOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    order_id: int
    client_order_id: str | None = Field(default=None)
    error_code: int
    error_message: str | None = Field(default=None)


class DeletedOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    symbol: str
    price: float
    time: int
    order_id: int
    side: SideType
    position_side: str | None = Field(default=None)
    type: str | None = Field(default=None)
    orig_qty: float
    executed_qty: float | None = Field(default=None)
    avg_price: float | None = Field(default=None)
    cum_quote: float | None = Field(default=None)
    stop_price: float | str | None = Field(default=None)
    profit: float | None = Field(default=None)
    commission: float | None = Field(default=None)
    status: str | None = Field(default=None)
    update_time: int | None = Field(default=None)
    leverage: str | None = Field(default=None)
    client_order_id: str
    id: int | None = Field(default=None)
    advanceAttr: float | None = Field(default=None)
    position_id: float | None = Field(default=None, alias="position_id")
    take_profit_entrust_price: float | None = Field(default=None)
    stop_loss_entrust_price: float | None = Field(default=None)
    order_type: str | None = Field(default=None)
    working_type: str | None = Field(default=None)
    only_one_position: bool | None = Field(default=None)
    reduce_only: bool | None = Field(default=None)
    stop_guaranteed: str | None = Field(default=None)
    trigger_order_id: float | None = Field(default=None)


class DataDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    success: list[DeletedOrder] | None = Field(default_factory=list)
    failed: list[FailedOrder] | None = Field(default_factory=list)


class ResponseDeleteOrderlist(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
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


class QueryDeleteOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    order_id_list: list[int] | None = Field(default=None)
    client_order_id_list: list[str] | None = Field(default=None)
    symbol: str | None = Field(default=None)

    recv_window: int | None = Field(default=None)

    @field_serializer("order_id_list", when_used="always")
    @staticmethod
    def serialize_order_id_list(order_id_list: list[int] | None) -> bytes | None:
        value = None
        if order_id_list:
            value = dumps(order_id_list)
        return value

    @field_serializer("client_order_id_list", when_used="always")
    @staticmethod
    def serialize_client_order_id_list(
        client_order_id_list: list[int] | None,
    ) -> bytes | None:
        value = None
        if client_order_id_list:
            value = dumps(client_order_id_list)
        return value


def request_delete_order_list(
    query: QueryDeleteOrderList,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_BATCH_ORDERS

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


def query_delete_order_list(query: QueryDeleteOrderList) -> ResponseDeleteOrderlist:
    response = request_delete_order_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseDeleteOrderlist.model_validate_json(response.text)

    return endpoint_response


if __name__ == "__main__":
    result = request_delete_order_list(
        query=QueryDeleteOrderList(
            order_id_list=[1781270441522049024, 1781270440964206592],
            # symbol="BTC-USDT",
        ),
    )

    print("result:", result)
