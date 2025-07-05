import multiprocessing as mp
import uuid
from functools import partial

import hyperq


def producer(queue_name: str, num_items: int, data_length: int, queue_class: type) -> None:
    q = queue_class(queue_name)
    data = b"x" * data_length
    for _ in range(num_items):
        q.put(data)


def consumer(queue_name: str, num_items: int, queue_class: type) -> None:
    q = queue_class(queue_name)
    for _ in range(num_items):
        q.get()


class TestMultiprocessingBasic:
    def _run_multiprocessing_test(self, queue_class: type, queue_name: str):
        num_items = 100
        data_length = 64

        q = queue_class(num_items * data_length * 2, queue_name)

        consumer_proc = mp.Process(target=partial(consumer, queue_name, num_items, queue_class))
        producer_proc = mp.Process(target=partial(producer, queue_name, num_items, data_length, queue_class))

        consumer_proc.start()
        producer_proc.start()
        producer_proc.join()
        consumer_proc.join()

        assert producer_proc.exitcode == 0
        assert consumer_proc.exitcode == 0
        assert q.empty

    def test_hyperq_basic_multiprocessing(self):
        self._run_multiprocessing_test(hyperq.HyperQ, "test_hyperq_basic")

    def test_bytes_hyperq_basic_multiprocessing(self):
        self._run_multiprocessing_test(hyperq.BytesHyperQ, "test_bytes_basic")


class TestMultiprocessingMethods:
    def _run_stress_test(self, start_method: str, queue_class: type):
        mp.set_start_method(start_method, force=True)

        num_items_per_producer = 1000
        data_length = 256
        total_items = num_items_per_producer * 2

        queue_name = str(uuid.uuid4())[:24]

        q = queue_class(total_items * data_length * 4, queue_name)

        producers = []
        consumers = []

        for i in range(2):
            producer_proc = mp.Process(
                target=partial(producer, queue_name, num_items_per_producer, data_length, queue_class),
                name=f"producer_{i}",
            )
            producers.append(producer_proc)

        for i in range(2):
            consumer_proc = mp.Process(
                target=partial(consumer, queue_name, num_items_per_producer, queue_class), name=f"consumer_{i}"
            )
            consumers.append(consumer_proc)

        for proc in consumers + producers:
            proc.start()

        for proc in producers + consumers:
            proc.join()

        for proc in producers + consumers:
            assert proc.exitcode == 0, f"Process {proc.name} failed with exit code {proc.exitcode}"

        assert q.empty, f"Queue should be empty after stress test, but has {q.size} items"

    def test_hyperq_spawn_stress(self):
        self._run_stress_test("spawn", hyperq.HyperQ)

    def test_hyperq_fork_stress(self):
        self._run_stress_test("fork", hyperq.HyperQ)

    def test_bytes_hyperq_spawn_stress(self):
        self._run_stress_test("spawn", hyperq.BytesHyperQ)

    def test_bytes_hyperq_fork_stress(self):
        self._run_stress_test("fork", hyperq.BytesHyperQ)
