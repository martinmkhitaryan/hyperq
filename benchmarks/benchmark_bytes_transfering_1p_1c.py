#!/usr/bin/env python3
"""
Performance benchmark for HyperQ vs BytesHyperQ vs multiprocessing.Queue vs faster-fifo using bytes data
"""

import multiprocessing as mp
import time
from typing import Union

import faster_fifo
from tabulate import tabulate

import hyperq


def hyperq_producer(queue_name: str, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Producer function specifically for HyperQ using bytes data."""
    q = hyperq.HyperQ(queue_name)
    data = b"x" * data_length
    start = time.time()
    for _ in range(num_items):
        q.put(data)
    end = time.time()
    results_queue.put(("hyperq_producer", end - start))


def hyperq_consumer(queue_name: str, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Consumer function specifically for HyperQ."""
    q = hyperq.HyperQ(queue_name)
    start = time.time()
    for _ in range(num_items):
        q.get()
    end = time.time()
    results_queue.put(("hyperq_consumer", end - start))


def bytes_hyperq_producer(queue_name: str, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Producer function specifically for BytesHyperQ using bytes data."""
    q = hyperq.BytesHyperQ(queue_name)
    data = b"x" * data_length
    start = time.time()
    for _ in range(num_items):
        q.put(data)
    end = time.time()
    results_queue.put(("byteshyperq_producer", end - start))


def bytes_hyperq_consumer(queue_name: str, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Consumer function specifically for BytesHyperQ."""
    q = hyperq.BytesHyperQ(queue_name)
    start = time.time()
    for _ in range(num_items):
        q.get()
    end = time.time()
    results_queue.put(("byteshyperq_consumer", end - start))


def mp_queue_producer(queue: mp.Queue, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Producer function for standard multiprocessing.Queue using bytes data."""
    data = b"x" * data_length
    start = time.time()
    for _ in range(num_items):
        queue.put(data)
    end = time.time()
    results_queue.put(("mp_queue_producer", end - start))


def mp_queue_consumer(queue: mp.Queue, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Consumer function for standard multiprocessing.Queue."""
    start = time.time()
    for _ in range(num_items):
        queue.get()
    end = time.time()
    results_queue.put(("mp_queue_consumer", end - start))


def faster_fifo_producer(queue: faster_fifo.Queue, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Producer function for faster-fifo using bytes data."""
    data = b"x" * data_length
    start = time.time()
    for _ in range(num_items):
        queue.put(data)
    end = time.time()
    results_queue.put(("faster_fifo_producer", end - start))


def faster_fifo_consumer(queue: faster_fifo.Queue, num_items: int, data_length: int, results_queue: mp.Queue) -> None:
    """Consumer function for faster-fifo."""
    start = time.time()
    for _ in range(num_items):
        queue.get()
    end = time.time()
    results_queue.put(("faster_fifo_consumer", end - start))


def run_hyperq_benchmark(
    queue_name: str, num_items: int, data_length: int, results_queue: mp.Queue
) -> dict[str, float]:
    """Run benchmark specifically for HyperQ using dedicated producer/consumer functions."""
    # Create queue with capacity and name
    capacity = 1024 * 1024  # 1MB
    queue = hyperq.HyperQ(capacity, name=queue_name)
    actual_queue_name = queue.shm_name

    # Start producer and consumer processes using dedicated functions
    consumer_proc = mp.Process(target=hyperq_consumer, args=(actual_queue_name, num_items, data_length, results_queue))
    producer_proc = mp.Process(target=hyperq_producer, args=(actual_queue_name, num_items, data_length, results_queue))

    consumer_proc.start()
    producer_proc.start()
    producer_proc.join()
    consumer_proc.join()

    # Collect results
    queue_results: dict[str, float] = {}
    for _ in range(2):
        name, time_taken = results_queue.get()
        queue_results[name] = time_taken

    # Calculate metrics
    total_time = queue_results["hyperq_producer"] + queue_results["hyperq_consumer"]
    throughput = num_items / total_time if total_time > 0 else 0
    latency = (total_time / num_items * 1000) if num_items > 0 else 0

    return {"total": total_time, "throughput": throughput, "latency": latency}


def run_bytes_hyperq_benchmark(
    queue_name: str, num_items: int, data_length: int, results_queue: mp.Queue
) -> dict[str, float]:
    """Run benchmark specifically for BytesHyperQ using dedicated producer/consumer functions."""
    # Create queue with capacity and name
    capacity = 1024 * 1024  # 1MB
    queue = hyperq.BytesHyperQ(capacity, name=queue_name)
    actual_queue_name = queue.shm_name

    # Start producer and consumer processes using dedicated functions
    consumer_proc = mp.Process(
        target=bytes_hyperq_consumer, args=(actual_queue_name, num_items, data_length, results_queue)
    )
    producer_proc = mp.Process(
        target=bytes_hyperq_producer, args=(actual_queue_name, num_items, data_length, results_queue)
    )

    consumer_proc.start()
    producer_proc.start()
    producer_proc.join()
    consumer_proc.join()

    # Collect results
    queue_results: dict[str, float] = {}
    for _ in range(2):
        name, time_taken = results_queue.get()
        queue_results[name] = time_taken

    # Calculate metrics
    total_time = queue_results["byteshyperq_producer"] + queue_results["byteshyperq_consumer"]
    throughput = num_items / total_time if total_time > 0 else 0
    latency = (total_time / num_items * 1000) if num_items > 0 else 0

    return {"total": total_time, "throughput": throughput, "latency": latency}


def run_mp_queue_benchmark(num_items: int, data_length: int, results_queue: mp.Queue) -> dict[str, float]:
    """Run benchmark for standard multiprocessing.Queue using dedicated producer/consumer functions."""
    # Create multiprocessing queue
    queue = mp.Queue()

    # Start producer and consumer processes using dedicated functions
    consumer_proc = mp.Process(target=mp_queue_consumer, args=(queue, num_items, data_length, results_queue))
    producer_proc = mp.Process(target=mp_queue_producer, args=(queue, num_items, data_length, results_queue))

    consumer_proc.start()
    producer_proc.start()
    producer_proc.join()
    consumer_proc.join()

    # Collect results
    queue_results: dict[str, float] = {}
    for _ in range(2):
        name, time_taken = results_queue.get()
        queue_results[name] = time_taken

    # Calculate metrics
    total_time = queue_results["mp_queue_producer"] + queue_results["mp_queue_consumer"]
    throughput = num_items / total_time if total_time > 0 else 0
    latency = (total_time / num_items * 1000) if num_items > 0 else 0

    return {"total": total_time, "throughput": throughput, "latency": latency}


def run_faster_fifo_benchmark(num_items: int, data_length: int, results_queue: mp.Queue) -> dict[str, float]:
    """Run benchmark for faster-fifo using dedicated producer/consumer functions."""
    # Create faster-fifo queue
    queue = faster_fifo.Queue()

    # Start producer and consumer processes using dedicated functions
    consumer_proc = mp.Process(target=faster_fifo_consumer, args=(queue, num_items, data_length, results_queue))
    producer_proc = mp.Process(target=faster_fifo_producer, args=(queue, num_items, data_length, results_queue))

    consumer_proc.start()
    producer_proc.start()
    producer_proc.join()
    consumer_proc.join()

    # Collect results
    queue_results: dict[str, float] = {}
    for _ in range(2):
        name, time_taken = results_queue.get()
        queue_results[name] = time_taken

    # Calculate metrics
    total_time = queue_results["faster_fifo_producer"] + queue_results["faster_fifo_consumer"]
    throughput = num_items / total_time if total_time > 0 else 0
    latency = (total_time / num_items * 1000) if num_items > 0 else 0

    return {"total": total_time, "throughput": throughput, "latency": latency}


def run_benchmark(num_items: int, data_length: int) -> dict[str, dict[str, Union[float, str]]]:
    """Run benchmark for all queue types and return results."""
    results_queue: mp.Queue = mp.Queue()

    # Test HyperQ
    hyperq_name = f"hq_{num_items}_{data_length}"
    hyperq_results = run_hyperq_benchmark(hyperq_name, num_items, data_length, results_queue)

    # Test BytesHyperQ
    bytes_name = f"bhq_{num_items}_{data_length}"
    bytes_results = run_bytes_hyperq_benchmark(bytes_name, num_items, data_length, results_queue)

    # Test multiprocessing.Queue
    mp_results = run_mp_queue_benchmark(num_items, data_length, results_queue)

    # Test faster-fifo
    faster_fifo_results = run_faster_fifo_benchmark(num_items, data_length, results_queue)

    # Add queue class to each result
    hyperq_with_class: dict[str, Union[float, str]] = {
        "total": hyperq_results["total"],
        "throughput": hyperq_results["throughput"],
        "latency": hyperq_results["latency"],
        "queue_class": "HyperQ",
    }
    bytes_with_class: dict[str, Union[float, str]] = {
        "total": bytes_results["total"],
        "throughput": bytes_results["throughput"],
        "latency": bytes_results["latency"],
        "queue_class": "BytesHyperQ",
    }
    mp_with_class: dict[str, Union[float, str]] = {
        "total": mp_results["total"],
        "throughput": mp_results["throughput"],
        "latency": mp_results["latency"],
        "queue_class": "multiprocessing.Queue",
    }
    faster_fifo_with_class: dict[str, Union[float, str]] = {
        "total": faster_fifo_results["total"],
        "throughput": faster_fifo_results["throughput"],
        "latency": faster_fifo_results["latency"],
        "queue_class": "faster-fifo",
    }

    return {
        "hyperq": hyperq_with_class,
        "bytes": bytes_with_class,
        "mp_queue": mp_with_class,
        "faster_fifo": faster_fifo_with_class,
    }


def main():
    """Run performance benchmarks and display results."""
    test_configs = [
        (100_000, 32),
        (100_000, 64),
        (100_000, 128),
        (100_000, 256),
        (100_000, 512),
        (100_000, 1024),
        (100_000, 4 * 1024),
        (100_000, 8 * 1024),
        (100_000, 16 * 1024),
    ]

    print("Running bytes performance benchmarks...")
    print("=" * 64)

    headers = [
        "Queue Type",
        "Total Time (s)",
        "Latency (ms)",
        "Throughput (items/s)",
    ]

    for num_items, data_length in test_configs:
        results = run_benchmark(num_items, data_length)

        table_data = [
            [
                "HyperQ",
                results['hyperq']['total'],
                results['hyperq']['latency'],
                int(results['hyperq']['throughput']),
            ],
            [
                "BytesHyperQ",
                results['bytes']['total'],
                results['bytes']['latency'],
                int(results['bytes']['throughput']),
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

        print(f"\nResults for {num_items} messages of {data_length} bytes:")
        print(tabulate(table_data, headers=headers))

        fastest_queue = table_data[0][0]
        fastest_throughput = table_data[0][3]
        print(f"🏆 Fastest: {fastest_queue} with {fastest_throughput:,} items/s")

        # Calculate speed ratios compared to other queue types
        for i in range(1, len(table_data)):
            slower_queue = table_data[i][0]
            slower_throughput = table_data[i][3]
            ratio = fastest_throughput / slower_throughput
            print(f"   {ratio:.1f}x faster than {slower_queue}")

        # Sleep between test configurations to ensure clean separation
        if num_items != test_configs[-1][0] or data_length != test_configs[-1][1]:
            print("\n" + "=" * 64)
            print("Sleeping 2 seconds before next test configuration...")
            time.sleep(2)

    return test_configs


if __name__ == "__main__":
    main()
