#!/usr/bin/env python3
"""
Car Parking Simulation
======================

Terminal layout (matches original template):

    [ P1 ZONE ]        [ P2 ZONE ]        [ P3 ZONE ]        [ P4 ZONE ]

   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ Earn: $X.X  │   │ Earn: $X.X  │   │ Earn: $X.X  │   │ Earn: $X.X  │
   │ Used: X.Xs  │   │ Used: X.Xs  │   │ Used: X.Xs  │   │ Used: X.Xs  │
   │ Idle: X.Xs  │   │ Idle: X.Xs  │   │ Idle: X.Xs  │   │ Idle: X.Xs  │
   │ Free: X/4   │   │ Free: X/4   │   │ Free: X/4   │   │ Free: X/4   │
   ├─────────────┤   ├─────────────┤   ├─────────────┤   ├─────────────┤
   │  P1_3 [🚗]  │   │  P2_3 [  ]  │   │  P3_3 [  ]  │   │  P4_3 [  ]  │
   │  P1_2 [  ]  │   │  P2_2 [🚗]  │   │  P3_2 [  ]  │   │  P4_2 [  ]  │
   │  P1_1 [  ]  │   │  P2_1 [  ]  │   │  P3_1 [🚗]  │   │  P4_1 [  ]  │
   │  P1_0 [  ]  │   │  P2_0 [  ]  │   │  P3_0 [  ]  │   │  P4_0 [  ]  │

        E11 🚗          E21               E31               E41
        E10               E20               E30               E40

--------    -------------     -------------     --------------   -----------------

 🚗  🚗   H2  H3  H4  H5  H6  H7  H8  H9  H10 H11 H12 H13 H14 H15 H16

----------------------------------------------------------------------------------

Cars enter at H0, randomly choose a zone, park for 10 s, then exit.
All zones full → car drives the entire highway and leaves.
"""

import itertools
import os
import random
import threading
import time
from typing import List, Optional

# ── Constants ──────────────────────────────────────────────────────────────────
NUM_ZONES = 4
ZONE_CAPACITY = 4          # spots per zone
HIGHWAY_LEN = 17           # H0 … H16
PARK_DURATION = 10.0       # seconds a car stays in its spot
SPAWN_INTERVAL_MIN = 1.5   # seconds between arrivals (min)
SPAWN_INTERVAL_MAX = 3.0   # seconds between arrivals (max)
EARNING_PER_SECOND = 2.0   # $ per second per occupied spot
DISPLAY_INTERVAL = 0.25    # seconds between screen redraws
CAR_MOVE_INTERVAL = 0.35   # seconds per highway/entry step

CAR = "🚗"    # car emoji (occupies 2 terminal columns)
EMPTY = "  "  # 2 columns – matches emoji width

# Highway index beneath each zone's entry ramp
ZONE_H_POS = [2, 6, 10, 14]

# ── Shared state ───────────────────────────────────────────────────────────────
_lock = threading.Lock()
_car_counter = itertools.count(1)

# highway[i]         – None or car-id string at position H i
highway: List[Optional[str]] = [None] * HIGHWAY_LEN

# entry_lanes[z][0]  – E_z0  (highway-side ramp)
# entry_lanes[z][1]  – E_z1  (zone-side ramp)
entry_lanes: List[List[Optional[str]]] = [[None, None] for _ in range(NUM_ZONES)]

simulation_active: bool = True


class Zone:
    """One parking zone with ZONE_CAPACITY spots and running statistics."""

    def __init__(self, zone_id: int) -> None:
        self.zone_id = zone_id
        self.spots: List[Optional[str]] = [None] * ZONE_CAPACITY
        self.earnings: float = 0.0
        self.total_occupied_secs: float = 0.0
        self.total_idle_secs: float = 0.0

    # Call periodically (while holding _lock) to advance stats by dt seconds.
    def tick(self, dt: float) -> None:
        occupied = sum(1 for s in self.spots if s is not None)
        idle = ZONE_CAPACITY - occupied
        self.total_occupied_secs += occupied * dt
        self.total_idle_secs += idle * dt
        self.earnings += occupied * EARNING_PER_SECOND * dt

    @property
    def available(self) -> int:
        return self.spots.count(None)

    def try_park(self, car_id: str) -> int:
        """Try to park car_id; return spot index or -1 if full."""
        for i, s in enumerate(self.spots):
            if s is None:
                self.spots[i] = car_id
                return i
        return -1

    def unpark(self, spot_idx: int) -> None:
        self.spots[spot_idx] = None


