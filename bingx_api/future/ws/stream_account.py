from enum import Enum
from logging import getLogger, Logger
from queue import SimpleQueue
from threading import Event
from typing import Literal

from orjson import loads
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from websockets.exceptions import ConnectionClosed

from robot_one.api.bingx.future.ws.model.base_streamer import (
    BaseProducer,
    BaseStreamer,
)
from robot_one.api.bingx.future.ws.valid_listen_key import ValidListenKey
from robot_one.api.bingx.future.ws.stream_channel import (
    ProducerChannel,
    StreamerChannel,
    QueryChannel,
)

__all__ = (
    "AccountUpdate",
    "BalanceInformation",
    "EventType",
    "OrderUpdate",
    "ResponseAccountUpdate",
    "ResponseConfigUpdate",
    "ResponseData",
    "ResponseOrderTradeUpdate",
    "StreamerAccount",
    "TradeInformation",
)

SideType = Literal["BUY", "SELL"]
StatusType = Literal[
    "CANCELED",
    "CANCELLED",
    "EXPIRED",
    "FAILED",
    "FILLED",
    "NEW",
    "PARTIALLY_FILLED",
    "PENDING",
    "WORKING",
]
OrderType = Literal[
    "LIMIT",
    "LIQUIDATION",
    "MARKET",
    "STOP",
    "TAKE_PROFIT",
]


