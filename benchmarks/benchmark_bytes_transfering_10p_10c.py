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
    messages_sent = 0

    # Create a message of specified size
    message = b"x" * message_size

    for i in range(num_messages):
        if queue.put(message):
            messages_sent += 1

    # Send termination signal (small message)
    termination_msg = b"TERMINATE"
    queue.put(termination_msg)


def hyperq_consumer(queue_name: str, consumer_id: int):
    queue = HyperQ(queue_name)

    while True:
        message = queue.get()

        # Check if this is a termination signal
        if message == b"TERMINATE":
            break


def bytes_hyperq_producer(queue_name: str, producer_id: int, num_messages: int, message_size: int):
    queue = BytesHyperQ(queue_name)
    messages_sent = 0

    # Create a message of specified size
    message = b"x" * message_size

    for i in range(num_messages):
        if queue.put(message):
            messages_sent += 1

    # Send termination signal (small message)
    termination_msg = b"TERMINATE"
    queue.put(termination_msg)


def bytes_hyperq_consumer(queue_name: str, consumer_id: int):
    queue = BytesHyperQ(queue_name)

    while True:
        message = queue.get()

        # Check if this is a termination signal
        if message == b"TERMINATE":
            break


def mp_producer(queue: MPQueue, producer_id: int, num_messages: int, message_size: int):
    messages_sent = 0

    # Create a message of specified size
    message = b"x" * message_size

    for i in range(num_messages):
        queue.put(message)
        messages_sent += 1

    # Send termination signal (small message)
    termination_msg = b"TERMINATE"
    queue.put(termination_msg)


def mp_consumer(queue: MPQueue, consumer_id: int):
    while True:
        message = queue.get()

        # Check if this is a termination signal
        if message == b"TERMINATE":
            break


def ff_producer(queue: faster_fifo.Queue, producer_id: int, num_messages: int, message_size: int):
    messages_sent = 0

    # Create a message of specified size
    message = b"x" * message_size

    for i in range(num_messages):
        queue.put(message)
        messages_sent += 1

    # Send termination signal (small message)
    termination_msg = b"TERMINATE"
    queue.put(termination_msg)


def ff_consumer(queue: faster_fifo.Queue, consumer_id: int):
    while True:
        message = queue.get()

        # Check if this is a termination signal
        if message == b"TERMINATE":
            break


def test_hyperq_10p10c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    """Test function for HyperQ with 10 producers and 10 consumers."""
    # Test parameters
    num_producers = 10
    num_consumers = 10
    total_messages = num_producers * messages_per_producer

    # Generate unique queue name (keep under 28 chars)
    queue_suffix = str(uuid.uuid4())[:4]
    queue_name = f"/hq10p10c_{queue_suffix}"

    # Create the queue in main process
    queue = HyperQ(1024 * 1024, name=queue_name)
    actual_queue_name = queue.shm_name

    # Start timing
    start_time = time.perf_counter()

    # Start producers
    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=hyperq_producer, args=(actual_queue_name, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    # Start consumers
    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=hyperq_consumer, args=(actual_queue_name, i))
        p.start()
        consumer_processes.append(p)

    # Wait for all producers to finish
    for p in producer_processes:
        p.join()

    # Wait for all consumers to finish
    for p in consumer_processes:
        p.join()

    # End timing
    end_time = time.perf_counter()
    duration = end_time - start_time

    # Calculate performance metrics
    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    # Return results in the same format as benchmark_bytes_transfering_1p_1c.py
    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "HyperQ",
    }


def test_bytes_hyperq_10p10c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    """Test function for BytesHyperQ with 10 producers and 10 consumers."""
    # Test parameters
    num_producers = 10
    num_consumers = 10
    total_messages = num_producers * messages_per_producer

    # Generate unique queue name (keep under 28 chars)
    queue_suffix = str(uuid.uuid4())[:4]
    queue_name = f"/bhq10p10c_{queue_suffix}"

    # Create the queue in main process
    queue = BytesHyperQ(1024 * 1024, name=queue_name)
    actual_queue_name = queue.shm_name

    # Start timing
    start_time = time.perf_counter()

    # Start producers
    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=bytes_hyperq_producer, args=(actual_queue_name, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    # Start consumers
    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=bytes_hyperq_consumer, args=(actual_queue_name, i))
        p.start()
        consumer_processes.append(p)

    # Wait for all producers to finish
    for p in producer_processes:
        p.join()

    # Wait for all consumers to finish
    for p in consumer_processes:
        p.join()

    # End timing
    end_time = time.perf_counter()
    duration = end_time - start_time

    # Calculate performance metrics
    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    # Return results in the same format as benchmark_bytes_transfering_1p_1c.py
    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "BytesHyperQ",
    }