zones: List[Zone] = [Zone(i) for i in range(NUM_ZONES)]

global_stats = {
    "total_arrived": 0,
    "total_parked": 0,
    "turned_away": 0,
}


# ── Stats ticker ───────────────────────────────────────────────────────────────
def _stats_ticker() -> None:
    """Advance zone earnings / time stats every 100 ms."""
    prev = time.time()
    while simulation_active:
        time.sleep(0.1)
        now = time.time()
        dt = now - prev
        prev = now
        with _lock:
            for z in zones:
                z.tick(dt)


# ── Car lifecycle ──────────────────────────────────────────────────────────────
def _car_thread(car_id: str) -> None:
    """
    Full lifecycle of one car:
      1. Appear at the first free highway slot.
      2. Drive toward preferred zones (random order).
      3. Enter zone → park for PARK_DURATION seconds → exit zone.
      4. Drive off the end of the highway.
    """
    # ── Step 1: enter highway ─────────────────────────────────────────────────
    with _lock:
        current_h = _find_free_highway_slot(0)
        if current_h == -1:
            return  # Highway completely full – give up
        highway[current_h] = car_id
        global_stats["total_arrived"] += 1

    preferred = list(range(NUM_ZONES))
    random.shuffle(preferred)
    parked_zone = -1
    parked_spot = -1

    # ── Step 2: try each preferred zone in random order ───────────────────────
    for target_zone in preferred:
        target_h = ZONE_H_POS[target_zone]

        # Drive toward the zone's highway position
        reached = _drive_to(car_id, current_h, target_h)
        if not reached:
            continue
        current_h = target_h

        # Attempt to enter the zone through its entry ramp
        entered, parked_spot = _enter_and_park(car_id, current_h, target_zone)
        if entered:
            parked_zone = target_zone
            with _lock:
                global_stats["total_parked"] += 1
            break

    # ── Step 3: park, then exit ───────────────────────────────────────────────
    if parked_zone != -1:
        time.sleep(PARK_DURATION)
        current_h = _exit_zone(car_id, parked_zone, parked_spot)
    else:
        with _lock:
            global_stats["turned_away"] += 1

    # ── Step 4: drive off the end of the highway ──────────────────────────────
    _drive_to_exit(car_id, current_h)


def _find_free_highway_slot(start: int) -> int:
    """Return the first free slot at or after *start*, or -1 if none."""
    for h in range(start, HIGHWAY_LEN):
        if highway[h] is None:
            return h
    return -1


def _drive_to(car_id: str, from_h: int, to_h: int) -> bool:
    """
    Move car_id from *from_h* toward *to_h* one step at a time.
    Return True when car reaches *to_h*, False if already past it.
    """
    current = from_h
    if current > to_h:
        return False  # Already past this zone

    while current < to_h:
        time.sleep(CAR_MOVE_INTERVAL)
        with _lock:
            next_h = current + 1
            if next_h < HIGHWAY_LEN and highway[next_h] is None:
                highway[current] = None
                highway[next_h] = car_id
                current = next_h
            # If next slot is blocked we wait in place (spin next iteration)
    return current == to_h


def _enter_and_park(car_id: str, h_pos: int, zone_idx: int):
    """
    Try to move car from highway into *zone_idx*.
    Returns (True, spot_idx) on success, (False, -1) otherwise.
    """
    # Move into E_z0
    with _lock:
        z = zones[zone_idx]
        if z.available == 0 or entry_lanes[zone_idx][0] is not None:
            return False, -1
        highway[h_pos] = None
        entry_lanes[zone_idx][0] = car_id

    time.sleep(CAR_MOVE_INTERVAL)

    # Advance to E_z1
    with _lock:
        if entry_lanes[zone_idx][1] is not None:
            # Lane blocked – retreat to highway
            highway[h_pos] = car_id
            entry_lanes[zone_idx][0] = None
            return False, -1
        entry_lanes[zone_idx][0] = None
        entry_lanes[zone_idx][1] = car_id

    time.sleep(CAR_MOVE_INTERVAL)

    # Enter a parking spot
    with _lock:
        spot = zones[zone_idx].try_park(car_id)
        if spot == -1:
            # Race condition: zone filled between checks – retreat
            highway[h_pos] = car_id
            entry_lanes[zone_idx][1] = None
            return False, -1
        entry_lanes[zone_idx][1] = None

    return True, spot


