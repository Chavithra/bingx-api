from logging import getLogger, Logger
from threading import Event, Lock, Thread
from time import sleep
from requests import HTTPError

from robot_one.api.bingx.future.ws.read_listen_key import query_listen_key
from robot_one.api.bingx.future.ws.update_listen_key import (
    query_update_listen_key,
    QueryUpdateListenKey,
)

__all__ = [
    "LockedKey",
    "ValidListenKey",
]


class LockedKey:
    def __init__(self, key: str):
        self._key = key
        self._lock = Lock()

    def update_key(self, key: str):
        with self._lock:
            self._key = key

    def get_key(self) -> str:
        with self._lock:
            return self._key

    def __repr__(self):
        return f"LockedKey(key='{self._key}')"


class ValidListenKey(Thread):
    def __init__(
        self,
        logger: Logger | None = None,
        refresh_s: int = 1800,
    ) -> None:
        """Listen key expires 60 minutes after creation.
        Once refreshed/extended it is valid for an extra 60 minutes.
        Bingx recommend refreshing the key every 30 minutes.
        """

        Thread.__init__(self)

        self._refresh_s = refresh_s
        self._logger = logger or getLogger(name=self.__class__.__name__)

        self._locked_key: LockedKey | None = None
        self._stop_event = Event()
        self._ready_event = Event()

    @property
    def refresh_s(self) -> int:
        return self._refresh_s

    @property
    def locked_key(self) -> LockedKey | None:
        return self._locked_key

    @property
    def ready_event(self) -> Event:
        return self._ready_event

    @property
    def stop_event(self) -> Event:
        return self._stop_event

    def __enter__(self):
        read_event = self._ready_event

        self.start()

        read_event.wait()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def refresh_locked_key(self):
        locked_key = self._locked_key
        logger = self._logger
        ready_event = self._ready_event

        if locked_key is None:
            self._locked_key = LockedKey(key=query_listen_key())
            ready_event.set()
            logger.debug("<BINGX:REST>::NEW:LISTEN_KEY:%s", self._locked_key)
        else:
            try:
                query_update_listen_key(
                    query=QueryUpdateListenKey(
                        listen_key=locked_key.get_key(),
                    )
                )

                logger.debug("<BINGX:REST>::REFRESHED:LISTEN_KEY:%s", self._locked_key)
            except HTTPError as e:
                logger.fatal(e)
                self._locked_key = None

    def run(self):
        refresh_s = self._refresh_s
        logger = self._logger
        stop_event = self._stop_event

        logger.debug("<BINGX:REST>::NEW:WS_LISTEN_KEY:%s", self.locked_key)

        while True:
            self.refresh_locked_key()

            if stop_event.is_set():
                logger.debug(
                    "<BINGX:REST>::STOP_REFRESHING:WS_LISTEN_KEY:%s",
                    self._locked_key,
                )
                break

            logger.debug("<BINGX:REST>::SLEEPING:INTERVAL_S:%s", refresh_s)

            sleep(refresh_s)

    def stop(self):
        self._stop_event.set()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)

    valid_listen_key = ValidListenKey(refresh_s=10)

    with valid_listen_key as fresh_key:
        locked = fresh_key.locked_key
        if locked:
            print(locked.get_key())

        sleep(40)
