import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.tracker import CentroidTracker


def test_same_face_keeps_same_id_across_frames():
    tracker = CentroidTracker()
    ids_frame1 = tracker.update([(10, 10, 50, 50)])
    ids_frame2 = tracker.update([(12, 11, 52, 51)])  # slight movement
    assert ids_frame1[0] == ids_frame2[0]


def test_new_face_gets_new_id():
    tracker = CentroidTracker()
    ids_frame1 = tracker.update([(10, 10, 50, 50)])
    ids_frame2 = tracker.update([(10, 10, 50, 50), (400, 400, 440, 440)])
    assert ids_frame1[0] in ids_frame2
    assert len(set(ids_frame2)) == 2


def test_track_expires_after_max_misses():
    tracker = CentroidTracker(max_misses=2)
    ids = tracker.update([(10, 10, 50, 50)])
    original_id = ids[0]
    tracker.update([])  # miss 1
    tracker.update([])  # miss 2
    tracker.update([])  # miss 3 -> should be dropped
    new_ids = tracker.update([(10, 10, 50, 50)])
    assert new_ids[0] != original_id