def _exit_zone(car_id: str, zone_idx: int, spot_idx: int) -> int:
    """
    Remove car from its spot, traverse exit ramp, return to highway.
    Returns the highway position where the car ends up.
    """
    with _lock:
        zones[zone_idx].unpark(spot_idx)
        entry_lanes[zone_idx][1] = car_id

    time.sleep(CAR_MOVE_INTERVAL)

    with _lock:
        entry_lanes[zone_idx][1] = None
        entry_lanes[zone_idx][0] = car_id

    time.sleep(CAR_MOVE_INTERVAL)

    target_h = ZONE_H_POS[zone_idx]
    with _lock:
        entry_lanes[zone_idx][0] = None
        # Place the car back at the nearest free highway spot
        landed = _place_near(car_id, target_h)

    return landed


def _place_near(car_id: str, center: int) -> int:
    """
    Park car_id at the highway slot nearest to *center*.
    Must be called while holding _lock.
    Returns the chosen position.
    """
    for offset in range(HIGHWAY_LEN):
        for h in (center - offset, center + offset):
            if 0 <= h < HIGHWAY_LEN and highway[h] is None:
                highway[h] = car_id
                return h
    # Fallback (shouldn't happen in normal operation)
    highway[center] = car_id
    return center


def _drive_to_exit(car_id: str, from_h: int) -> None:
    """Drive car from *from_h* to the end of the highway and remove it."""
    current = from_h
    while True:
        time.sleep(CAR_MOVE_INTERVAL)
        with _lock:
            if current >= HIGHWAY_LEN - 1:
                highway[current] = None
                break
            next_h = current + 1
            if highway[next_h] is None:
                highway[current] = None
                highway[next_h] = car_id
                current = next_h


# ── Car spawner ────────────────────────────────────────────────────────────────
def _spawner_thread() -> None:
    """Spawn a new car thread every SPAWN_INTERVAL_MIN–MAX seconds."""
    while simulation_active:
        delay = random.uniform(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_MAX)
        time.sleep(delay)
        if not simulation_active:
            break
        car_id = f"C{next(_car_counter):02d}"
        t = threading.Thread(target=_car_thread, args=(car_id,), daemon=True)
        t.start()


# ── Display ────────────────────────────────────────────────────────────────────

def _slot(car_id: Optional[str]) -> str:
    """Return a 2-column representation: car emoji or two spaces."""
    return CAR if car_id else EMPTY


def _spot_label(zone_num: int, spot: int, car_id: Optional[str]) -> str:
    """
    Format a parking spot row for inside a zone box.
    Inner width = 13 characters (between the two │ borders).
    Emoji occupies 2 terminal columns, so we compensate with 1 fewer space.
    """
    label = f"P{zone_num}_{spot}"
    if car_id:
        # "  P1_0 [🚗] " → label(4) + " [" + emoji(2-wide) + "] " = 4+4+2-1 pad
        return f"  {label} [{CAR}]  "
    else:
        return f"  {label} [  ]  "