class BalanceInformation(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    a: str | None = Field(default=None, description="Asset name, e.g.: USDT.")
    bc: float | None = Field(
        default=None, description="Wallet balance change amount, e.g.: 0."
    )
    cw: float | None = Field(
        default=None,
        description="Wallet balance excluding isolated margin, e.g.: 5233.21709203",
    )
    wb: float | None = Field(
        default=None, description="Wallet balance, e.g.: 5277.59264687."
    )


class TradeInformation(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    ep: float | None = Field(default=None, description="Entry price, e.g.: 7.25620000.")
    iw: float | None = Field(
        default=None,
        description="If it is an isolated position, the position margin, e.g.: 23.19081642.",
    )
    mt: float | None = Field(default=None, description="Margin mode, e.g.: isolated.")
    pa: float | None = Field(default=None, description="Position, e.g.: 108.84300000.")
    ps: str | None = Field(default=None, description="Position direction, e.g.: SHORT.")
    s: str | None = Field(default=None, description="Trading pair, e.g.: LINK-USDT.")
    up: float | None = Field(
        default=None,
        description="Unrealized profit and loss of positions, e.g.: 1.42220000.",
    )


class AccountUpdate(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    m: str | None = Field(default=None, description="Event launch reason")
    B: list[dict] | None = Field(default=None, description="Balance information.")
    P: list[dict] | None = Field(default=None, description="Trade information.")


class EventType(str, Enum):
    ACCOUNT_CONFIG_UPDATE = "ACCOUNT_CONFIG_UPDATE"
    ACCOUNT_UPDATE = "ACCOUNT_UPDATE"
    ORDER_TRADE_UPDATE = "ORDER_TRADE_UPDATE"


class ResponseAccountUpdate(BaseModel):
    """
    Example:
    {
        "e": "ACCOUNT_UPDATE",
        "E": 1711119788960,
        "a": {
            "m": "ORDER",
            "B": [
                {
                    "a": "USDT",
                    "wb": "14440.10668834",
                    "cw": "10025.54321642",
                    "bc": "0"
                }
            ],
            "P": [
                {
                    "s": "BTC-USDT",
                    "pa": "0.30040000",
                    "ep": "64638.76890401",
                    "up": "-518.82880805",
                    "mt": "isolated",
                    "iw": "3580.20413912",
                    "ps": "LONG"
                }
            ]
        }
    }
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    e: Literal[EventType.ACCOUNT_UPDATE]

    E: int | None = Field(default=None, description="Event time.")
    T: int | None = Field(default=None, description="Event time.?")
    a: AccountUpdate | None = Field(default=None, description="Account data.")


class ResponseConfigUpdate(BaseModel):
    """
    Example:
    {
        "e": "ACCOUNT_CONFIG_UPDATE",
        "E": 1710664430174,
        "ac": {"s": "DGB-USDT", "l": 20, "S": 20, "mt": "isolated"},
    }
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    e: Literal[EventType.ACCOUNT_CONFIG_UPDATE]

    c: float = Field(default=None, description="Latest transaction price.")
    E: int = Field(description="Event time.")
    s: str = Field(default=None, description="Trading pair, e.g., BTC-USDT.")


class OrderUpdate(BaseModel):
    """
    Looks like the "PENDING" status is only on the REST API.
    Althought this option is not documented in the REST API documentation.
    It is an option of `X` here to WS and REST models compatible.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    ap: float | None = Field(default=None, description="Order average price.")
    c: str = Field(default="", description="Client custom order ID.")
    i: int = Field(default=None, description="Order ID.")
    n: float | None = Field(default=None, description="Handling fee.")
    N: str | None = Field(default=None, description="Fee asset type.")
    o: OrderType = Field(description="Order type.")
    p: float = Field(description="Order price.")
    ps: str = Field(description="Position direction.")
    q: float = Field(description="Order quantity.")
    rp: float | None = Field(
        default=None, description="The transaction achieves profit and loss."
    )
    S: SideType = Field(description="Order direction.")
    s: str = Field(description="Trading pair.")
    sp: float | None = Field(default=None, description="Trigger price.")
    T: int | None = Field(default=None, description="Transaction time.")
    wt: str | None = Field(default=None, description="Trigger price type.")
    X: StatusType = Field(description="Current status of the order.")
    x: str | None = Field(
        default=None, description="Specific execution type of this event."
    )
    z: float | None = Field(
        default=None, description="Order Filled Accumulated Quantity."
    )


class ResponseOrderTradeUpdate(BaseModel):
    """
        Example:
        {
            "e": "ORDER_TRADE_UPDATE",
            "E": 1710664488898,
            "o": {
                "s": "XRP-USDT",
                "c": "",
                "i": 1769281218845814784,
                "S": "SELL",
                "o": "LIMIT",
                "q": "80.00000000",
                "p": "0.61670000",
                "sp": "0.00000000",
                "ap": "0.00000000",
                "x": "TRADE",
                "X": "NEW",
                "N": "USDT",
                "n": "0.00000000",
                "T": 0,
                "wt": "MARK_PRICE",
                "ps": "SHORT",
                "rp": "0.00000000",
                "z": "0.00000000",
                "sg": "false",
            },
        }

        {
        "e": "ORDER_TRADE_UPDATE",
        "E": 1711119124890,
        "o": {
            "s": "BTC-USDT",
            "c": "",
            "i": 1771187887368515584,
            "S": "BUY",
            "o": "LIMIT",
            "q": "0.00080000",
            "p": "62824.30000000",
            "sp": "0.00000000",
            "ap": "62824.30000000",
            "x": "TRADE",
            "X": "FILLED",
            "N": "USDT",
            "n": "-0.01005189",
            "T": 0,
            "wt": "MARK_PRICE",
            "ps": "LONG",
            "rp": "0.00000000",
            "z": "0.00080000",
            "sg": "false"
        }
    }
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    e: Literal[EventType.ORDER_TRADE_UPDATE]

    s: str = Field(default=None, description="Trading pair, e.g., BTC-USDT.")
    E: int = Field(description="Event time.")
    o: OrderUpdate = Field(default=None, description="Order description.")


Data = ResponseAccountUpdate | ResponseConfigUpdate | ResponseOrderTradeUpdate


class ResponseData(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    data: Data = Field(description="Event type.", discriminator="e")


class ResponseListenKey(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    listen_key: str


class ProducerAccount(BaseProducer):
    def __init__(
        self,
        *args,
        catch_exception: bool = True,
        listen_key: ValidListenKey | None = None,
        logger: Logger | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._catch_exception = catch_exception
        self._logger = logger or getLogger(name=__name__)
        self._listen_key = listen_key or ValidListenKey()

        self._event_crash = Event()
        self._event_stop = Event()
        self._queue_iterator = SimpleQueue[ResponseData]()
        self._subscription_queue = SimpleQueue[QueryChannel]()

    @property
    def catch_exception(self) -> bool:
        return self._catch_exception

    @property
    def listen_key(self) -> ValidListenKey:
        return self._listen_key

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def queue_iterator(self) -> SimpleQueue[ResponseData]:
        return self._queue_iterator

    @property
    def event_crash(self) -> Event:
        return self._event_crash

    @property
    def event_stop(self) -> Event:
        return self._event_stop

    @property
    def subscription_queue(self) -> SimpleQueue[QueryChannel]:
        return self.subscription_queue

    def run(self):
        catch_exception = self._catch_exception
        logger = self._logger
        listen_key = self._listen_key
        queue_iterator = self._queue_iterator
        event_crash = self._event_crash
        event_stop = self._event_stop

        while not event_stop.is_set():
            try:
                with listen_key as refreshed_listen_key:
                    streamer_channel = StreamerChannel(
                        producer=ProducerChannel(
                            catch_exception=catch_exception,
                            listen_key=refreshed_listen_key,
                        ),
                    )

                    with streamer_channel as channel_stream:
                        logger.debug("<ACCOUNT_READER>:START_READING")

                        for message in channel_stream:
                            if event_stop.is_set():
                                logger.debug("<ACCOUNT_READER>:STOP_READING")
                                break

                            message_obj = loads(message)
                            response_update = ResponseData(data=message_obj)

                            logger.debug(
                                "<ACCOUNT_READER>:READ:RESPONSE_UPDATE:%s",
                                response_update,
                            )
                            queue_iterator.put_nowait(response_update)
            except ConnectionClosed as e:
                if not catch_exception:
                    raise e

                event_crash.set()
                logger.fatal("<ACCOUNT_READER>:%s", e)


StreamerAccount = BaseStreamer[ProducerAccount, ResponseData]

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.FATAL)

    streamer = StreamerAccount(producer=ProducerAccount())

    try:
        for _response_data in streamer:
            print(_response_data)
    except KeyboardInterrupt:
        print("Closing the websocket connection.")
