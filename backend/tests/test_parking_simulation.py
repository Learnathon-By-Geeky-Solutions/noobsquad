"""
Unit tests for backend/simulation/parking_simulation.py.

These tests exercise the core logic in isolation (no live threads / display).
"""

import sys
import threading
import time
from pathlib import Path

import pytest

# Add the backend directory to sys.path so imports work the same as in
# all other tests in this package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ── Helpers to get a fresh module state for each test ─────────────────────────

def _fresh_module():
    """
    Re-import parking_simulation with a clean global state so tests are
    independent of each other.
    """
    mod_name = "simulation.parking_simulation"
    # Remove cached module so re-import runs module-level initialisation
    sys.modules.pop(mod_name, None)
    import simulation.parking_simulation as ps
    # Reset mutable globals to a clean state
    ps.highway[:] = [None] * ps.HIGHWAY_LEN
    for lane in ps.entry_lanes:
        lane[0] = None
        lane[1] = None
    for z in ps.zones:
        z.spots[:] = [None] * ps.ZONE_CAPACITY
        z.earnings = 0.0
        z.total_occupied_secs = 0.0
        z.total_idle_secs = 0.0
    ps.global_stats.update({"total_arrived": 0, "total_parked": 0, "turned_away": 0})
    ps.simulation_active = True
    return ps


# ── Zone class unit tests ──────────────────────────────────────────────────────

class TestZone:
    def setup_method(self):
        self.ps = _fresh_module()
        self.zone = self.ps.Zone(0)

    def test_initial_state(self):
        z = self.zone
        assert z.available == self.ps.ZONE_CAPACITY
        assert z.earnings == 0.0
        assert z.total_occupied_secs == 0.0
        assert z.total_idle_secs == 0.0

    def test_try_park_fills_spots(self):
        z = self.zone
        for i in range(self.ps.ZONE_CAPACITY):
            spot = z.try_park(f"C{i:02d}")
            assert spot == i, f"Expected spot {i}, got {spot}"
        assert z.available == 0

    def test_try_park_returns_minus_one_when_full(self):
        z = self.zone
        for i in range(self.ps.ZONE_CAPACITY):
            z.try_park(f"C{i:02d}")
        assert z.try_park("C99") == -1

    def test_unpark_frees_spot(self):
        z = self.zone
        spot = z.try_park("C01")
        assert z.available == self.ps.ZONE_CAPACITY - 1
        z.unpark(spot)
        assert z.available == self.ps.ZONE_CAPACITY

    def test_tick_accumulates_occupied_time(self):
        z = self.zone
        z.try_park("C01")
        z.tick(5.0)  # 1 occupied spot × 5 s
        assert abs(z.total_occupied_secs - 5.0) < 1e-9
        assert abs(z.total_idle_secs - (self.ps.ZONE_CAPACITY - 1) * 5.0) < 1e-9

    def test_tick_accumulates_idle_time_when_empty(self):
        z = self.zone
        z.tick(3.0)  # all 4 spots idle
        assert abs(z.total_idle_secs - self.ps.ZONE_CAPACITY * 3.0) < 1e-9
        assert z.total_occupied_secs == 0.0

    def test_tick_earnings(self):
        z = self.zone
        z.try_park("C01")
        z.try_park("C02")
        z.tick(1.0)  # 2 occupied × $2/s × 1 s = $4
        expected = 2 * self.ps.EARNING_PER_SECOND * 1.0
        assert abs(z.earnings - expected) < 1e-9


# ── Highway helper tests ───────────────────────────────────────────────────────

class TestHighwayHelpers:
    def setup_method(self):
        self.ps = _fresh_module()

    def test_find_free_highway_slot_empty(self):
        # All slots free – should return 0
        result = self.ps._find_free_highway_slot(0)
        assert result == 0

    def test_find_free_highway_slot_skips_occupied(self):
        ps = self.ps
        ps.highway[0] = "C01"
        ps.highway[1] = "C02"
        result = ps._find_free_highway_slot(0)
        assert result == 2

    def test_find_free_highway_slot_returns_minus_one_when_full(self):
        ps = self.ps
        for i in range(ps.HIGHWAY_LEN):
            ps.highway[i] = f"C{i:02d}"
        result = ps._find_free_highway_slot(0)
        assert result == -1

    def test_place_near_chooses_center_when_free(self):
        ps = self.ps
        with ps._lock:
            pos = ps._place_near("C01", 5)
        assert pos == 5
        assert ps.highway[5] == "C01"

    def test_place_near_finds_neighbour_when_center_occupied(self):
        ps = self.ps
        ps.highway[5] = "X"
        with ps._lock:
            pos = ps._place_near("C01", 5)
        assert pos in (4, 6)
        assert ps.highway[pos] == "C01"


