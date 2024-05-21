from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from requests import Response, Request, Session

from robot_one.api.bingx.future.rest.core import get_signed_request, build_session
from robot_one.api.bingx.api_config import build_api_config
from robot_one.api.bingx.future.ws.url import SWAP_USER_AUTH_USER_DATA_STREAM

API_CONFIG = build_api_config()

__all__ = [
    "query_listen_key",
    "request_listen_key",
    "ResponseListenKey",
]


class ResponseListenKey(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    listen_key: str


def request_listen_key(
    api_key: str = API_CONFIG.API_KEY,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SWAP_USER_AUTH_USER_DATA_STREAM

    params_map = {
        "X-BX-APIKEY": api_key,
    }

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


def query_listen_key(session: Session | None = None) -> str:
    """Expires after 60 minutes."""
    response = request_listen_key(session=session)
    response.raise_for_status()
    endpoint_response = ResponseListenKey.model_validate_json(response.text)

    return endpoint_response.listen_key
