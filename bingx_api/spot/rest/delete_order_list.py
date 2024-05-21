from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.spot.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.spot.rest.create_order import (
    SideType,
    StatusType,
    OrderType,
)
from robot_one.api.bingx.spot.rest.url import SPOT_V1_TRADE_CANCEL_ORDERS

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

    client_order_id: str = Field(
        default="",
        max_length=40,
        validation_alias="clientOrderID",
    )
    cummulative_quote_qty: float
    executed_qty: float
    order_id: int
    orig_qty: float
    price: float
    side: SideType
    status: StatusType
    stop_price: float
    symbol: str
    type: OrderType


class DataDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    orders: list[DeletedOrder] = Field(default_factory=list)


class ResponseDeleteOrderlist(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    debugMsg: str
    msg: str
    data: DataDeleteOrder | None = Field(default=None)

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        # 100400: INVALID PARAMETER
        # MOST LIKELY THE ORDER DOESN'T EXIST OR WAS ALREADY CANCELED
        if data.get("code") not in [0, 100400]:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryDeleteOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    client_order_ids: list[str] | None = Field(default=None, alias="clientOrderIDs")
    order_ids: list[int] | None = Field(default=None)
    recv_window: int | None = Field(default=None)
    symbol: str

    @field_serializer("order_ids", when_used="always")
    @staticmethod
    def serialize_order_ids(order_ids: list[int] | None) -> str | None:
        value = None
        if order_ids:
            order_ids_str = [str(order_id) for order_id in order_ids]
            value = ",".join(order_ids_str)

        return value

    @field_serializer("client_order_ids", when_used="always")
    @staticmethod
    def serialize_client_order_ids(
        client_order_ids: list[int] | None,
    ) -> str | None:
        value = None
        if client_order_ids:
            client_order_ids_str = [str(order_id) for order_id in client_order_ids]

            value = ",".join(client_order_ids_str)
        return value


def request_delete_order_list(
    query: QueryDeleteOrderList,
    session: Session | None = None,
) -> Response:
    """
    Up on error cause by any of the order_id/client_order_id at any position:
    - None of the order are canceled
    - Only the first error is indicated in the error `msg`

    The field `debugMsg` seems to be always empty.
    """
    session = session or build_session()

    url = SPOT_V1_TRADE_CANCEL_ORDERS

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


def query_delete_order_list(query: QueryDeleteOrderList) -> ResponseDeleteOrderlist:
    response = request_delete_order_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseDeleteOrderlist.model_validate_json(response.text)

    return endpoint_response


if __name__ == "__main__":
    result = query_delete_order_list(
        query=QueryDeleteOrderList(
            # order_ids=[1780556252686745600, 1780556304037609472, 1780556350602772480],
            order_ids=[1780556350602772480, 1780556252686745600, 1780556304037609472],
            symbol="XRP-USDT",
        ),
    )

    print("result:", result)
