import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.liveness import eye_aspect_ratio, texture_score, moire_energy, LivenessTracker
from config import Config


def test_eye_aspect_ratio_open_vs_closed():
    # Open eye: taller vertical span relative to width -> higher EAR
    open_eye = np.array([[0, 0], [1, 2], [2, 2], [4, 0], [2, -2], [1, -2]], dtype=float)
    closed_eye = np.array([[0, 0], [1, 0.2], [2, 0.2], [4, 0], [2, -0.2], [1, -0.2]], dtype=float)

    ear_open = eye_aspect_ratio(open_eye)
    ear_closed = eye_aspect_ratio(closed_eye)
    assert ear_open > ear_closed


def test_texture_score_flat_image_is_low():
    flat = np.full((100, 100), 128, dtype=np.uint8)
    noisy = (np.random.default_rng(0).random((100, 100)) * 255).astype(np.uint8)
    assert texture_score(flat) < texture_score(noisy)


def test_moire_energy_runs_and_bounded():
    img = (np.random.default_rng(1).random((100, 100)) * 255).astype(np.uint8)
    e = moire_energy(img)
    assert 0.0 <= e <= 1.0


def test_liveness_tracker_blink_counting():
    tracker = LivenessTracker()
    # simulate: open, open, closed, closed, open -> should register exactly one blink
    for ear in [0.30, 0.29, 0.10, 0.09, 0.31]:
        tracker.update_ear(ear)
    assert tracker.blink_count == 1


def test_liveness_tracker_no_blink_below_consec_threshold():
    tracker = LivenessTracker()
    # single closed frame shouldn't count (needs EAR_CONSEC_FRAMES consecutive)
    for ear in [0.30, 0.10, 0.30]:
        tracker.update_ear(ear)
    assert tracker.blink_count == 0


def test_liveness_pass_requires_blink_and_spatial_agreement():
    tracker = LivenessTracker()
    for ear in [0.30, 0.29, 0.10, 0.09, 0.31]:
        tracker.update_ear(ear)
    for _ in range(5):
        tracker.texture_votes.append(True)
        tracker.moire_votes.append(True)
    is_live, evidence = tracker.is_live()
    assert is_live is True
    assert evidence["blinked"] is True
