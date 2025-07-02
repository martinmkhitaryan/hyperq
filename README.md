# HyperQ

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/hyperq.svg)](https://badge.fury.io/py/hyperq)

> ⚠️ **Warning: This package is not ready for production usage yet.** It's currently in active development and may have bugs, especially with multiprocessing scenarios using the spawn start method.

**Hyper-fast queue for Python** - A high-performance queue implementation using Cython and C++ for inter-process communication.

## 🚀 Features

- **Lightning Fast**: Optimized C++ implementation with Python bindings
- **Inter-Process Communication**: Shared memory-based queues for high-performance IPC
- **Ring Buffer Architecture**: Uses a ring buffer with double virtual memory mapping to the same physical memory.
- **Two Queue Types**:
  - `HyperQ`: General-purpose queue for Python objects
  - `BytesHyperQ`: Specialized queue for bytes data (even faster)
- **Thread-Safe**: Safe for concurrent access
- **Unix-like Systems**: Works on Linux and macOS (POSIX-compliant systems)
- **Python 3.10+**: Modern Python support

## 📋 TODO

- [ ] **Fix multiprocessing spawn start method bug** - Critical issue with multiple consumers/producers
  - Queue doesn't work properly when `multiprocessing.set_start_method('spawn')` is used
  - Affects scenarios with multiple consumers and producers
- [ ] **Add `__getstate__` and `__setstate__` methods** to make queue objects picklable
  - Allow passing queue objects directly to multiprocessing functions
  - Serialize only the shared memory name/descriptor, not the entire queue state
  - Enable seamless integration with multiprocessing.Pool and other parallel processing tools
- [ ] **Add timeout support** for `put()` and `get()` operations
- [ ] **Add non-blocking operations** (`put_nowait()`, `get_nowait()`)
  - `put_nowait()`: Non-blocking put that raises `queue.Full` if queue is full
  - `get_nowait()`: Non-blocking get that raises `queue.Empty` if queue is empty
  - Useful for polling scenarios where you don't want to block the thread
- [ ] **Add batch operations** for better performance
  - `put_many(items)`: Put multiple items in a single operation
  - `get_many(count)`: Get multiple items in a single operation
  - `get_all()`: Get all available items at once
  - Reduces synchronization overhead for bulk operations
- [ ] **Design decision: Queue name management**
  - **Option A**: Encapsulate queue names (auto-generate, hide from client)
  - **Option B**: Client specifies queue names (current approach)
  - **Option C**: Hybrid approach (auto-generate with optional override)
- [ ] **Add Windows support** (requires different shared memory implementation)
- [ ] **Add more comprehensive tests** including stress tests and edge cases
- [ ] **Add documentation** for advanced usage patterns
  - **orjson + BytesHyperQ for JSON**: Use `orjson.dumps()` + `BytesHyperQ` for fastest JSON serialization and transfer.



## ⚠️ Platform Support

**Currently supported:**
- ✅ Linux
- ✅ macOS

**Not supported:**
- ❌ Windows (uses POSIX-specific APIs)
- ❌ PyPy

## 🔧 Technical Details

### Ring Buffer Implementation

HyperQ uses a ring buffer with double virtual memory mapping to the same physical memory. This eliminates the need for 2 memcpy operations when data wraps around the buffer boundaries.

### Shared Memory Architecture

- **Header segment**: Contains queue metadata, synchronization primitives, and buffer information
- **Buffer segment**: The actual data storage with double virtual memory mapping
- **POSIX shared memory**: Uses `shm_open()` and `mmap()` for cross-process memory sharing
- **Synchronization**: Uses POSIX mutexes and condition variables for thread/process safety

## 📦 Installation

### From PyPI

```bash
pip install hyperq
```

### From Source

```bash
git clone https://github.com/martinmkhitaryan/hyperq.git
cd hyperq
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/martinmkhitaryan/hyperq.git
cd hyperq
pip install -e ".[test]"
```

## 🎯 Quick Start

### Basic Usage

```python
import multiprocessing as mp
from hyperq import HyperQ, BytesHyperQ

# Create a queue with 1MB capacity
queue = HyperQ(1024 * 1024, name="/my_queue")

# Put data
queue.put("Hello, World!")
queue.put(42)
queue.put({"key": "value"})

# Get data
data = queue.get()  # "Hello, World!"
number = queue.get()  # 42
obj = queue.get()  # {"key": "value"}
```

### Inter-Process Communication

```python
import multiprocessing as mp
from hyperq import HyperQ

def producer(queue_name):
    queue = HyperQ(queue_name)
    for i in range(1000):
        queue.put(f"Message {i}")

def consumer(queue_name):
    queue = HyperQ(queue_name)
    for _ in range(1000):
        message = queue.get()
        print(f"Received: {message}")

if __name__ == "__main__":
    # Create queue in main process
    queue = HyperQ(1024 * 1024, name="/shared_queue")
    queue_name = queue.shm_name

    # Start producer and consumer processes
    p1 = mp.Process(target=producer, args=(queue_name,))
    p2 = mp.Process(target=consumer, args=(queue_name,))

    p1.start()
    p2.start()
    p1.join()
    p2.join()
```

### Bytes-Specific Queue (Faster)

```python
from hyperq import BytesHyperQ

# For bytes data, use BytesHyperQ for better performance
queue = BytesHyperQ(1024 * 1024, name="/bytes_queue")

# Put bytes data
queue.put(b"Hello, World!")
queue.put(b"Binary data")

# Get bytes data
data = queue.get()  # b"Hello, World!"
```

## 📊 Performance Benchmarks

HyperQ is designed for high-performance scenarios. Here are some benchmark results:

**Hardware:**
- **CPU**: Intel(R) Core(TM) i9-9980HK CPU @ 2.40GHz
- **Memory**: 16GB
- **OS**: macOS 15.3.1
- **Python**: 3.10


### 1 Producer, 1 Consumer
```bash
Running bytes performance benchmarks...
================================================================

Results for 100000 messages of 32 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.119976      0.00119976                  833499
HyperQ                         0.421588      0.00421588                  237198
multiprocessing.Queue          2.09399       0.0209399                    47755
faster-fifo                    2.36328       0.0236328                    42314
🏆 Fastest: BytesHyperQ with 833,499 items/s
   3.5x faster than HyperQ
   17.5x faster than multiprocessing.Queue
   19.7x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 64 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.124732      0.00124732                  801717
HyperQ                         0.474716      0.00474716                  210652
faster-fifo                    1.67101       0.0167101                    59843
multiprocessing.Queue          2.20561       0.0220561                    45338
🏆 Fastest: BytesHyperQ with 801,717 items/s
   3.8x faster than HyperQ
   13.4x faster than faster-fifo
   17.7x faster than multiprocessing.Queue

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 128 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.116276      0.00116276                  860024
HyperQ                         0.499545      0.00499545                  200182
multiprocessing.Queue          1.99662       0.0199662                    50084
faster-fifo                    2.65151       0.0265151                    37714
🏆 Fastest: BytesHyperQ with 860,024 items/s
   4.3x faster than HyperQ
   17.2x faster than multiprocessing.Queue
   22.8x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 256 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.235679      0.00235679                  424305
HyperQ                         0.837711      0.00837711                  119372
multiprocessing.Queue          2.32011       0.0232011                    43101
faster-fifo                    2.68104       0.0268104                    37298
🏆 Fastest: BytesHyperQ with 424,305 items/s
   3.6x faster than HyperQ
   9.8x faster than multiprocessing.Queue
   11.4x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 512 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.251292      0.00251292                  397943
HyperQ                         0.770943      0.00770943                  129711
multiprocessing.Queue          2.08766       0.0208766                    47900
faster-fifo                    2.16858       0.0216858                    46113
🏆 Fastest: BytesHyperQ with 397,943 items/s
   3.1x faster than HyperQ
   8.3x faster than multiprocessing.Queue
   8.6x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 1024 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.209373      0.00209373                  477616
HyperQ                         0.664122      0.00664122                  150574
multiprocessing.Queue          2.28728       0.0228728                    43720
faster-fifo                    2.30807       0.0230807                    43326
🏆 Fastest: BytesHyperQ with 477,616 items/s
   3.2x faster than HyperQ
   10.9x faster than multiprocessing.Queue
   11.0x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 4096 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.419936      0.00419936                  238131
HyperQ                         1.0191        0.010191                     98126
multiprocessing.Queue          2.18819       0.0218819                    45699
faster-fifo                    3.13527       0.0313527                    31895
🏆 Fastest: BytesHyperQ with 238,131 items/s
   2.4x faster than HyperQ
   5.2x faster than multiprocessing.Queue
   7.5x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 8192 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                    0.701695      0.00701695                  142512
HyperQ                         1.34373       0.0134373                    74419
multiprocessing.Queue          2.95495       0.0295495                    33841
faster-fifo                    3.40265       0.0340265                    29388
🏆 Fastest: BytesHyperQ with 142,512 items/s
   1.9x faster than HyperQ
   4.2x faster than multiprocessing.Queue
   4.8x faster than faster-fifo

================================================================
Sleeping 2 seconds before next test configuration...

Results for 100000 messages of 16384 bytes:
Queue Type               Total Time (s)    Latency (ms)    Throughput (items/s)
---------------------  ----------------  --------------  ----------------------
BytesHyperQ                     1.22369       0.0122369                   81720
HyperQ                          1.62568       0.0162568                   61512
faster-fifo                     3.81159       0.0381159                   26235
multiprocessing.Queue           5.12029       0.0512029                   19530
🏆 Fastest: BytesHyperQ with 81,720 items/s
   1.3x faster than HyperQ
   3.1x faster than faster-fifo
   4.2x faster than multiprocessing.Queue
```

*Results may vary depending on hardware and system configuration.*

## 🔧 API Reference

### HyperQ

```python
class HyperQ:
    def __init__(self, capacity: int, name: str = None)

    def put(self, item) -> bool
    def get(self)  # Blocks until data is available
    def empty(self) -> bool
    def full(self) -> bool
    def size(self) -> int
    def clear(self)
```

### BytesHyperQ

```python
class BytesHyperQ:
    def __init__(self, capacity: int, name: str = None)

    def put(self, data: bytes) -> bool
    def get(self) -> bytes  # Blocks until data is available
    def empty(self) -> bool
    def full(self) -> bool
    def size(self) -> int
    def clear(self)
```

### Parameters

- **capacity**: Maximum size of the queue in bytes
- **name**: Optional name for the shared memory segment (max 28 characters)

### Important Notes

- **Blocking operations**: `get()` blocks indefinitely until data is available
- **No timeout support**: Currently no timeout functionality is implemented
- **Queue names**: Must be 28 characters or less
- **Platform limitation**: Only works on Unix-like systems (Linux/macOS)

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hyperq
```

## 📈 Running Benchmarks

```bash
# 1 producer, 1 consumer benchmark
python benchmarks/benchmark_bytes_transfering_1p_1c.py

# 10 producers, 10 consumers benchmark
python benchmarks/benchmark_bytes_transfering_10p_10c.py
```

## 🏗️ Building from Source

### Prerequisites

- Python 3.10+
- Cython >= 0.29.0
- C++ compiler with C++20 support (GCC 8+, Clang 10+)
- Unix-like system (Linux or macOS)

### Build Steps

```bash
# Clone the repository
git clone https://github.com/martinmkhitaryan/hyperq.git
cd hyperq

# Install build dependencies
pip install -e ".[test]"

# Build the extension
python setup.py build_ext --inplace
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `source .venv/bin/activate` (Linux/macOS)
4. Install development dependencies: `pip install -e ".[test]"`
5. Run tests: `pytest`
6. Make your changes and submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Cython](https://cython.org/) for high-performance Python extensions
- Uses POSIX shared memory and threading primitives
- Inspired by the need for faster inter-process communication in Python

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/martinmkhitaryan/hyperq/issues)
- **Discussions**: [GitHub Discussions](https://github.com/martinmkhitaryan/hyperq/discussions)
- **Email**: mkhitaryan.martin@2000gmail.com

## 🔄 Version History
- **0.0.7**: Replaced is_creator logic with ref count logic for better shared memory management; identified and documented issue with multiprocessing spawn start method not working properly with multiple consumers and producers
- **0.0.6**: Fix cibuildwheel configurations.
- **0.0.5**: Added platform-specific build and skip patterns for Linux and macOS; improved cibuildwheel configuration with separate build targets for manylinux and macosx wheels
- **0.0.4**: Fixed cibuildwheel configuration for proper multi-platform wheel builds; added architecture-specific settings for Linux (x86_64/i686) and macOS (x86_64/arm64);
- **0.0.3**: Fixed cibuildwheel configuration for proper linux wheel build;
- **0.0.2**: Added proper PyPI wheel support for Linux and macOS using cibuildwheel; improved release workflow for multi-platform builds and C++20 compatibility
- **0.0.1**: Initial release with HyperQ and BytesHyperQ implementations

---
