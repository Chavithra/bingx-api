from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from requests import Response, Request, Session

from robot_one.api.bingx.future.rest.core import build_session
from robot_one.api.bingx.future.ws.url import SWAP_USER_AUTH_USER_DATA_STREAM

__all__ = [
    "query_update_listen_key",
    "QueryUpdateListenKey",
    "request_update_listen_key",
]


class QueryUpdateListenKey(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    listen_key: str


def request_update_listen_key(
    query: QueryUpdateListenKey,
    session: Session | None = None,
) -> Response:
    """Expires after 60 minutes
    API recommend to send a ping every 30 minutes.
    Returns status code 404 if invalid listen_key.
    Returns status code 200 on success.
    """

    session = session or build_session()

    url = SWAP_USER_AUTH_USER_DATA_STREAM

    params_map = query.model_dump(by_alias=True, exclude_none=True)

    session_request = Request(
        method="PUT",
        params=params_map,
        url=url,
    )
    prepped = session.prepare_request(request=session_request)

    response = session.send(request=prepped)
    response.raise_for_status()

    return response


def query_update_listen_key(
    query: QueryUpdateListenKey,
    session: Session | None = None,
):
    """Expires after 60 minutes."""

    response = request_update_listen_key(query=query, session=session)
    response.raise_for_status()


if __name__ == "__main__":
    order_list = request_update_listen_key(
        query=QueryUpdateListenKey(listen_key="..."),
    )

    print("result:", order_list)