def _render() -> str:
    """Build the full terminal frame as a string."""
    with _lock:
        hw = list(highway)
        el = [list(lane) for lane in entry_lanes]
        zdata = [
            {
                "earnings": z.earnings,
                "used": z.total_occupied_secs,
                "idle": z.total_idle_secs,
                "available": z.available,
                "spots": list(z.spots),
                "num": z.zone_id + 1,
            }
            for z in zones
        ]
        snap = dict(global_stats)

    lines: List[str] = []

    # ── Zone headers ──────────────────────────────────────────────────────────
    lines.append(
        "   [ P1 ZONE ]        [ P2 ZONE ]        [ P3 ZONE ]        [ P4 ZONE ]"
    )
    lines.append("")

    # ── Stat boxes ────────────────────────────────────────────────────────────
    BORDER_TOP = (
        "   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐"
    )
    BORDER_MID = (
        "   ├─────────────┤   ├─────────────┤   ├─────────────┤   ├─────────────┤"
    )

    def stat_row(values: List[str]) -> str:
        cells = [f"│ {v:<11} │" for v in values]
        return "   " + "   ".join(cells)

    lines.append(BORDER_TOP)
    # Each value must be ≤ 11 chars so that "│ {v:<11} │" is exactly 15 chars
    # matching the ┌─────────────┐ (13 inner dashes + 2 corners = 15).
    lines.append(stat_row([f"Earn:${z['earnings']:5.1f}" for z in zdata]))  # 11
    lines.append(stat_row([f"Used:{z['used']:5.1f}s" for z in zdata]))      # 11
    lines.append(stat_row([f"Idle:{z['idle']:5.1f}s" for z in zdata]))      # 11
    lines.append(stat_row([f"Free:{z['available']}/4" for z in zdata]))     #  8
    lines.append(BORDER_MID)

    # ── Parking spots (top = index 3, bottom = index 0) ───────────────────────
    for row in (3, 2, 1, 0):
        cells = []
        for z in zdata:
            label = _spot_label(z["num"], row, z["spots"][row])
            cells.append(f"│{label}│")
        lines.append("   " + "   ".join(cells))

    lines.append("")

    # ── Entry / exit lanes ────────────────────────────────────────────────────
    # E_z1 row then E_z0 row, positioned to align with zone columns
    e1_parts = []
    e0_parts = []
    for zi in range(NUM_ZONES):
        e1_parts.append(f"E{zi+1}1[{_slot(el[zi][1])}]")
        e0_parts.append(f"E{zi+1}0[{_slot(el[zi][0])}]")

    e1_line = "        " + "               ".join(e1_parts)
    e0_line = "        " + "               ".join(e0_parts)
    lines.append(e1_line)
    lines.append(e0_line)

    lines.append("")
    lines.append(
        "--------    -------------     -------------     --------------   -----------------"
    )
    lines.append("")

    # ── Highway ───────────────────────────────────────────────────────────────
    hw_cars = " ".join(_slot(hw[i]) for i in range(HIGHWAY_LEN))
    hw_labels = " ".join(f"H{i:<2}" for i in range(HIGHWAY_LEN))
    lines.append(f" {hw_cars}")
    lines.append(f" {hw_labels}")
    lines.append("-" * 78)
    lines.append("")

    # ── Global stats ──────────────────────────────────────────────────────────
    lines.append(
        f" Arrived: {snap['total_arrived']:4d}   "
        f"Parked: {snap['total_parked']:4d}   "
        f"Turned away: {snap['turned_away']:4d}"
    )
    lines.append("")
    lines.append(" Press Ctrl+C to stop the simulation.")

    return "\n".join(lines)


def _display_thread() -> None:
    """Continuously clear the screen and redraw the simulation."""
    while simulation_active:
        _clear_screen()
        print(_render())
        time.sleep(DISPLAY_INTERVAL)


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


# ── Public API used by tests ───────────────────────────────────────────────────

def get_zone_snapshot() -> List[dict]:
    """Thread-safe snapshot of all zone states (for testing / inspection)."""
    with _lock:
        return [
            {
                "zone_id": z.zone_id,
                "available": z.available,
                "earnings": z.earnings,
                "total_occupied_secs": z.total_occupied_secs,
                "total_idle_secs": z.total_idle_secs,
                "spots": list(z.spots),
            }
            for z in zones
        ]


def get_global_stats() -> dict:
    """Thread-safe copy of the global arrival/parking stats."""
    with _lock:
        return dict(global_stats)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    global simulation_active

    daemon_threads = [
        threading.Thread(target=_stats_ticker, daemon=True, name="stats-ticker"),
        threading.Thread(target=_spawner_thread, daemon=True, name="spawner"),
        threading.Thread(target=_display_thread, daemon=True, name="display"),
    ]
    for t in daemon_threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        simulation_active = False
        time.sleep(DISPLAY_INTERVAL * 2)  # let display thread finish last frame
        _clear_screen()
        print("\n=== Simulation Stopped ===\n")
        print(_render())


if __name__ == "__main__":
    main()
