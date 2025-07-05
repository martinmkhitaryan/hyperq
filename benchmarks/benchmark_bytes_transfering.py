import multiprocessing as mp
import time
import uuid
from multiprocessing import Queue as MPQueue
from typing import Any, Callable, TypedDict, Union

import faster_fifo

from hyperq import BytesHyperQ, HyperQ


class BenchmarkResult(TypedDict):
    total: float
    throughput: float
    latency: float
    queue_class: str


class QueueConfig:
    def __init__(
        self, name: str, queue_class: str, queue_factory: Callable, producer_target: Callable, consumer_target: Callable
    ):
        self.name = name
        self.queue_class = queue_class
        self.queue_factory = queue_factory
        self.producer_target = producer_target
        self.consumer_target = consumer_target


def generic_producer(queue: Any, producer_id: int, num_messages: int, message_size: int):
    message = b"x" * message_size
    for i in range(num_messages):
        queue.put(message)


def generic_consumer(queue: Any, consumer_id: int):
    while True:
        message = queue.get()
        if message == b"TERMINATE":
            break


def hyperq_producer(queue_name: str, producer_id: int, num_messages: int, message_size: int):
    queue = HyperQ(queue_name)
    generic_producer(queue, producer_id, num_messages, message_size)


def hyperq_consumer(queue_name: str, consumer_id: int):
    queue = HyperQ(queue_name)
    generic_consumer(queue, consumer_id)


def bytes_hyperq_producer(queue_name: str, producer_id: int, num_messages: int, message_size: int):
    queue = BytesHyperQ(queue_name)
    generic_producer(queue, producer_id, num_messages, message_size)


def bytes_hyperq_consumer(queue_name: str, consumer_id: int):
    queue = BytesHyperQ(queue_name)
    generic_consumer(queue, consumer_id)


def mp_producer(queue: MPQueue, producer_id: int, num_messages: int, message_size: int):
    generic_producer(queue, producer_id, num_messages, message_size)


def mp_consumer(queue: MPQueue, consumer_id: int):
    generic_consumer(queue, consumer_id)


def ff_producer(queue: faster_fifo.Queue, producer_id: int, num_messages: int, message_size: int):
    generic_producer(queue, producer_id, num_messages, message_size)


def ff_consumer(queue: faster_fifo.Queue, consumer_id: int):
    generic_consumer(queue, consumer_id)


def calculate_metrics(duration: float, total_messages: int) -> tuple[float, float]:
    """Calculate throughput and latency from duration and message count."""
    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0
    return throughput, latency


def run_benchmark_test(
    config: QueueConfig, message_size: int, messages_per_producer: int, num_producers: int, num_consumers: int
) -> BenchmarkResult:
    """Generic benchmark test function that works with any queue configuration."""
    total_messages = num_producers * messages_per_producer

    if config.name in ["HyperQ", "BytesHyperQ"]:
        queue_name = str(uuid.uuid4())[:24]
        queue = config.queue_factory(name=queue_name)
        actual_queue_name = queue.shm_name
    else:
        queue = config.queue_factory()
        actual_queue_name = queue

    start_time = time.perf_counter()

    producer_processes = []
    for i in range(num_producers):
        args = (
            (actual_queue_name, i, messages_per_producer, message_size)
            if config.name in ["HyperQ", "BytesHyperQ"]
            else (queue, i, messages_per_producer, message_size)
        )
        p = mp.Process(target=config.producer_target, args=args)
        p.start()
        producer_processes.append(p)

    consumer_processes = []
    for i in range(num_consumers):
        args = (actual_queue_name, i) if config.name in ["HyperQ", "BytesHyperQ"] else (queue, i)
        p = mp.Process(target=config.consumer_target, args=args)
        p.start()
        consumer_processes.append(p)

    for p in producer_processes:
        p.join()

    for _ in range(num_consumers):
        queue.put(b"TERMINATE")

    for p in consumer_processes:
        p.join()

    end_time = time.perf_counter()
    duration = end_time - start_time

    throughput, latency = calculate_metrics(duration, total_messages)

    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": config.queue_class,
    }


