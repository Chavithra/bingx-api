from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_USER_COMMISSION_RATE


class CommissionRate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    taker_commission_rate: float
    maker_commission_rate: float


class Data(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    commission: CommissionRate


class EndpointResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    msg: str
    data: Data


class QueryCommissionRate(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    recvWindow: int = Field(default=0)


def request_commission_rate(
    query: QueryCommissionRate | None = None,
    session: Session | None = None,
) -> Response:
    query = query or QueryCommissionRate()
    session = session or build_session()

    url = SWAP_V2_USER_COMMISSION_RATE
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


def query_commission_rate(query: QueryCommissionRate | None = None) -> CommissionRate:
    response = request_commission_rate(query=query)
    response.raise_for_status()
    endpoint_response = EndpointResponse.model_validate_json(response.text)

    return endpoint_response.data.commission


if __name__ == "__main__":
    order_list = query_commission_rate()

    print("result:", order_list)