def test_mp_10p10c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    """Test function for multiprocessing.Queue with 10 producers and 10 consumers."""
    # Test parameters
    num_producers = 10
    num_consumers = 10
    total_messages = num_producers * messages_per_producer

    # Create the multiprocessing queue
    queue = MPQueue()

    # Start timing
    start_time = time.perf_counter()

    # Start producers
    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=mp_producer, args=(queue, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    # Start consumers
    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=mp_consumer, args=(queue, i))
        p.start()
        consumer_processes.append(p)

    # Wait for all producers to finish
    for p in producer_processes:
        p.join()

    # Wait for all consumers to finish
    for p in consumer_processes:
        p.join()

    # End timing
    end_time = time.perf_counter()
    duration = end_time - start_time

    # Calculate performance metrics
    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    # Return results in the same format as benchmark_bytes_transfering_1p_1c.py
    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "multiprocessing.Queue",
    }


def test_ff_10p10c(message_size: int, messages_per_producer: int) -> BenchmarkResult:
    """Test function for faster-fifo.Queue with 10 producers and 10 consumers."""
    # Test parameters
    num_producers = 10
    num_consumers = 10
    total_messages = num_producers * messages_per_producer

    # Create the faster-fifo queue
    queue = faster_fifo.Queue(max_size_bytes=1024 * 1024)

    # Start timing
    start_time = time.perf_counter()

    # Start producers
    producer_processes = []
    for i in range(num_producers):
        p = mp.Process(target=ff_producer, args=(queue, i, messages_per_producer, message_size))
        p.start()
        producer_processes.append(p)

    # Start consumers
    consumer_processes = []
    for i in range(num_consumers):
        p = mp.Process(target=ff_consumer, args=(queue, i))
        p.start()
        consumer_processes.append(p)

    # Wait for all producers to finish
    for p in producer_processes:
        p.join()

    # Wait for all consumers to finish
    for p in consumer_processes:
        p.join()

    # End timing
    end_time = time.perf_counter()
    duration = end_time - start_time

    # Calculate performance metrics
    throughput = total_messages / duration
    latency = (duration / total_messages * 1000) if total_messages > 0 else 0

    # Return results in the same format as benchmark_bytes_transfering_1p_1c.py
    return {
        "total": duration,
        "throughput": throughput,
        "latency": latency,
        "queue_class": "faster-fifo",
    }


def run_benchmark(message_size: int, messages_per_producer: int) -> dict[str, BenchmarkResult]:
    """Run benchmark for all queue types and return results."""
    # Test HyperQ
    hyperq_results = test_hyperq_10p10c(message_size, messages_per_producer)

    # Test BytesHyperQ
    bytes_hyperq_results = test_bytes_hyperq_10p10c(message_size, messages_per_producer)

    # Test Multiprocessing.Queue
    mp_results = test_mp_10p10c(message_size, messages_per_producer)

    # Test faster-fifo.Queue
    ff_results = test_ff_10p10c(message_size, messages_per_producer)

    return {
        "hyperq": hyperq_results,
        "bytes_hyperq": bytes_hyperq_results,
        "mp_queue": mp_results,
        "faster_fifo": ff_results,
    }


def main():
    """Run performance benchmarks with different configurations."""
    # Test configurations: (messages_per_producer, message_size)
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

    print("Running 10p10c bytes performance benchmarks...")
    print("=" * 80)

    headers = [
        "Queue Type",
        "Total Time (s)",
        "Latency (ms)",
        "Throughput (items/s)",
    ]

    for messages_per_producer, message_size in test_configs:
        print(f"\nResults for {messages_per_producer:,} messages of {message_size} bytes per producer:")
        print(f"Total messages: {messages_per_producer * 10:,} (10 producers)")
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

        # Print table using simple formatting
        print(f"{headers[0]:<20} {headers[1]:<15} {headers[2]:<15} {headers[3]:<20}")
        print("-" * 80)
        for row in table_data:
            print(f"{row[0]:<20} {row[1]:<15.3f} {row[2]:<15.3f} {row[3]:<20,}")

        fastest_queue = table_data[0][0]
        fastest_throughput = table_data[0][3]
        print(f"\n🏆 Fastest: {fastest_queue} with {fastest_throughput:,} items/s")

        # Calculate speed ratios compared to other queue types
        for i in range(1, len(table_data)):
            slower_queue = table_data[i][0]
            slower_throughput = table_data[i][3]
            ratio = fastest_throughput / slower_throughput
            print(f"   {ratio:.1f}x faster than {slower_queue}")

        # Sleep between test configurations to ensure clean separation
        if (messages_per_producer, message_size) != test_configs[-1]:
            print("\n" + "=" * 80)
            print("Sleeping 2 seconds before next test configuration...")
            time.sleep(2)

    return test_configs


if __name__ == "__main__":
    # Set multiprocessing start method for macOS
    mp.set_start_method('fork', force=True)
    main()