QUEUE_SIZE = 1024 * 1024
QUEUE_CONFIGS = {
    "hyperq": QueueConfig(
        name="HyperQ",
        queue_class="HyperQ",
        queue_factory=lambda name: HyperQ(QUEUE_SIZE, name=name),
        producer_target=hyperq_producer,
        consumer_target=hyperq_consumer,
    ),
    "bytes_hyperq": QueueConfig(
        name="BytesHyperQ",
        queue_class="BytesHyperQ",
        queue_factory=lambda name: BytesHyperQ(QUEUE_SIZE, name=name),
        producer_target=bytes_hyperq_producer,
        consumer_target=bytes_hyperq_consumer,
    ),
    "mp_queue": QueueConfig(
        name="multiprocessing.Queue",
        queue_class="multiprocessing.Queue",
        queue_factory=lambda: MPQueue(),
        producer_target=mp_producer,
        consumer_target=mp_consumer,
    ),
    "faster_fifo": QueueConfig(
        name="faster-fifo",
        queue_class="faster-fifo",
        queue_factory=lambda: faster_fifo.Queue(max_size_bytes=QUEUE_SIZE),
        producer_target=ff_producer,
        consumer_target=ff_consumer,
    ),
}


def run_benchmark(
    message_size: int, messages_per_producer: int, num_producers: int = 4, num_consumers: int = 4
) -> dict[str, BenchmarkResult]:
    results = {}

    for key, config in QUEUE_CONFIGS.items():
        result = run_benchmark_test(config, message_size, messages_per_producer, num_producers, num_consumers)
        results[key] = result

    return results


def main():
    test_configs = [
        (message_count, message_size, num_producers, num_consumers)
        for num_consumers, num_producers in [[1, 1], [4, 4]]
        for message_count in [100000]
        for message_size in [32, 64, 128, 256, 512, 1024, 4 * 1024, 8 * 1024, 16 * 1024, 32 * 1024]
    ]

    print("Running bytes performance benchmarks...")
    print("=" * 80)

    headers = [
        "Queue Type",
        "Total Time (s)",
        "Latency (ms)",
        "Throughput (items/s)",
    ]

    for messages_per_producer, message_size, num_producers, num_consumers in test_configs:
        print(f"\nResults for {messages_per_producer:,} messages of {message_size} bytes per producer:")
        print(
            f"Total messages: {messages_per_producer * num_producers:,} ({num_producers} producers, {num_consumers} consumers)"
        )
        print("-" * 80)

        results = run_benchmark(message_size, messages_per_producer, num_producers, num_consumers)

        table_data = [
            [
                config.name,
                results[key]['total'],
                results[key]['latency'],
                int(results[key]['throughput']),
            ]
            for key, config in QUEUE_CONFIGS.items()
        ]

        table_data.sort(key=lambda x: x[3], reverse=True)

        print(f"{headers[0]:<20} {headers[1]:<15} {headers[2]:<15} {headers[3]:<20}")
        print("-" * 80)
        for row in table_data:
            print(f"{row[0]:<20} {row[1]:<15.3f} {row[2]:<15.3f} {row[3]:<20,}")

        fastest_queue = table_data[0][0]
        fastest_throughput = table_data[0][3]
        print(f"\n🏆 Fastest: {fastest_queue} with {fastest_throughput:,} items/s")

        for i in range(1, len(table_data)):
            slower_queue = table_data[i][0]
            slower_throughput = table_data[i][3]
            ratio = fastest_throughput / slower_throughput
            print(f"   {ratio:.1f}x faster than {slower_queue}")

        if (messages_per_producer, message_size, num_producers, num_consumers) != test_configs[-1]:
            print("\n" + "=" * 80)
            print("Sleeping 2 seconds before next test configuration...")
            time.sleep(2)

    return test_configs


if __name__ == "__main__":
    main()
