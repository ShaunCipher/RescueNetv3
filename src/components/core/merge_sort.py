def merge_sort(arr, key):
    """
    Standard Merge Sort Implementation
    Requirement: Divide, Conquer, Combine
    """
    # --- 1. BASE CASE ---
    if len(arr) <= 1:
        return arr

    # --- 2. DIVIDE ---
    mid = len(arr) // 2
    left_half = arr[:mid]
    right_half = arr[mid:]

    # --- 3. CONQUER ---
    # Recursively sort both halves
    sorted_left = merge_sort(left_half, key)
    sorted_right = merge_sort(right_half, key)

    # --- 4. COMBINE ---
    return merge(sorted_left, sorted_right, key)

def merge(left, right, key):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        # Comparison based on the chosen metric
        if left[i].get(key, 0) <= right[j].get(key, 0):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Combine remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def sort_facilities_by_distance(master_registry, node_map, accident_coords):
    """
    Sorts facilities by distance from accident location using merge sort.
    Groups facilities by category and sorts each category by distance.

    Args:
        master_registry: Dictionary of facility data
        node_map: Dictionary mapping node IDs to coordinates
        accident_coords: Tuple (x, y) of accident location

    Returns:
        Dictionary with categories as keys and sorted facility lists as values
    """
    import math

    ax, ay = accident_coords
    facilities_by_category = {}

    print(f"DEBUG: Available Facilities: {len(master_registry)}")

    for item_id, data in master_registry.items():
        facility_copy = data.copy()

        # Get facility coordinates from node_map
        if str(item_id) in node_map:
            fx, fy = node_map[str(item_id)]
        else:
            continue  # Skip if coordinates not found

        # Calculate Euclidean Distance
        dist = math.sqrt((fx - ax)**2 + (fy - ay)**2)
        facility_copy['distance'] = round(dist, 2)

        # Group by category
        category = facility_copy.get('category', 'Unknown')
        if category not in facilities_by_category:
            facilities_by_category[category] = []
        facilities_by_category[category].append(facility_copy)

    # Sort each category by distance
    for category in facilities_by_category:
        facilities_by_category[category] = merge_sort(facilities_by_category[category], key='distance')

    return facilities_by_category