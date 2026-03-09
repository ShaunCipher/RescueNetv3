"""Binary search utilities for facility lookup.

This module provides a binary search implementation tailored to the project's
facility data structure (a list of dicts with a "distance" key).

It also includes a helper to compute distances the same way as our merge_sort
module does (based on a given accident location).
"""

from .merge_sort import sort_facilities_by_distance


def binary_search(arr, target, key):
    """Perform binary search on a sorted list of dictionaries.

    Args:
        arr: List of dicts sorted by `key`.
        target: The value to search for.
        key: The dict key to compare against.

    Returns:
        The index of the matching item in `arr`, or -1 if not found.
    """

    left = 0
    right = len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_value = arr[mid].get(key)

        if mid_value is None:
            return -1

        if mid_value == target:
            return mid
        elif mid_value < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


def find_by_distance(master_registry, node_map, accident_coords, target_distance):
    """Find a facility by distance using binary search.

    This uses an internally sorted list (by distance) derived from the master
    registry and the given accident coordinates.

    Args:
        master_registry: Dictionary of facility data.
        node_map: Dict mapping node IDs (as str) to (x,y) coordinates.
        accident_coords: Tuple (x, y) representing the reference point.
        target_distance: Distance to search for.

    Returns:
        (facility_dict, sorted_list) where facility_dict is the matching facility
        or None if not found; sorted_list is the full sorted list by distance.
    """

    # Sort all facilities by their distance to the accident coordinates.
    sorted_by_category = sort_facilities_by_distance(master_registry, node_map, accident_coords)

    # Flatten into a single sorted list (preserving per-category ordering)
    sorted_flat = []
    for cat in sorted(sorted_by_category.keys()):
        sorted_flat.extend(sorted_by_category[cat])

    index = binary_search(sorted_flat, target_distance, "distance")
    if index == -1:
        return None, sorted_flat

    return sorted_flat[index], sorted_flat
