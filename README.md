# HyperQ

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/hyperq.svg)](https://badge.fury.io/py/hyperq)

**Hyper-fast queue for Python** - A high-performance queue implementation using Cython and C++ for inter-process communication.

## 🚀 Features

- **Lightning Fast**: Optimized C++ implementation with Python bindings
- **Inter-Process Communication**: Shared memory-based queues for high-performance IPC
- **Ring Buffer Architecture**: Uses a ring buffer with double virtual memory mapping to the same physical memory.
- **Two Queue Types**:
  - `HyperQ`: General-purpose queue for Python objects
  - `BytesHyperQ`: Specialized queue for bytes data
- **Thread-Safe**: Safe for concurrent access
- **Unix-like Systems**: Works on Linux and macOS (POSIX-compliant systems)
- **Python 3.10+**: Modern Python support

## 📋 TODO

- [ ] **Fix multiprocessing spawn start method bug in macOS** - Critical issue with multiple consumers/producers
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
- ⚠️ macOS (There is an issue when start method is set to spawn and there are multiple producers/consumers)

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
queue = HyperQ(1024 * 1024, name="my_queue")

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
    queue = HyperQ(1024 * 1024, name="shared_queue")
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
queue = BytesHyperQ(1024 * 1024, name="bytes_queue")

# Put bytes data
queue.put(b"Hello, World!")
queue.put(b"Binary data")

# Get bytes data
data = queue.get()  # b"Hello, World!"
```

## 📊 Performance Benchmarks

HyperQ is designed for high-performance scenarios. Here are some benchmark results:

**Hardware:**
- **CPU**: Intel® Core™ i3-12100 
- **Memory**: 8GB
- **OS**: Ubuntu 22.04 / Virtual Box
- **Python**: 3.12


### Benchmark bytes transfering.
```bash
Running bytes performance benchmarks...
================================================================================

Results for 100,000 messages of 32 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.018           0.000           5,528,243           
HyperQ               0.090           0.001           1,106,593           
multiprocessing.Queue 0.334           0.003           299,499             
faster-fifo          0.406           0.004           246,330             

🏆 Fastest: BytesHyperQ with 5,528,243 items/s
   5.0x faster than HyperQ
   18.5x faster than multiprocessing.Queue
   22.4x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 64 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.020           0.000           5,067,022           
HyperQ               0.090           0.001           1,105,261           
multiprocessing.Queue 0.388           0.004           257,635             
faster-fifo          0.397           0.004           251,805             

🏆 Fastest: BytesHyperQ with 5,067,022 items/s
   4.6x faster than HyperQ
   19.7x faster than multiprocessing.Queue
   20.1x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 128 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.025           0.000           3,988,545           
HyperQ               0.102           0.001           984,694             
multiprocessing.Queue 0.332           0.003           301,471             
faster-fifo          0.402           0.004           248,764             

🏆 Fastest: BytesHyperQ with 3,988,545 items/s
   4.1x faster than HyperQ
   13.2x faster than multiprocessing.Queue
   16.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 256 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.030           0.000           3,280,452           
HyperQ               0.098           0.001           1,024,640           
multiprocessing.Queue 0.344           0.003           290,311             
faster-fifo          0.395           0.004           253,071             

🏆 Fastest: BytesHyperQ with 3,280,452 items/s
   3.2x faster than HyperQ
   11.3x faster than multiprocessing.Queue
   13.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 512 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.028           0.000           3,550,212           
HyperQ               0.105           0.001           956,745             
multiprocessing.Queue 0.357           0.004           279,993             
faster-fifo          0.420           0.004           238,251             

🏆 Fastest: BytesHyperQ with 3,550,212 items/s
   3.7x faster than HyperQ
   12.7x faster than multiprocessing.Queue
   14.9x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 1024 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.042           0.000           2,390,645           
HyperQ               0.109           0.001           917,085             
multiprocessing.Queue 0.379           0.004           263,922             
faster-fifo          0.413           0.004           241,983             

🏆 Fastest: BytesHyperQ with 2,390,645 items/s
   2.6x faster than HyperQ
   9.1x faster than multiprocessing.Queue
   9.9x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 4096 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.077           0.001           1,296,410           
HyperQ               0.153           0.002           653,955             
multiprocessing.Queue 0.420           0.004           238,116             
faster-fifo          0.437           0.004           228,823             

🏆 Fastest: BytesHyperQ with 1,296,410 items/s
   2.0x faster than HyperQ
   5.4x faster than multiprocessing.Queue
   5.7x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 8192 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.107           0.001           936,460             
HyperQ               0.203           0.002           492,091             
multiprocessing.Queue 0.497           0.005           201,165             
faster-fifo          0.539           0.005           185,473             

🏆 Fastest: BytesHyperQ with 936,460 items/s
   1.9x faster than HyperQ
   4.7x faster than multiprocessing.Queue
   5.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 16384 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.189           0.002           528,889             
HyperQ               0.303           0.003           329,876             
multiprocessing.Queue 0.658           0.007           152,017             
faster-fifo          0.762           0.008           131,168             

🏆 Fastest: BytesHyperQ with 528,889 items/s
   1.6x faster than HyperQ
   3.5x faster than multiprocessing.Queue
   4.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 32768 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.375           0.004           266,432             
HyperQ               0.484           0.005           206,720             
faster-fifo          0.939           0.009           106,544             
multiprocessing.Queue 1.053           0.011           94,985              

🏆 Fastest: BytesHyperQ with 266,432 items/s
   1.3x faster than HyperQ
   2.5x faster than faster-fifo
   2.8x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 32 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.097           0.000           4,142,198           
HyperQ               0.313           0.001           1,276,678           
faster-fifo          0.863           0.002           463,335             
multiprocessing.Queue 2.907           0.007           137,604             

🏆 Fastest: BytesHyperQ with 4,142,198 items/s
   3.2x faster than HyperQ
   8.9x faster than faster-fifo
   30.1x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 64 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.108           0.000           3,713,089           
HyperQ               0.336           0.001           1,189,575           
faster-fifo          0.847           0.002           472,108             
multiprocessing.Queue 2.928           0.007           136,622             

🏆 Fastest: BytesHyperQ with 3,713,089 items/s
   3.1x faster than HyperQ
   7.9x faster than faster-fifo
   27.2x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 128 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.104           0.000           3,838,310           
HyperQ               0.293           0.001           1,365,044           
faster-fifo          0.880           0.002           454,557             
multiprocessing.Queue 2.968           0.007           134,779             

🏆 Fastest: BytesHyperQ with 3,838,310 items/s
   2.8x faster than HyperQ
   8.4x faster than faster-fifo
   28.5x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 256 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.121           0.000           3,306,829           
HyperQ               0.346           0.001           1,156,464           
faster-fifo          0.848           0.002           471,452             
multiprocessing.Queue 3.024           0.008           132,281             

🏆 Fastest: BytesHyperQ with 3,306,829 items/s
   2.9x faster than HyperQ
   7.0x faster than faster-fifo
   25.0x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 512 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.139           0.000           2,870,961           
HyperQ               0.413           0.001           968,493             
faster-fifo          0.892           0.002           448,522             
multiprocessing.Queue 3.143           0.008           127,257             

🏆 Fastest: BytesHyperQ with 2,870,961 items/s
   3.0x faster than HyperQ
   6.4x faster than faster-fifo
   22.6x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 1024 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.209           0.001           1,918,401           
HyperQ               0.546           0.001           732,611             
faster-fifo          0.929           0.002           430,677             
multiprocessing.Queue 3.299           0.008           121,240             

🏆 Fastest: BytesHyperQ with 1,918,401 items/s
   2.6x faster than HyperQ
   4.5x faster than faster-fifo
   15.8x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 4096 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.400           0.001           1,001,018           
HyperQ               0.745           0.002           536,564             
faster-fifo          1.176           0.003           340,031             
multiprocessing.Queue 4.032           0.010           99,196              

🏆 Fastest: BytesHyperQ with 1,001,018 items/s
   1.9x faster than HyperQ
   2.9x faster than faster-fifo
   10.1x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 8192 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.679           0.002           589,081             
HyperQ               1.111           0.003           359,917             
faster-fifo          1.554           0.004           257,363             
multiprocessing.Queue 4.742           0.012           84,353              

🏆 Fastest: BytesHyperQ with 589,081 items/s
   1.6x faster than HyperQ
   2.3x faster than faster-fifo
   7.0x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 16384 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          1.278           0.003           313,053             
HyperQ               1.765           0.004           226,633             
faster-fifo          2.442           0.006           163,817             
multiprocessing.Queue 6.288           0.016           63,613              

🏆 Fastest: BytesHyperQ with 313,053 items/s
   1.4x faster than HyperQ
   1.9x faster than faster-fifo
   4.9x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 32768 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          2.374           0.006           168,526             
HyperQ               2.887           0.007           138,536             
faster-fifo          3.804           0.010           105,154             
multiprocessing.Queue 10.354          0.026           38,634              

🏆 Fastest: BytesHyperQ with 168,526 items/s
   1.2x faster than HyperQ
   1.6x faster than faster-fifo
   4.4x faster than multiprocessing.Queue
Running bytes performance benchmarks...
================================================================================

Results for 100,000 messages of 32 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.018           0.000           5,528,243           
HyperQ               0.090           0.001           1,106,593           
multiprocessing.Queue 0.334           0.003           299,499             
faster-fifo          0.406           0.004           246,330             

🏆 Fastest: BytesHyperQ with 5,528,243 items/s
   5.0x faster than HyperQ
   18.5x faster than multiprocessing.Queue
   22.4x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 64 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.020           0.000           5,067,022           
HyperQ               0.090           0.001           1,105,261           
multiprocessing.Queue 0.388           0.004           257,635             
faster-fifo          0.397           0.004           251,805             

🏆 Fastest: BytesHyperQ with 5,067,022 items/s
   4.6x faster than HyperQ
   19.7x faster than multiprocessing.Queue
   20.1x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 128 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.025           0.000           3,988,545           
HyperQ               0.102           0.001           984,694             
multiprocessing.Queue 0.332           0.003           301,471             
faster-fifo          0.402           0.004           248,764             

🏆 Fastest: BytesHyperQ with 3,988,545 items/s
   4.1x faster than HyperQ
   13.2x faster than multiprocessing.Queue
   16.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 256 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.030           0.000           3,280,452           
HyperQ               0.098           0.001           1,024,640           
multiprocessing.Queue 0.344           0.003           290,311             
faster-fifo          0.395           0.004           253,071             

🏆 Fastest: BytesHyperQ with 3,280,452 items/s
   3.2x faster than HyperQ
   11.3x faster than multiprocessing.Queue
   13.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 512 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.028           0.000           3,550,212           
HyperQ               0.105           0.001           956,745             
multiprocessing.Queue 0.357           0.004           279,993             
faster-fifo          0.420           0.004           238,251             

🏆 Fastest: BytesHyperQ with 3,550,212 items/s
   3.7x faster than HyperQ
   12.7x faster than multiprocessing.Queue
   14.9x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 1024 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.042           0.000           2,390,645           
HyperQ               0.109           0.001           917,085             
multiprocessing.Queue 0.379           0.004           263,922             
faster-fifo          0.413           0.004           241,983             

🏆 Fastest: BytesHyperQ with 2,390,645 items/s
   2.6x faster than HyperQ
   9.1x faster than multiprocessing.Queue
   9.9x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 4096 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.077           0.001           1,296,410           
HyperQ               0.153           0.002           653,955             
multiprocessing.Queue 0.420           0.004           238,116             
faster-fifo          0.437           0.004           228,823             

🏆 Fastest: BytesHyperQ with 1,296,410 items/s
   2.0x faster than HyperQ
   5.4x faster than multiprocessing.Queue
   5.7x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 8192 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.107           0.001           936,460             
HyperQ               0.203           0.002           492,091             
multiprocessing.Queue 0.497           0.005           201,165             
faster-fifo          0.539           0.005           185,473             

🏆 Fastest: BytesHyperQ with 936,460 items/s
   1.9x faster than HyperQ
   4.7x faster than multiprocessing.Queue
   5.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 16384 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.189           0.002           528,889             
HyperQ               0.303           0.003           329,876             
multiprocessing.Queue 0.658           0.007           152,017             
faster-fifo          0.762           0.008           131,168             

🏆 Fastest: BytesHyperQ with 528,889 items/s
   1.6x faster than HyperQ
   3.5x faster than multiprocessing.Queue
   4.0x faster than faster-fifo

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 32768 bytes per producer:
Total messages: 100,000 (1 producers, 1 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.375           0.004           266,432             
HyperQ               0.484           0.005           206,720             
faster-fifo          0.939           0.009           106,544             
multiprocessing.Queue 1.053           0.011           94,985              

🏆 Fastest: BytesHyperQ with 266,432 items/s
   1.3x faster than HyperQ
   2.5x faster than faster-fifo
   2.8x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 32 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.097           0.000           4,142,198           
HyperQ               0.313           0.001           1,276,678           
faster-fifo          0.863           0.002           463,335             
multiprocessing.Queue 2.907           0.007           137,604             

🏆 Fastest: BytesHyperQ with 4,142,198 items/s
   3.2x faster than HyperQ
   8.9x faster than faster-fifo
   30.1x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 64 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.108           0.000           3,713,089           
HyperQ               0.336           0.001           1,189,575           
faster-fifo          0.847           0.002           472,108             
multiprocessing.Queue 2.928           0.007           136,622             

🏆 Fastest: BytesHyperQ with 3,713,089 items/s
   3.1x faster than HyperQ
   7.9x faster than faster-fifo
   27.2x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 128 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.104           0.000           3,838,310           
HyperQ               0.293           0.001           1,365,044           
faster-fifo          0.880           0.002           454,557             
multiprocessing.Queue 2.968           0.007           134,779             

🏆 Fastest: BytesHyperQ with 3,838,310 items/s
   2.8x faster than HyperQ
   8.4x faster than faster-fifo
   28.5x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 256 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.121           0.000           3,306,829           
HyperQ               0.346           0.001           1,156,464           
faster-fifo          0.848           0.002           471,452             
multiprocessing.Queue 3.024           0.008           132,281             

🏆 Fastest: BytesHyperQ with 3,306,829 items/s
   2.9x faster than HyperQ
   7.0x faster than faster-fifo
   25.0x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 512 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.139           0.000           2,870,961           
HyperQ               0.413           0.001           968,493             
faster-fifo          0.892           0.002           448,522             
multiprocessing.Queue 3.143           0.008           127,257             

🏆 Fastest: BytesHyperQ with 2,870,961 items/s
   3.0x faster than HyperQ
   6.4x faster than faster-fifo
   22.6x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 1024 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.209           0.001           1,918,401           
HyperQ               0.546           0.001           732,611             
faster-fifo          0.929           0.002           430,677             
multiprocessing.Queue 3.299           0.008           121,240             

🏆 Fastest: BytesHyperQ with 1,918,401 items/s
   2.6x faster than HyperQ
   4.5x faster than faster-fifo
   15.8x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 4096 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.400           0.001           1,001,018           
HyperQ               0.745           0.002           536,564             
faster-fifo          1.176           0.003           340,031             
multiprocessing.Queue 4.032           0.010           99,196              

🏆 Fastest: BytesHyperQ with 1,001,018 items/s
   1.9x faster than HyperQ
   2.9x faster than faster-fifo
   10.1x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 8192 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          0.679           0.002           589,081             
HyperQ               1.111           0.003           359,917             
faster-fifo          1.554           0.004           257,363             
multiprocessing.Queue 4.742           0.012           84,353              

🏆 Fastest: BytesHyperQ with 589,081 items/s
   1.6x faster than HyperQ
   2.3x faster than faster-fifo
   7.0x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 16384 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          1.278           0.003           313,053             
HyperQ               1.765           0.004           226,633             
faster-fifo          2.442           0.006           163,817             
multiprocessing.Queue 6.288           0.016           63,613              

🏆 Fastest: BytesHyperQ with 313,053 items/s
   1.4x faster than HyperQ
   1.9x faster than faster-fifo
   4.9x faster than multiprocessing.Queue

================================================================================
Sleeping 2 seconds before next test configuration...

Results for 100,000 messages of 32768 bytes per producer:
Total messages: 400,000 (4 producers, 4 consumers)
--------------------------------------------------------------------------------
Queue Type           Total Time (s)  Latency (ms)    Throughput (items/s)
--------------------------------------------------------------------------------
BytesHyperQ          2.374           0.006           168,526             
HyperQ               2.887           0.007           138,536             
faster-fifo          3.804           0.010           105,154             
multiprocessing.Queue 10.354          0.026           38,634              

🏆 Fastest: BytesHyperQ with 168,526 items/s
   1.2x faster than HyperQ
   1.6x faster than faster-fifo
   4.4x faster than multiprocessing.Queue
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
python benchmarks/benchmark_bytes_transfering.py
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
- **1.0.0**: First working version on Linux and macOS (single producer and single consumer only; multiple producers or consumers not supported).
- **0.1.0**: Refactored constructor and destructor in hyperq.hpp; reference count via atomic variable.
- **0.0.9**: Updated benchmarks in README.md.
- **0.0.8**: Updated benchmark suite, test suite, pyproject.toml configuration; optimized CI/CD release workflow.
- **0.0.7**: Replaced is_creator logic with ref count logic for better shared memory management; identified and documented issue with multiprocessing spawn start method not working properly with multiple consumers and producers.
- **0.0.6**: Fix cibuildwheel configurations.
- **0.0.5**: Added platform-specific build and skip patterns for Linux and macOS; improved cibuildwheel configuration with separate build targets for manylinux and macosx wheels
- **0.0.4**: Fixed cibuildwheel configuration for proper multi-platform wheel builds; added architecture-specific settings for Linux (x86_64/i686) and macOS (x86_64/arm64);
- **0.0.3**: Fixed cibuildwheel configuration for proper linux wheel build;
- **0.0.2**: Added proper PyPI wheel support for Linux and macOS using cibuildwheel; improved release workflow for multi-platform builds and C++20 compatibility
- **0.0.1**: Initial release with HyperQ and BytesHyperQ implementations
---
