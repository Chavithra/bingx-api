from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    model_validator,
    TypeAdapter,
)
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import (
    SWAP_V2_TRADE_BATCH_ORDERS,
)
from robot_one.api.bingx.future.rest.create_order import (
    CreatedOrder,
    SideType,
    OrderType,
    PositionSideType,
    QueryCreateOrder,
)


__all__ = [
    "CreatedOrder",
    "DataCreateOrderList",
    "SideType",
    "OrderType",
    "PositionSideType",
    "query_create_order_list",
    "QueryCreateOrder",
    "QueryCreateOrderList",
    "request_create_order_list",
    "ResponseCreateOrderList",
]


class QueryCreateOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    batch_orders: list[QueryCreateOrder]

    @field_serializer("batch_orders", when_used="always")
    @staticmethod
    def serialize_batch(batch_orders: list[QueryCreateOrder]) -> bytes:
        return TypeAdapter(list[QueryCreateOrder]).dump_json(
            batch_orders,
            exclude_none=True,
            by_alias=True,
        )


class DataCreateOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    orders: list[CreatedOrder]


class ResponseCreateOrderList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: DataCreateOrderList

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") not in [0, 80001]:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


def request_create_order_list(
    query: QueryCreateOrderList,
    session: Session | None = None,
) -> Response:
    """
    BEWARE :
    - (BAD) GET LIMIT of 4000 characters: send by batch of 15 max.
    - (GOOD) Accepts multiple symbol at the time.
    - (GOOD) If one failed the order are still created: but data are still sent in `data` field.
    - (GOOD) It truncate automatically the price and quantity when incorrect.
    """

    session = session or build_session()

    url = SWAP_V2_TRADE_BATCH_ORDERS

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


def query_create_order_list(query: QueryCreateOrderList) -> ResponseCreateOrderList:
    """Beware : GET requests with more than 4000 characters are rejected by the API.
    So it is better not send more than 15 order at the time.
    """

    response = request_create_order_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseCreateOrderList.model_validate_json(response.text)

    return endpoint_response


if __name__ == "__main__":
    result = query_create_order_list(
        query=QueryCreateOrderList(
            batch_orders=[
                QueryCreateOrder(
                    quantity=0.0001434,
                    price=60100.0667,
                    side="BUY",
                    symbol="BTC-USDT",
                    type="LIMIT",
                ),
                QueryCreateOrder(
                    quantity=0.001,
                    price=61000,
                    side="BUY",
                    symbol="BTC-USDT",
                    type="LIMIT",
                ),
                QueryCreateOrder(
                    quantity=0.01,
                    price=2800,
                    side="BUY",
                    symbol="ETH-USDT",
                    type="LIMIT",
                ),
            ],
        ),
    )

    print("result:", result)
