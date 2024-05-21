from abc import ABC, abstractmethod
from queue import SimpleQueue
from threading import Event, Thread
from typing import Generic, TypeVar

__all__ = (
    "BaseProducer",
    "BaseStreamer",
)


class BaseProducer(ABC, Thread):
    @property
    @abstractmethod
    def queue_iterator(self) -> SimpleQueue:
        pass

    @property
    @abstractmethod
    def event_stop(self) -> Event:
        pass


ContentType = TypeVar("ContentType")
ProducerType = TypeVar("ProducerType", bound=BaseProducer)


class BaseStreamer(Generic[ProducerType, ContentType]):
    def __init__(
        self,
        producer: ProducerType,
    ):
        self._producer = producer
        self._running = False

    def __enter__(self):
        self.__start_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._producer.event_stop.set()

    def __iter__(self):
        self.__start_thread()
        return self

    def __next__(self) -> ContentType:
        return self._producer.queue_iterator.get()

    def __start_thread(self) -> None:
        if not self._running:
            self._producer.start()
            self._running = True

    @property
    def producer(self) -> ProducerType:
        return self._producer

    def start(self) -> ProducerType:
        return self._producer.start()

    def stop(self) -> None:
        self._producer.event_stop.set()
