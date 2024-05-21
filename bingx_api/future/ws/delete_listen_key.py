from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from requests import Response, Request, Session

from robot_one.api.bingx.future.rest.core import build_session
from robot_one.api.bingx.future.ws.url import SWAP_USER_AUTH_USER_DATA_STREAM


class QueryDeleteListenKey(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    listen_key: str


def request_delete_listen_key(
    query: QueryDeleteListenKey,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_USER_AUTH_USER_DATA_STREAM

    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="DELETE",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


if __name__ == "__main__":
    order_list = request_delete_listen_key(
        query=QueryDeleteListenKey(listen_key="..."),
    )

    print("result:", order_list)
