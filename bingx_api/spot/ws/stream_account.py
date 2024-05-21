from logging import getLogger, Logger
from queue import SimpleQueue
from threading import Event
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from robot_one.api.bingx.spot.ws.model.base_streamer import (
    BaseProducer,
    BaseStreamer,
)
from robot_one.api.bingx.spot.ws.valid_listen_key import ValidListenKey
from robot_one.api.bingx.spot.ws.stream_channel import (
    ProducerChannel,
    StreamerChannel,
    Subscription,
)

__all__ = (
    "OrderUpdate",
    "ProducerAccount",
    "ResponseData",
    "StreamerAccount",
    "ValidListenKey",
)

EventType = Literal["executionReport"]
DataType = Literal["spot.executionReport"]
OrderType = Literal[
    "MARKET",
    "LIMIT",
    "TAKE_STOP_LIMIT",
    "TAKE_STOP_MARKET",
    "TRIGGER_LIMIT",
    "TRIGGER_MARKET",
]
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


class OrderUpdate(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        frozen=True,
        populate_by_name=True,
    )

    C: str | None = Field(default=None, description="Client order id")
    E: int = Field(description="Event time")
    e: Literal["executionReport"] = Field(description="Event Type")
    i: int = Field(description="Order ID")
    l: float = Field(description="Last order transaction volume")
    L: float = Field(description="Last transaction price of the order")
    m: bool = Field(description="Original order amount")
    n: float = Field(description="Number of handling fees")
    N: str = Field(description="Handling fee asset category")
    O: int = Field(description="Order creation time")
    o: OrderType
    p: float = Field(description="Original order price")
    Q: float = Field(description="Last transaction amount of the order")
    q: float = Field(description="Order original quantity")
    S: SideType
    s: str = Field(description="Trading pair")
    t: float = Field(description="Transaction ID")
    T: int = Field(description="Transaction time")
    X: StatusType = Field(description="Order status")
    x: str = Field(description="?", examples=["CANCELED"])
    Y: float = Field(description="Accumulated transaction amount of orders")
    Z: float = Field(description="?", examples=[0])
    z: float = Field(description="Accumulated transaction volume of orders")


class ResponseData(BaseModel):
    """
    Example:
    {
        "code": 0,
        "dataType": "spot.executionReport",
        "data": {
            "e": "executionReport",
            "E": 1712620300043,
            "s": "CKB-USDT",
            "S": "BUY",
            "o": "LIMIT",
            "q": 228,
            "p": 0.021851,
            "x": "CANCELED",
            "X": "CANCELED",
            "i": 1777483570864881664,
            "l": 0,
            "z": 0,
            "L": 0,
            "n": 0,
            "N": "",
            "T": 0,
            "t": 0,
            "O": 1712620082103,
            "Z": 0,
            "Y": 0,
            "Q": 5,
            "m": false,
        },
    }
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="ignore",
        frozen=True,
    )

    code: int | None = Field(default=None)
    data_type: Literal["spot.executionReport"] = Field(description="Event type.")
    data: OrderUpdate = Field(discriminator="e")


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
        logger: Logger | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._catch_exception = catch_exception
        self._logger = logger or getLogger(name=__name__)

        self._event_crash = Event()
        self._event_stop = Event()
        self._queue_iterator = SimpleQueue[ResponseData]()

    @property
    def catch_exception(self) -> bool:
        return self._catch_exception

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

    def run(self):
        catch_exception = self._catch_exception
        logger = self._logger
        queue_iterator = self._queue_iterator
        event_crash = self._event_crash
        event_stop = self._event_stop

        while not event_stop.is_set():
            try:
                listen_key = ValidListenKey()

                with listen_key as refreshed_listen_key:
                    streamer_channel = StreamerChannel(
                        producer=ProducerChannel(
                            catch_exception=False,
                            listen_key=refreshed_listen_key,
                            subscription_list=[
                                Subscription(
                                    id="0",
                                    data_type="spot.executionReport",
                                )
                            ],
                        ),
                    )

                    with streamer_channel as channel_stream:
                        logger.debug("<ACCOUNT_READER>:START_READING")

                        for message in channel_stream:
                            if event_stop.is_set():
                                logger.debug("<ACCOUNT_READER>:STOP_READING")
                                break

                            response_update = ResponseData.model_validate_json(
                                json_data=message
                            )

                            logger.debug(
                                "<ACCOUNT_READER>:READ:RESPONSE_UPDATE:%s",
                                response_update,
                            )
                            queue_iterator.put_nowait(response_update)
            except Exception as e:
                if not catch_exception:
                    raise e

                event_crash.set()
                logger.fatal("<ACCOUNT_READER>:%s", e)


StreamerAccount = BaseStreamer[ProducerAccount, ResponseData]

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)

    streamer = StreamerAccount(producer=ProducerAccount())

    try:
        for _response_data in streamer:
            print(_response_data)
    except KeyboardInterrupt:
        print("Closing the websocket connection.")
