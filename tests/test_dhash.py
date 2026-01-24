import pytest

from tools.comparer.img_comparer.hasher.dhash import DHash


def test_threshold():
    """test threshold setter"""

    hasher = DHash(
        hash_type="dhash",
        threshold=10,
        hash_size=16
    )

    for i in [10, 10.0, "10"]:
        hasher.threshold = i
        assert isinstance(hasher.threshold, int)

def test_hash_size():
    hasher = DHash()

    for i in [16, 16.0, "16", (16, 16)]:
        hasher.hash_size = i
        assert isinstance(hasher.hash_size, int)

