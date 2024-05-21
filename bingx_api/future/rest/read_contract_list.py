import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
    get_signed_request,
)
from robot_one.api.bingx.future.rest.url import SWAP_V2_QUOTE_CONTRACTS


class Contract(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    api_state_close: str
    api_state_open: str
    asset: str
    contract_id: int
    currency: str
    fee_rate: float
    price_precision: int
    quantity_precision: int
    size: float
    status: int
    symbol: str
    trade_min_limit: int


class ResponseContractList(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    msg: str
    data: list[Contract]

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

    url = SWAP_V2_QUOTE_CONTRACTS
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


def query_contract_list(query: QueryContractList | None = None) -> list[Contract]:
    response = request_contract_list(query=query)
    response.raise_for_status()
    endpoint_response = ResponseContractList.model_validate_json(response.text)

    return endpoint_response.data


def read_contract_list_from_file() -> dict:
    path = Path(
        "/home/chavithra/code/python/robot/robot_one/payload/bingx/rest/swap_v1_quote_all_contracts.json"
    )

    contract = {}
    with path.open(mode="r") as f:
        contract = json.load(f)["data"]["contracts"]

    return contract


if __name__ == "__main__":
    contract_list = query_contract_list()

    print("result:", contract_list)
