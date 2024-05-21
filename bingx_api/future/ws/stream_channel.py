import gzip
from logging import getLogger, Logger
from queue import SimpleQueue
from re import match
from threading import Event

from pydantic import BaseModel, Field
from websockets.exceptions import ConnectionClosed
from websockets.sync import client
from websockets.sync.connection import Connection

from robot_one.adapter.core.abstract.locked_obj import LockedObj
from robot_one.api.bingx.future.ws.model.base_streamer import (
    BaseProducer,
    BaseStreamer,
)
from robot_one.api.bingx.future.ws.model.query_channel import (
    QueryChannel,
    ReqType,
)
from robot_one.api.bingx.future.ws.url import SWAP_MARKET
from robot_one.api.bingx.future.ws.valid_listen_key import ValidListenKey

__all__ = (
    "QUERY_CHANNEL_LIST_EXAMPLE",
    "StreamerChannel",
    "Subscription",
)

DataType = str
IdType = str
QUERY_CHANNEL_LIST_EXAMPLE = [
    QueryChannel(
        id="id1",
        req_type=ReqType.SUB,
        data_type="BTC-USDT@lastPrice",
    ),
    QueryChannel(
        id="id2",
        req_type=ReqType.SUB,
        data_type="FLOKI-USDT@lastPrice",
    ),
]


class Subscription(BaseModel):
    id: str = Field(description="An identifier that service will send back.")
    data_type: str = Field(
        description="Subscribed data type, e.g., BTC-USDT@lastPrice",
    )

    def __hash__(self):
        return hash((self.id, self.data_type))


