from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_TRADE_ORDER


class DeletedOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    symbol: str | None = Field(default=None)
    price: float | None = Field(default=None)
    time: int | None = Field(default=None)


class ResponseDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: DeletedOrder

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryDeleteOrder(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    client_order_id: str | None = Field(default=None)
    order_id: str | None = Field(default=None)
    recv_window: int | None = Field(default=None)
    symbol: str


def request_delete_order(
    query: QueryDeleteOrder,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_ORDER

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


def query_order(query: QueryDeleteOrder) -> DeletedOrder:
    response = request_delete_order(query=query)
    response.raise_for_status()
    endpoint_response = ResponseDeleteOrder.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    result = request_delete_order(
        query=QueryDeleteOrder(
            order_id="1771652526917234688",
            symbol="ETH-USDT",
        ),
    )

    print("result:", result)
