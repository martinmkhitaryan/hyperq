from dataclasses import dataclass

import numpy as np

import hyperq


@dataclass
class CustomClass:
    x: int
    y: str
    z: float


class TestDifferentDataTypes:
    """Test HyperQ with different data types."""

    def test_different_data_types(self):
        q = hyperq.HyperQ(1024 * 1024, "tddt")
        arr = np.arange(10, dtype=np.float32)

        test_cases = [
            42,
            3.14159,
            "hello world",
            b"byte string",
            {"a": 1, "b": 2},
            [1, 2, 3, "four"],
            (5, 6, 7, "eight"),
            CustomClass(7, "test", 2.71),
            None,
            True,
            False,
            arr,
        ]

        for i, obj in enumerate(test_cases):
            q.put(obj)
            result = q.get()

            if isinstance(obj, CustomClass):
                assert isinstance(result, CustomClass), f"CustomClass type mismatch at index {i}"
                assert (
                    result.x == obj.x and result.y == obj.y and result.z == obj.z
                ), f"CustomClass value mismatch at index {i}"
            elif isinstance(obj, np.ndarray):
                assert isinstance(result, np.ndarray), f"Numpy array type mismatch at index {i}"
                assert np.array_equal(result, obj), f"Numpy array value mismatch at index {i}: {result} != {obj}"
            else:
                assert result == obj, f"Value mismatch at index {i}: {result} != {obj}"
