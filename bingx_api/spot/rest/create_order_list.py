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

from robot_one.api.bingx.spot.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.spot.rest.url import (
    SPOT_V1_TRADE_BATCH_ORDERS,
)
from robot_one.api.bingx.spot.rest.create_order import (
    CreatedOrder,
    SideType,
    OrderType,
    QueryCreateOrder,
)


__all__ = [
    "CreatedOrder",
    "DataCreateOrderList",
    "SideType",
    "OrderType",
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

    data: list[QueryCreateOrder]

    @field_serializer("data", when_used="always")
    @staticmethod
    def serialize_batch(data: list[QueryCreateOrder]) -> bytes:
        return TypeAdapter(list[QueryCreateOrder]).dump_json(
            data,
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
    debug_msg: str
    msg: str
    data: DataCreateOrderList

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
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
    - (BAD) It seems to only accept one symbol at the time otherwise an error 100400 is thrown.
    - (GOOD) If one failed all the order are not created.
    - (GOOD) It truncate automatically the price and quantity when incorrect.
    """

    session = session or build_session()

    url = SPOT_V1_TRADE_BATCH_ORDERS

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


def query_create_order_list(query: QueryCreateOrderList) -> list[CreatedOrder]:
    response = request_create_order_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseCreateOrderList.model_validate_json(response.text)

    return endpoint_response.data.orders


if __name__ == "__main__":
    result = query_create_order_list(
        query=QueryCreateOrderList(
            data=[
                QueryCreateOrder(
                    price=1.134343,
                    quantity=75.701443,
                    side="BUY",
                    symbol="ARB-USDT",
                    type="LIMIT",
                    new_client_order_id="",
                ),
            ],
        ),
    )

    print("result:", result)