class ProducerChannel(BaseProducer):
    @staticmethod
    def build_query_channel_list_diff(
        current_list: list[Subscription],
        expected_list: list[Subscription],
    ) -> list[QueryChannel]:
        current_set = set(current_list)
        expected_set = set(expected_list)

        to_sub_set = expected_set - current_set
        sub_list = [
            QueryChannel(id=q.id, req_type=ReqType.SUB, data_type=q.data_type)
            for q in to_sub_set
        ]

        to_unsub_set = current_set - expected_set
        unsub_list = [
            QueryChannel(id=q.id, req_type=ReqType.UNSUB, data_type=q.data_type)
            for q in to_unsub_set
        ]

        return sub_list + unsub_list

    @staticmethod
    def build_query_channel_list(
        subscription_list: list[Subscription],
    ) -> list[QueryChannel]:
        sub_list = [
            QueryChannel(id=q.id, req_type=ReqType.SUB, data_type=q.data_type)
            for q in subscription_list
        ]

        return sub_list

    @staticmethod
    def send_query_channel_list(
        query_channel_list: list[QueryChannel],
        websocket: Connection,
        logger: Logger | None = None,
    ) -> None:
        logger = logger or getLogger(__name__)

        for query_channel in query_channel_list:
            query_channel_json = query_channel.model_dump_json(
                exclude_none=True,
                by_alias=True,
            )
            websocket.send(message=query_channel_json)

            logger.debug("<BINGX:WS>:SUBSCRIBING:CHANNEL:%s", query_channel)

    @staticmethod
    def is_ping(message: bytes) -> bool:
        return message == b"Ping"

    @staticmethod
    def is_subscription_confirmation(message: bytes) -> bool:
        pattern = r"""\{"id":"[^"]*","code":0,"msg":"","dataType":"","data":null\}"""

        return bool(match(pattern=pattern, string=message.decode(encoding="utf-8")))

    @staticmethod
    def is_error(message: bytes) -> bool:
        return not (message.find(b'"code":0') > 0 or message.startswith(b'{"e":"'))

    @staticmethod
    def decompress(data: str | bytes) -> bytes:
        if isinstance(data, bytes):
            decompressed_data = gzip.decompress(data)
        elif isinstance(data, str):
            decompressed_data = gzip.decompress(data.encode("utf-8"))

        return decompressed_data

    def __init__(
        self,
        *args,
        catch_exception: bool = True,
        listen_key: ValidListenKey | None = None,
        logger: Logger | None = None,
        max_connection_retry: int = 3,
        subscription_list: list[Subscription] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        event_stop = Event()
        locked_subscription_list = LockedObj[list[Subscription]](
            obj=subscription_list or [],
        )
        logger = logger or getLogger(name=self.__class__.__name__)
        queue_iterator = SimpleQueue[bytes]()
        websocket = None

        self._catch_exception = catch_exception
        self._event_stop = event_stop
        self._listen_key = listen_key
        self._locked_subscription_list = locked_subscription_list
        self._logger = logger
        self._max_connection_retry = max_connection_retry
        self._queue_iterator = queue_iterator
        self._websocket = websocket

    @property
    def catch_exception(self) -> bool:
        return self._catch_exception

    @property
    def event_stop(self) -> Event:
        return self._event_stop

    @property
    def queue_iterator(self) -> SimpleQueue[bytes]:
        return self._queue_iterator

    @property
    def listen_key(self) -> ValidListenKey | None:
        return self._listen_key

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def max_connection_retry(self) -> int:
        return self._max_connection_retry

    @property
    def subscription_list(self) -> list[Subscription]:
        return self._locked_subscription_list.obj

    @subscription_list.setter
    def subscription_list(self, subscription_list: list[Subscription]) -> None:
        self.subscribe(expected_list=subscription_list)

    @property
    def websocket(self) -> Connection | None:
        return self._websocket

    def build_url(self) -> str:
        listen_key = self._listen_key

        if listen_key and listen_key.locked_key:
            url = f"{SWAP_MARKET}?listenKey={listen_key.locked_key.get_key()}"
        else:
            url = SWAP_MARKET

        return url

    def run(self):
        catch_exception = self._catch_exception
        event_stop = self._event_stop
        logger = self._logger
        max_connection_retry = self._max_connection_retry
        queue_iterator = self._queue_iterator

        connection_retry = 0
        url = self.build_url()

        while not event_stop.is_set() and connection_retry <= max_connection_retry:
            try:
                with client.connect(url) as websocket:
                    self._websocket = websocket

                    logger.debug("<BINGX:WS>:READING")

                    self.subscribe()

                    for message_gzip in websocket:
                        if event_stop.is_set():
                            logger.debug("<BINGX:WS>:STOP_READING")
                            break

                        if connection_retry:
                            connection_retry = 0

                        message = self.decompress(data=message_gzip)

                        if self.is_ping(message=message):
                            websocket.send(message=b"Pong")
                            logger.debug("<BINGX:WS>:SENDING:MESSAGE:%s", b"Pong")
                        elif self.is_error(message=message):
                            logger.fatal("<BINGX:WS>:ERROR:MESSAGE:%s", message)
                        elif self.is_subscription_confirmation(message=message):
                            logger.debug("<BINGX:WS>:CONFIRMATION:MESSAGE:%s", message)
                        else:
                            logger.debug("<BINGX:WS>:CONTENT:MESSAGE:%s", message)
                            queue_iterator.put_nowait(item=message)
            except ConnectionClosed as e:
                if not catch_exception:
                    raise e

                logger.fatal("<BINGX:WS>:%s", e)
                connection_retry += 1

    def subscribe(self, expected_list: list[Subscription] | None = None) -> None:
        locked_subscription_list = self._locked_subscription_list
        logger = self._logger
        websocket = self._websocket

        with locked_subscription_list as current_list:
            if websocket is None:
                current_list[:] = expected_list or current_list
            elif expected_list:
                query_channel_list = self.build_query_channel_list_diff(
                    current_list=current_list,
                    expected_list=expected_list,
                )
                self.send_query_channel_list(
                    logger=logger,
                    query_channel_list=query_channel_list,
                    websocket=websocket,
                )
                current_list[:] = expected_list
            else:
                query_channel_list = self.build_query_channel_list(
                    subscription_list=current_list,
                )
                self.send_query_channel_list(
                    logger=logger,
                    query_channel_list=query_channel_list,
                    websocket=websocket,
                )


StreamerChannel = BaseStreamer[ProducerChannel, bytes]

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.FATAL)

    streamer = StreamerChannel(
        producer=ProducerChannel(
            subscription_list=[
                Subscription(
                    id="id1",
                    data_type="BTC-USDT@lastPrice",
                ),
                Subscription(
                    id="id1",
                    data_type="ETH-USDT@lastPrice",
                ),
            ],
        ),
    )

    try:
        for received_message in streamer:
            print(received_message)
    except KeyboardInterrupt:
        print("Closing the websocket connection.")
