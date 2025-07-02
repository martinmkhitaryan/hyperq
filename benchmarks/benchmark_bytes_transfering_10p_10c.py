import multiprocessing as mp
import time
import uuid
from multiprocessing import Queue as MPQueue
from typing import TypedDict

import faster_fifo

from hyperq import BytesHyperQ, HyperQ


class BenchmarkResult(TypedDict):
    total: float
    throughput: float
    latency: float
    queue_class: str


def hyperq_producer(queue_name: str, producer_id: int, num_messages: int, message_size: int):
    queue = HyperQ(queue_name)

    message = b"x" * message_size

    for i in range(num_messages):
        queue.put(message)


def hyperq_consumer(queue_name: str, consumer_id: int):
    queue = HyperQ(queue_name)

    while True:
        message = queue.get()
        if message == b"TERMINATE":
            break


def bytes_hyperq_producer(queue_name: str, producer_id: int, num_messages: int, message_size: int):
    queue = BytesHyperQ(queue_name)

    message = b"x" * message_size

    for i in range(num_messages):
        queue.put(message)


def bytes_hyperq_consumer(queue_name: str, consumer_id: int):
    queue = BytesHyperQ(queue_name)

    while True:
        message = queue.get()

        if message == b"TERMINATE":
            break


def mp_producer(queue: MPQueue, producer_id: int, num_messages: int, message_size: int):
    message = b"x" * message_size

    for i in range(num_messages):
        queue.put(message)


def mp_consumer(queue: MPQueue, consumer_id: int):
    while True:
        message = queue.get()

        if message == b"TERMINATE":
            break


def ff_producer(queue: faster_fifo.Queue, producer_id: int, num_messages: int, message_size: int):
    message = b"x" * message_size

    for i in range(num_messages):
        queue.put(message)


def ff_consumer(queue: faster_fifo.Queue, consumer_id: int):
    while True:
        message = queue.get()

        if message == b"TERMINATE":
            break


def test_hyperq_2p2c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    num_producers = 2
    num_consumers = 2
    total_messages = num_producers * messages_per_producer

    queue_suffix = str(uuid.uuid4())[:4]
    queue_name = f"/hq2p2c_{queue_suffix}"

    queue = HyperQ(1024 * 1024, name=queue_name)
    actual_queue_name = queue.shm_name

    start_time = time.perf_counter()

    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=hyperq_producer, args=(actual_queue_name, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=hyperq_consumer, args=(actual_queue_name, i))
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

    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "HyperQ",
    }


def test_bytes_hyperq_2p2c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    num_producers = 2
    num_consumers = 2
    total_messages = num_producers * messages_per_producer

    queue_suffix = str(uuid.uuid4())[:4]
    queue_name = f"/bhq2p2c_{queue_suffix}"

    queue = BytesHyperQ(1024 * 1024, name=queue_name)
    actual_queue_name = queue.shm_name

    start_time = time.perf_counter()

    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=bytes_hyperq_producer, args=(actual_queue_name, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=bytes_hyperq_consumer, args=(actual_queue_name, i))
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

    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "BytesHyperQ",
    }


def test_mp_2p2c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    num_producers = 2
    num_consumers = 2
    total_messages = num_producers * messages_per_producer

    queue = MPQueue()

    start_time = time.perf_counter()

    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=mp_producer, args=(queue, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=mp_consumer, args=(queue, i))
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

    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "multiprocessing.Queue",
    }


def test_ff_2p2c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    num_producers = 2
    num_consumers = 2
    total_messages = num_producers * messages_per_producer

    queue = faster_fifo.Queue(max_size_bytes=1024 * 1024)

    start_time = time.perf_counter()

    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=ff_producer, args=(queue, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=ff_consumer, args=(queue, i))
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

    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "faster-fifo",
    }


def run_benchmark(message_size: int, messages_per_producer: int) -> dict[str, BenchmarkResult]:
    hyperq_results = test_hyperq_2p2c(message_size, messages_per_producer)

    print(f"HyperQ results: {hyperq_results}")
    bytes_hyperq_results = test_bytes_hyperq_2p2c(message_size, messages_per_producer)
    print(f"BytesHyperQ results: {bytes_hyperq_results}")
    mp_results = test_mp_2p2c(message_size, messages_per_producer)
    print(f"multiprocessing.Queue results: {mp_results}")
    ff_results = test_ff_2p2c(message_size, messages_per_producer)
    print(f"faster-fifo results: {ff_results}")
    return {
        "hyperq": hyperq_results,
        "bytes_hyperq": bytes_hyperq_results,
        "mp_queue": mp_results,
        "faster_fifo": ff_results,
    }


def main():
    test_configs = [
        (42_000, 32),
        (42_000, 64),
        (42_000, 128),
        (42_000, 256),
        (42_000, 512),
        (42_000, 1024),
        (42_000, 4 * 1024),
        (42_000, 8 * 1024),
        (42_000, 16 * 1024),
        (42_000, 32 * 1024),
    ]

    print("Running 2p2c bytes performance benchmarks...")
    print("=" * 80)

    headers = [
        "Queue Type",
        "Total Time (s)",
        "Latency (ms)",
        "Throughput (items/s)",
    ]

    for messages_per_producer, message_size in test_configs:
        print(f"\nResults for {messages_per_producer:,} messages of {message_size} bytes per producer:")
        print(f"Total messages: {messages_per_producer * 2:,} (2 producers)")
        print("-" * 80)

        results = run_benchmark(message_size, messages_per_producer)

        table_data = [
            [
                "HyperQ",
                results['hyperq']['total'],
                results['hyperq']['latency'],
                int(results['hyperq']['throughput']),
            ],
            [
                "BytesHyperQ",
                results['bytes_hyperq']['total'],
                results['bytes_hyperq']['latency'],
                int(results['bytes_hyperq']['throughput']),
            ],
            [
                "multiprocessing.Queue",
                results['mp_queue']['total'],
                results['mp_queue']['latency'],
                int(results['mp_queue']['throughput']),
            ],
            [
                "faster-fifo",
                results['faster_fifo']['total'],
                results['faster_fifo']['latency'],
                int(results['faster_fifo']['throughput']),
            ],
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

        if (messages_per_producer, message_size) != test_configs[-1]:
            print("\n" + "=" * 80)
            print("Sleeping 2 seconds before next test configuration...")
            time.sleep(2)

    return test_configs


if __name__ == "__main__":
    mp.set_start_method("fork")
    main()
