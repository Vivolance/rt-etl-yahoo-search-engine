import time
from typing import Generic, TypeVar

SingleMessage = TypeVar("SingleMessage")


class Batcher(Generic[SingleMessage]):
    def __init__(self, batch_size: int = 100, batch_timeout_s: int = 1):
        self._batch_start: float = -1
        self._batch: list[SingleMessage] = []
        self._batch_size: int = batch_size
        self._batch_timeout_s: int = batch_timeout_s

    def batch_ready(self) -> bool:
        """
        Case 1: current time - batch_start > _batch_timeout_s
        - produce

        Case 2: batch_size == 100
        - produce

        return False
        """
        hit_timeout: bool = (
            time.perf_counter() - self._batch_start > self._batch_timeout_s
        )
        hit_batch_size: bool = len(self._batch) >= self._batch_size
        return hit_timeout or hit_batch_size

    def reset_batch(self) -> None:
        """
        Resets the batch
        - Clear the batch list
        - Reset the batch start
        """
        self._batch.clear()
        self._batch_start = time.perf_counter()

    def get_batch(self) -> list[SingleMessage]:
        return self._batch

    def append(self, message: SingleMessage) -> None:
        self._batch.append(message)

    def append_batch(self, messages: list[SingleMessage]) -> None:
        self._batch.extend(messages)
