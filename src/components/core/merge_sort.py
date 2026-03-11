import os
import math
import pandas as pd
import networkx as nx
from time import perf_counter


def merge_sort(arr, key, log_fn=None, label=None):
    """
    Standard Merge Sort Time Measurement Implementation.
    Complexity: O(n log n)

    This implementation measures total runtime on the outermost call only
    and logs the duration via `log_fn` when given, otherwise prints to terminal.

    """
    # --- 0. TIMING SETUP for outermost call ---
    if not hasattr(merge_sort, "_merge_depth"):
        merge_sort._merge_depth = 0

    merge_sort._merge_depth += 1
    if merge_sort._merge_depth == 1:
        merge_sort._start_time = perf_counter()
    # --- 1. BASE CASE ---
    if len(arr) <= 1:
        if merge_sort._merge_depth == 1:
            elapsed = perf_counter() - merge_sort._start_time
            label_text = f" of {label}" if label else ""
            msg = f"merge_sort completed {len(arr)} elements{label_text} in {elapsed:.6f} seconds"
            if log_fn:
                log_fn(msg)
            else:
                print(msg)
            del merge_sort._merge_depth
            del merge_sort._start_time
        else:
            merge_sort._merge_depth -= 1
        return arr

    # --- 2. DIVIDE ---
    mid = len(arr) // 2
    left_half = arr[:mid]
    right_half = arr[mid:]

    # --- 3. CONQUER ---
    sorted_left = merge_sort(left_half, key, log_fn=log_fn)
    sorted_right = merge_sort(right_half, key, log_fn=log_fn)

    # --- 4. COMBINE ---
    merged = merge(sorted_left, sorted_right, key)

    if merge_sort._merge_depth == 1:
        elapsed = perf_counter() - merge_sort._start_time
        label_text = f" of {label}" if label else ""
        msg = f"merge_sort completed {len(arr)} elements{label_text} in {elapsed:.6f} seconds"
        if log_fn:
            log_fn(msg)
        else:
            print(msg)
        del merge_sort._merge_depth
        del merge_sort._start_time
    else:
        merge_sort._merge_depth -= 1

    return merged

def merge(left, right, key):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        # Comparison based on the distance key
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

def sort_facilities_by_distance(master_registry, node_map, accident_coords, edges_df=None, accident_node_id=None, workspace=None):
    """
    Calculates distances (Road or Euclidean) and groups facilities by category.
    Filters out 'Unknown' categories to keep the UI clean.

    If workspace with terminal logger is provided, timing messages are routed to the terminal.
    """
    def _log(message):
        if workspace and hasattr(workspace, 'terminal') and hasattr(workspace.terminal, 'log'):
            workspace.terminal.log(message)
        else:
            print(message)
    # Build NetworkX graph for road distance if edge data is provided
    G = None
    if edges_df is not None:
        G = nx.Graph()
        try:
            # Expects columns: 'from', 'to', 'weight'
            for _, row in edges_df.iterrows():
                G.add_edge(int(row['from']), int(row['to']), weight=float(row['weight']))
        except Exception as e:
            print(f"Warning: Could not build road network graph: {e}")

    ax, ay = accident_coords
    facilities_by_category = {}

    for item_id, data in master_registry.items():
        facility_copy = data.copy()

        # --- FILTER: Remove 'Unknown' or missing categories ---
        category = facility_copy.get('category', 'Unknown')
        if not category or category == 'Unknown':
            continue

        # Get facility coordinates from node_map
        if str(item_id) in node_map:
            fx, fy = node_map[str(item_id)]
        else:
            continue  # Skip if coordinates are missing

        # Distance Calculation
        dist = 0
        if G is not None and accident_node_id is not None:
            try:
                # Calculate Shortest Path distance along the road network
                dist = nx.shortest_path_length(
                    G, 
                    source=int(accident_node_id), 
                    target=int(item_id), 
                    weight='weight'
                )
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                # Fallback to Euclidean distance
                dist = math.hypot(fx - ax, fy - ay)
        else:
            # Direct Euclidean distance
            dist = math.hypot(fx - ax, fy - ay)
        
        facility_copy['distance'] = round(dist, 2)

        # Group by category
        if category not in facilities_by_category:
            facilities_by_category[category] = []
        facilities_by_category[category].append(facility_copy)

    # --- SORT: Apply merge sort to each category ---
    for category in facilities_by_category:
        facilities_by_category[category] = merge_sort(
            facilities_by_category[category],
            key='distance',
            log_fn=_log,
            label=category
        )

    return facilities_by_category