from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_TRADE_LEVERAGE


class Leverage(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    long_leverage: int
    max_long_leverage: int
    max_short_leverage: int
    short_leverage: int
    short_leverage: int


class ResponseLeverage(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    msg: str
    data: Leverage

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryLeverage(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    recvWindow: int = Field(default=0)


def request_leverage(
    query: QueryLeverage,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_TRADE_LEVERAGE
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


def query_leverage(query: QueryLeverage) -> Leverage:
    response = request_leverage(query=query)
    response.raise_for_status()
    endpoint_response = ResponseLeverage.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    leverage = query_leverage(query=QueryLeverage(symbol="BTC-USDT"))

    print("result:", leverage)
