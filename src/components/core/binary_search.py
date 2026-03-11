import math
import os

import pandas as pd


FACILITY_FILES = (
    "hospitals.csv",
    "firestations.csv",
    "policestations.csv",
    "drrm.csv",
    "schools.csv",
    "churches.csv",
)

def _base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _to_float_pair(coords):
    if not coords or len(coords) < 2:
        return None
    try:
        return float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return None


def _build_node_lookup(node_map):
    lookup = {}

    if node_map is None:
        node_map = pd.DataFrame()

    if isinstance(node_map, dict):
        for node_id, coords in node_map.items():
            pair = _to_float_pair(coords)
            if pair is not None:
                lookup[str(node_id).strip()] = pair
        return lookup

    if isinstance(node_map, pd.DataFrame) and not node_map.empty:
        df = node_map.copy()
    else:
        nodes_path = os.path.join(_base_dir(), "data", "nodes.csv")
        if not os.path.exists(nodes_path):
            return lookup
        df = pd.read_csv(nodes_path)

    df.columns = df.columns.str.strip()
    required = {"id", "x", "y"}
    if not required.issubset(df.columns):
        return lookup

    df = df[list(required)].dropna()
    for _, row in df.iterrows():
        try:
            lookup[str(row["id"]).strip()] = (float(row["x"]), float(row["y"]))
        except (TypeError, ValueError):
            continue

    return lookup


def _load_registry_from_csv():
    data_dir = os.path.join(_base_dir(), "data")
    registry = {}

    for filename in FACILITY_FILES:
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            continue

        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        if "id" not in df.columns:
            continue

        for _, row in df.iterrows():
            node_id = str(row["id"]).strip()
            if not node_id:
                continue
            registry[node_id] = row.to_dict()

    return registry


def _normalize_registry(master_registry):
    if isinstance(master_registry, dict) and master_registry:
        normalized = {}
        for item_id, data in master_registry.items():
            if not isinstance(data, dict):
                continue
            normalized[str(item_id).strip()] = data.copy()
        if normalized:
            return normalized

    return _load_registry_from_csv()


def _build_sorted_facility_list(master_registry, node_map, accident_coords):
    coords = _to_float_pair(accident_coords)
    if coords is None:
        return []

    ax, ay = coords
    registry = _normalize_registry(master_registry)
    node_lookup = _build_node_lookup(node_map)
    facilities = []

    for item_id, data in registry.items():
        fx_fy = node_lookup.get(str(item_id).strip())
        if fx_fy is None:
            try:
                fx_fy = (float(data["x"]), float(data["y"]))
            except (KeyError, TypeError, ValueError):
                continue

        fx, fy = fx_fy
        facility_copy = data.copy()
        dist = math.sqrt((fx - ax) ** 2 + (fy - ay) ** 2)
        facility_copy["distance"] = round(dist, 2)
        facility_copy["id"] = str(facility_copy.get("id", item_id)).strip()
        facilities.append(facility_copy)

    facilities.sort(key=lambda item: (item.get("distance", float("inf")), item.get("name", "")))
    return facilities


def binary_search(arr, target, key):
    """Perform binary search on a sorted list of dictionaries."""

    left = 0
    right = len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_value = arr[mid].get(key)

        if mid_value is None:
            return -1

        if mid_value == target:
            return mid
        if mid_value < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


def find_by_distance(master_registry, node_map, accident_coords, target_distance):
    """Find a facility by rounded Euclidean distance using binary search."""

    try:
        rounded_target = round(float(target_distance), 2)
    except (TypeError, ValueError):
        return None, []

    sorted_facilities = _build_sorted_facility_list(master_registry, node_map, accident_coords)
    if not sorted_facilities:
        return None, []

    index = binary_search(sorted_facilities, rounded_target, "distance")
    if index == -1:
        return None, sorted_facilities

    while index > 0 and sorted_facilities[index - 1].get("distance") == rounded_target:
        index -= 1

    return sorted_facilities[index], sorted_facilities
