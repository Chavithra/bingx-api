from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
)
from robot_one.api.bingx.spot.rest.url import SPOT_V1_COMMON_SYMBOLS

__all__ = [
    "Contract",
    "ContractListData",
    "ResponseContractList",
    "QueryContractList",
    "request_contract_list",
    "query_contract_list",
]

class Contract(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    api_state_buy: bool
    api_state_sell: bool
    max_notional: float
    max_qty: float
    min_notional: float
    min_qty: float
    status: int
    step_size: float
    symbol: str
    tick_size: float
    time_online: int


class ContractListData(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    symbols: list[Contract]


class ResponseContractList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    msg: str
    debugMsg: str
    data: ContractListData

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class QueryContractList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    recvWindow: int = Field(default=0)


def request_contract_list(
    query: QueryContractList | None = None,
    session: Session | None = None,
) -> Response:
    query = query or QueryContractList()
    session = session or build_session()

    url = SPOT_V1_COMMON_SYMBOLS
    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="GET",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)

    print(prepped.method, prepped.url)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def query_contract_list(query: QueryContractList | None = None) -> list[Contract]:
    response = request_contract_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseContractList.model_validate_json(response.text)

    return endpoint_response.data.symbols


if __name__ == "__main__":
    contract_list = query_contract_list()

    for contract in contract_list:
        print(contract)
