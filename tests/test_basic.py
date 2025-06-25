import hyperq


class TestHyperQBasicOperations:
    """Test basic HyperQ operations."""

    def test_single_item(self):
        """Test putting and getting a single item."""
        q = hyperq.HyperQ(1024, "test_single")
        test_item = "test_string"
        q.put(test_item)
        result = q.get()
        assert result == test_item

    def test_multiple_items(self):
        """Test putting and getting multiple items in order."""
        q = hyperq.HyperQ(1024, "test_multiple")
        items = [1, 2, 3, 4, 5]

        for item in items:
            q.put(item)

        for expected_item in items:
            result = q.get()
            assert result == expected_item


class TestBytesHyperQBasicOperations:
    """Test basic BytesHyperQ operations."""

    def test_single_bytes_item(self):
        """Test putting and getting a single bytes item."""
        q = hyperq.BytesHyperQ(1024, "test_bytes_single")
        test_item = b"test_bytes_string"
        q.put(test_item)
        result = q.get()
        assert result == test_item

    def test_multiple_bytes_items(self):
        """Test putting and getting multiple bytes items in order."""
        q = hyperq.BytesHyperQ(1024, "test_bytes_multiple")
        items = [b"item1", b"item2", b"item3", b"item4", b"item5"]

        for item in items:
            q.put(item)

        for expected_item in items:
            result = q.get()
            assert result == expected_item
