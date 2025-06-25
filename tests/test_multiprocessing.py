import multiprocessing as mp
from functools import partial

import hyperq


def producer(queue_name: str, num_items: int, data_length: int, queue_class: type, data_type: str) -> None:
    q = queue_class(queue_name)
    data = (data_type * data_length) if data_type == "x" else (b"x" * data_length)
    for _ in range(num_items):
        q.put(data)


def consumer(queue_name: str, num_items: int, queue_class: type) -> None:
    q = queue_class(queue_name)
    for _ in range(num_items):
        q.get()


class TestMultiprocessingBasic:
    def _run_multiprocessing_test(self, queue_class: type, queue_name: str, data_type: str = "x"):
        num_items = 100
        data_length = 64

        q = queue_class(num_items * data_length * 2, queue_name)

        consumer_proc = mp.Process(target=partial(consumer, queue_name, num_items, queue_class))
        producer_proc = mp.Process(target=partial(producer, queue_name, num_items, data_length, queue_class, data_type))

        consumer_proc.start()
        producer_proc.start()
        producer_proc.join()
        consumer_proc.join()

        assert producer_proc.exitcode == 0
        assert consumer_proc.exitcode == 0
        assert q.empty

    def test_hyperq_basic_multiprocessing(self):
        """Test basic HyperQ multiprocessing functionality."""
        self._run_multiprocessing_test(hyperq.HyperQ, "test_hyperq_basic", "x")

    def test_bytes_hyperq_basic_multiprocessing(self):
        """Test basic BytesHyperQ multiprocessing functionality."""
        self._run_multiprocessing_test(hyperq.BytesHyperQ, "test_bytes_basic", "bytes")
