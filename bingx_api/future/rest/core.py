import hmac
from datetime import datetime
from hashlib import sha256
from urllib.parse import unquote

from requests import PreparedRequest, Session

from robot_one.api.bingx.api_config import build_api_config

API_CONFIG = build_api_config()


def build_session(
    headers: dict | None = None,
    hooks: dict | None = None,
) -> Session:
    """Setup a "requests.Session" object.
    Args:
        headers (dict, optional):
            Headers to used for the Session.
            Defaults to None.
        hooks (dict, optional):
            Hooks for the Session.
            Defaults to None.

    Returns:
        requests.Session:
            Session object with the right headers and hooks.
    """

    session = Session()

    if isinstance(headers, dict):
        session.headers.update(headers)

    if isinstance(hooks, dict):
        session.hooks.update(hooks)

    return session


def get_signature(query_string: str) -> str:
    signature = hmac.new(
        key=API_CONFIG.API_SECRET.encode("utf-8"),
        msg=query_string.encode("utf-8"),
        digestmod=sha256,
    ).hexdigest()
    return signature


def get_timestamp() -> int:
    return int(datetime.now().timestamp() * 1000)


def get_signed_request(
    prepared_request: PreparedRequest,
    api_key: str = API_CONFIG.API_KEY,
) -> PreparedRequest:
    if prepared_request.url is None:
        raise AttributeError("No URL provided.")

    prepared_request.prepare_headers({"X-BX-APIKEY": api_key})

    timestamp = get_timestamp()
    prepared_request.prepare_url(
        url=prepared_request.url,
        params={"timestamp": timestamp},
    )

    query_string = unquote(prepared_request.url.split("?")[1])

    signature = get_signature(query_string=query_string)
    prepared_request.prepare_url(
        url=prepared_request.url,
        params={"signature": signature},
    )

    print(prepared_request.method, len(prepared_request.url), prepared_request.url)

    return prepared_request
