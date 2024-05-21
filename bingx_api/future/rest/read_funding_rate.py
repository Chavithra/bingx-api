from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
)
from robot_one.api.bingx.future.rest.url import (
    SWAP_V2_QUOTE_PREMIUM_INDEX,
    SWAP_V2_QUOTE_FUNDING_RATE,
)


class PreniumIndex(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    mark_price: float
    index_price: float
    last_funding_rate: float
    next_funding_time: float


class FundingRate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    funding_rate: float
    funding_time: float


class PreniumIndexResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: PreniumIndex


class FundingRateResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: int
    msg: str
    data: list[FundingRate]


class QueryPreniumIndex(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    recv_window: int | None = Field(default=None)


class QueryFundingRate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    start_time: int
    end_time: int | None = Field(default=None)
    limit: int = Field(default=1000)
    recv_window: int | None = Field(default=None)


def request_current_funding_rate(
    query: QueryPreniumIndex,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_QUOTE_PREMIUM_INDEX

    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="GET",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)

    print(prepped.url)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def fetch_current_funding_rate(query: QueryPreniumIndex) -> PreniumIndex:
    response = request_current_funding_rate(query=query)
    response.raise_for_status()
    endpoint_response = PreniumIndexResponse.model_validate_json(response.text)

    return endpoint_response.data


def request_funding_rate_history(
    query: QueryFundingRate,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_V2_QUOTE_FUNDING_RATE

    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="GET",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)
    # prepped = get_signed_request(prepared_request=prepped)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def query_funding_rate_history(query: QueryFundingRate) -> list[FundingRate]:
    response = request_funding_rate_history(query=query)
    response.raise_for_status()
    endpoint_response = FundingRateResponse.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    current_funding_rate = fetch_current_funding_rate(
        query=QueryPreniumIndex(
            symbol="BTC-USDT",
        ),
    )
    funding_rate_history = query_funding_rate_history(
        query=QueryFundingRate(
            limit=0,
            end_time=int(datetime.now().timestamp() * 1000),
            start_time=int(datetime.now().timestamp() * 1000) - 3 * 3600 * 1000,
            symbol="BTC-USDT",
        ),
    )

    print("result:", current_funding_rate)
    print("result:", funding_rate_history)
