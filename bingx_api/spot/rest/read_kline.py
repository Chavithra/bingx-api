from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from requests import Request, Response, Session

from robot_one.api.bingx.future.rest.core import (
    build_session,
)
from robot_one.api.bingx.spot.rest.url import SPOT_V2_MARKET_KLINE

__all__ = [
    "get_specific_unix_timestamp_ms",
    "get_unix_timestamp_ms",
    "Interval",
    "KLineEntry",
    "query_kline",
    "QueryKLine",
    "request_kline",
    "ResponseKline",
]


def get_unix_timestamp_ms(minus_delta: timedelta | None = None) -> int:
    minus_delta = minus_delta or timedelta()
    return int((datetime.now() - minus_delta).timestamp() * 1000)


def get_specific_unix_timestamp_ms(specific_time: datetime | None = None) -> int:
    specific_time = specific_time or datetime.now()
    return int(specific_time.now().timestamp() * 1000)


class Interval(str, Enum):
    MINUTES_1 = "1m"
    MINUTES_3 = "3m"
    MINUTES_5 = "5m"
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    HOURS_1 = "1h"
    HOURS_2 = "2h"
    HOURS_4 = "4h"
    HOURS_6 = "6h"
    HOURS_8 = "8h"
    HOURS_12 = "12h"
    DAYS_1 = "1d"
    DAYS_3 = "3d"
    WEEKS_1 = "1w"
    MONTHS_1 = "1M"

    def to_timedelta(self) -> timedelta:
        conversion = {
            "m": timedelta(minutes=1),
            "h": timedelta(hours=1),
            "d": timedelta(days=1),
            "w": timedelta(weeks=1),
            "M": timedelta(days=30),  # Approximation for a month
        }
        value = self.value
        unit = value[-1]
        number = int(value[:-1])
        return conversion[unit] * number


class KLineEntry(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    close: float = Field(description="Close price")
    high: float = Field(description="Max. price")
    low: float = Field(description="Min. price")
    open: float = Field(description="Open price")
    open_time: int = Field(description="Candlestick chart open time")
    time: int = Field(description="Candlestick chart close time")
    filled_price: float = Field(description="Filled price")
    volume: float = Field(description="Volume")


class ResponseKline(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )

    code: int
    timestamp: int
    data: list[KLineEntry] = Field(default_factory=list)

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, data: list[KLineEntry]) -> list[KLineEntry]:
        kline_entry_list = []
        if data and isinstance(data, list):
            for entry in data:
                if isinstance(entry, list) and len(entry) == 8:
                    kline_entry = KLineEntry(
                        open_time=entry[0],
                        open=entry[1],
                        high=entry[2],
                        low=entry[3],
                        close=entry[4],
                        filled_price=entry[5],
                        time=entry[6],
                        volume=entry[7],
                    )
                    kline_entry_list.append(kline_entry)
                else:
                    raise ValueError(f"Invalid entry, len(entry) != 8: {entry}")
        return kline_entry_list


class QueryKLine(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    symbol: str
    interval: str | Interval = Field(default=Interval.HOURS_1)
    start_time: int | None = Field(default=None)
    end_time: int | None = Field(default=None)
    limit: int = Field(default=1000)
    recv_window: int | None = Field(default=None)


def request_kline(
    query: QueryKLine,
    session: Session | None = None,
) -> Response:
    session = session or build_session()

    url = SPOT_V2_MARKET_KLINE
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


def query_kline(query: QueryKLine) -> list[KLineEntry]:
    response = request_kline(query=query)
    response.raise_for_status()
    endpoint_response = ResponseKline.model_validate_json(response.text)

    return endpoint_response.data


if __name__ == "__main__":
    result = query_kline(
        query=QueryKLine(
            # end_time=int(datetime.now().timestamp() * 1000),
            interval=Interval.MINUTES_15,
            # limit=10,
            start_time=int(datetime.now().timestamp() * 1000) - 20 * 3600 * 1000,
            symbol="BTC-USDT",
        ),
    )

    print("result:", result)
