from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V1_TICKER_PRICE


class LastPrice(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    price: float
    time: int


class ResponseLastPrice(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: LastPrice

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryLastPrice(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    recv_window: int | None = Field(default=None)


def request_last_price(
    query: QueryLastPrice,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V1_TICKER_PRICE

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


def query_last_price(query: QueryLastPrice) -> LastPrice:
    response = request_last_price(query=query)
    response.raise_for_status()
    endpoint_response = ResponseLastPrice.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    result = query_last_price(
        query=QueryLastPrice(
            symbol="BTC-USDT",
        ),
    )

    print("result:", result)