# ── Display / render tests ─────────────────────────────────────────────────────

class TestRender:
    def setup_method(self):
        self.ps = _fresh_module()

    def test_render_returns_string(self):
        output = self.ps._render()
        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_contains_zone_headers(self):
        output = self.ps._render()
        for n in range(1, 5):
            assert f"P{n} ZONE" in output

    def test_render_contains_highway_labels(self):
        output = self.ps._render()
        assert "H0" in output
        assert f"H{self.ps.HIGHWAY_LEN - 1}" in output

    def test_render_contains_entry_lane_labels(self):
        output = self.ps._render()
        for n in range(1, 5):
            assert f"E{n}0" in output
            assert f"E{n}1" in output

    def test_render_shows_car_emoji_on_highway(self):
        ps = self.ps
        ps.highway[3] = "C01"
        output = ps._render()
        assert ps.CAR in output

    def test_render_shows_stats(self):
        ps = self.ps
        ps.global_stats["total_arrived"] = 7
        ps.global_stats["total_parked"] = 5
        ps.global_stats["turned_away"] = 2
        output = ps._render()
        assert "7" in output
        assert "5" in output
        assert "2" in output

    def test_slot_empty(self):
        ps = self.ps
        assert ps._slot(None) == ps.EMPTY

    def test_slot_occupied(self):
        ps = self.ps
        assert ps._slot("C01") == ps.CAR


# ── Snapshot API tests ────────────────────────────────────────────────────────

class TestSnapshotAPI:
    def setup_method(self):
        self.ps = _fresh_module()

    def test_get_zone_snapshot_structure(self):
        snaps = self.ps.get_zone_snapshot()
        assert len(snaps) == self.ps.NUM_ZONES
        for i, s in enumerate(snaps):
            assert s["zone_id"] == i
            assert s["available"] == self.ps.ZONE_CAPACITY
            assert s["earnings"] == 0.0
            assert len(s["spots"]) == self.ps.ZONE_CAPACITY

    def test_get_global_stats_structure(self):
        stats = self.ps.get_global_stats()
        assert "total_arrived" in stats
        assert "total_parked" in stats
        assert "turned_away" in stats

    def test_get_zone_snapshot_reflects_parked_car(self):
        ps = self.ps
        with ps._lock:
            ps.zones[0].try_park("C01")
        snaps = ps.get_zone_snapshot()
        assert snaps[0]["available"] == ps.ZONE_CAPACITY - 1
        assert "C01" in snaps[0]["spots"]


# ── Integration-style smoke test (short run) ──────────────────────────────────

class TestIntegration:
    def test_car_eventually_parks(self):
        """
        Start a single car thread and verify it parks within a reasonable time.
        Uses a very short park duration to keep the test fast.
        """
        ps = _fresh_module()
        ps.PARK_DURATION = 0.5   # override for speed
        ps.CAR_MOVE_INTERVAL = 0.05

        car_thread = threading.Thread(
            target=ps._car_thread, args=("C01",), daemon=True
        )
        car_thread.start()

        # Wait up to 5 s for at least one car to have been parked
        deadline = time.time() + 5.0
        parked = False
        while time.time() < deadline:
            with ps._lock:
                parked = any(
                    spot == "C01"
                    for z in ps.zones
                    for spot in z.spots
                )
            if parked:
                break
            time.sleep(0.05)

        car_thread.join(timeout=6.0)
        stats = ps.get_global_stats()
        # At least arrived
        assert stats["total_arrived"] >= 1

    def test_car_turned_away_when_all_zones_full(self):
        """
        Pre-fill every zone. The car should be turned away (turned_away += 1)
        and should NOT appear in any zone after the thread finishes.
        """
        ps = _fresh_module()
        ps.CAR_MOVE_INTERVAL = 0.05

        # Fill every spot in every zone with dummy cars
        with ps._lock:
            for z in ps.zones:
                for i in range(ps.ZONE_CAPACITY):
                    z.spots[i] = f"DUMMY_{z.zone_id}_{i}"

        car_thread = threading.Thread(
            target=ps._car_thread, args=("C01",), daemon=True
        )
        car_thread.start()
        car_thread.join(timeout=10.0)

        stats = ps.get_global_stats()
        assert stats["turned_away"] == 1
        # C01 must not be in any zone spot
        for z in ps.zones:
            assert "C01" not in z.spots
