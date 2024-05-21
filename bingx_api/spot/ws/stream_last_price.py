from logging import getLogger, Logger
from queue import SimpleQueue
from threading import Event
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from robot_one.api.bingx.spot.ws.model.base_streamer import (
    BaseProducer,
    BaseStreamer,
)
from robot_one.api.bingx.spot.ws.stream_channel import (
    ProducerChannel,
    StreamerChannel,
    Subscription,
)

__all__ = (
    "LastPrice",
    "ProducerLastPrice",
    "StreamerLastPrice",
    "ResponseLastPrice",
)

SymbolType = str



class LastPrice(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    e: str = Field(description="Event type.")
    s: str = Field(description="Trading pair, e.g., BTC-USDT.")
    c: float = Field(description="Latest transaction price.")


class ResponseLastPrice(BaseModel):
    """For data_type = `<symbol>@lastPrice`

    Example:
    {
        "code": 0,
        "dataType": "FLOKI-USDT@lastPrice",
        "data": {
            "e": "lastPriceUpdate",
            "E": 1710351327012,
            "s": "FLOKI-USDT",
            "c": "0.00026882",
        },
    }
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    code: float
    data_type: str
    data: LastPrice

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_code(cls, data: Any) -> Any:
        if data.get("code") != 0:
            raise ValueError(
                "code: " + str(data.get("code")) + "; msg: " + data.get("msg")
            )

        return data


class ProducerLastPrice(BaseProducer):
    @staticmethod
    def build_subscription_list(symbol_list: list[str]) -> list[Subscription]:
        subscription_list = [
            Subscription(id="0", data_type=f"{symbol}@lastPrice")
            for symbol in symbol_list
        ]

        return subscription_list

    @staticmethod
    def parse_symbol_list(subscription_list: list[Subscription]) -> list[SymbolType]:
        symbol_list = []
        suffix_length = len("@lastPrice")

        for subscription in subscription_list:
            if subscription.data_type.endswith("@lastPrice"):
                symbol_list.append(subscription.data_type[:-suffix_length])

        return symbol_list

    def __init__(
        self,
        *args,
        logger: Logger | None = None,
        symbol_list: list[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        event_stop = Event()
        logger = logger or getLogger(name=self.__class__.__name__)
        queue_iterator = SimpleQueue[LastPrice]()
        streamer_channel = StreamerChannel(
            producer=ProducerChannel(
                subscription_list=self.build_subscription_list(
                    symbol_list=symbol_list or [],
                ),
            ),
        )

        self._event_stop = event_stop
        self._logger = logger
        self._queue_iterator = queue_iterator
        self._streamer_channel = streamer_channel

    @property
    def streamer_channel(self) -> StreamerChannel:
        return self._streamer_channel

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def event_stop(self) -> Event:
        return self._event_stop

    @property
    def queue_iterator(self) -> SimpleQueue[LastPrice]:
        return self._queue_iterator

    def run(self) -> None:
        event_stop = self._event_stop
        logger = self._logger
        queue_iterator = self._queue_iterator
        streamer_channel = self._streamer_channel

        for message in streamer_channel:
            logger.debug("<STREAMER_CHANNEL>:NEW_MESSAGE:%s>", message)

            if event_stop.is_set():
                logger.debug("<STREAMER_CHANNEL>:STOP_READING")
                break

            last_price = ResponseLastPrice.model_validate_json(json_data=message).data

            logger.debug("LAST_PRICE:%s", last_price)

            queue_iterator.put_nowait(item=last_price)

    @property
    def symbol_list(self) -> list[SymbolType]:
        subscription_list = self._streamer_channel.producer.subscription_list
        symbol_list = self.parse_symbol_list(subscription_list=subscription_list)
        return symbol_list

    @symbol_list.setter
    def symbol_list(self, symbol_list: list[SymbolType]) -> None:
        producer_channel = self._streamer_channel.producer
        expected_list = self.build_subscription_list(symbol_list=symbol_list)
        producer_channel.subscribe(expected_list=expected_list)


StreamerLastPrice = BaseStreamer[ProducerLastPrice, LastPrice]


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    streamer = StreamerLastPrice(
        producer=ProducerLastPrice(
            symbol_list=[
                "BTC-USDT",
                "ETH-USDT",
                "SOL-USDT",
                # "AVAX-USDT",
                # "ANKR-USDT",
                # "ADA-USDT",
                # "WIF-USDT",
                # "SHIB-USDT",
                # "RNDR-USDT",
                # "FET-USDT",
                # "XRP-USDT",
            ],
        ),
    )

    try:
        for received_message in streamer:
            print(received_message)
    except KeyboardInterrupt:
        print("Closing the websocket connection.")
