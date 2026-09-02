import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.face_engine import FaceMatchIndex


def test_index_finds_exact_match():
    idx = FaceMatchIndex(dim=4)
    vectors = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
    ], dtype=np.float32)
    idx.rebuild(vectors, employee_ids=[101, 102, 103])

    results = idx.search(np.array([1, 0, 0, 0], dtype=np.float32), top_k=1)
    assert results[0][0] == 101
    assert results[0][1] > 0.99


def test_index_orders_by_similarity():
    idx = FaceMatchIndex(dim=2)
    vectors = np.array([
        [1, 0],
        [0.7, 0.7],
    ], dtype=np.float32)
    idx.rebuild(vectors, employee_ids=[1, 2])

    results = idx.search(np.array([0.9, 0.1], dtype=np.float32), top_k=2)
    assert results[0][0] == 1  # closer to [1,0]
    assert results[0][1] >= results[1][1]


def test_index_empty_returns_empty():
    idx = FaceMatchIndex(dim=4)
    idx.rebuild(np.zeros((0, 4), dtype=np.float32), [])
    assert idx.search(np.array([1, 0, 0, 0], dtype=np.float32)) == []
