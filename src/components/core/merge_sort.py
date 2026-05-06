import os
import math
import pandas as pd
import networkx as nx
from time import perf_counter
from src.utils.logger import Logger


# ── Facility category → accidents.csv column mapping ──────────────────────────
CATEGORY_TO_NEED_COL = {
    'Hospital':             'need_medical',
    'Medical':              'need_medical',
    'Police Station':       'need_police',
    'Police':               'need_police',
    'Fire Station':         'need_firestation',
    'Fire':                 'need_firestation',
    'Evacuation Facility':  'need_evac',
    'DRRM':                 'need_evac',
    'School':               'need_evac',
    'Church':               'need_evac',
}

# Marker style per category shown on the map
CATEGORY_MARKER_STYLE = {
    'Hospital':             dict(marker='P', color='#27ae60', markersize=10, label='🏥 Hospital'),
    'Medical':              dict(marker='P', color='#27ae60', markersize=10, label='🏥 Medical'),
    'Policestation':       dict(marker='^', color='#2980b9', markersize=10, label='🚔 Police Station'),
    'Police':               dict(marker='^', color='#2980b9', markersize=10, label='🚔 Police'),
    'Firestation':         dict(marker='s', color='#e74c3c', markersize=10, label='🚒 Fire Station'),
    'Fire':                 dict(marker='s', color='#e74c3c', markersize=10, label='🚒 Fire'),
    'Evacuation Facility':  dict(marker='D', color='#000000', markersize=10, label='🏠 Evacuation'),
    'DRRM':                 dict(marker='D', color='#000000', markersize=10, label='🏠 DRRM'),
    'School':               dict(marker='D', color='#f1c40f', markersize=10, label='🏫 School'),
    'Church':               dict(marker='D', color='#e67e22', markersize=10, label='⛪ Church'),
}
DEFAULT_MARKER_STYLE = dict(marker='o', color='#9b59b6', markersize=9, label='Facility')

ACC_FILE = 'data/accidents.csv'


# ─────────────────────────────────────────────────────────────────────────────
#  Core sort helpers
# ─────────────────────────────────────────────────────────────────────────────

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
    left_half  = arr[:mid]
    right_half = arr[mid:]

    # --- 3. CONQUER ---
    sorted_left  = merge_sort(left_half,  key, log_fn=log_fn)
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
        if left[i].get(key, 0) <= right[j].get(key, 0):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  NEW ① — Accident facility-need reader
# ─────────────────────────────────────────────────────────────────────────────

def get_accident_needed_facilities(accident_id=None, accident_name=None, acc_file=ACC_FILE):
    """
    Read accidents.csv and return a dict describing what facilities an
    accident needs, together with its display name.

    Returns
    -------
    {
        'id':            <int>,
        'name':          <str>,
        'severity':      <str>,
        'num_victims':   <int>,
        'needs': {
            'Medical':              True/False,
            'Police Station':       True/False,
            'Fire Station':         True/False,
            'Evacuation Facility':  True/False,
        }
    }
    or None if the accident is not found.

    Example label rendered on the map / UI
    ──────────────────────────────────────
    "fire" needs: 🏥 Medical  🚔 Police  🚒 Fire Station  🏠 Evacuation
    """
    if not os.path.exists(acc_file):
        return None

    df = pd.read_csv(acc_file)

    # Match by id or name
    if accident_id is not None:
        match = df[df['id'] == int(accident_id)]
    elif accident_name is not None:
        match = df[df['name'] == accident_name]
    else:
        return None

    if match.empty:
        return None

    row = match.iloc[0]

    def _truthy(val):
        return str(val).strip().lower() in ('1', '1.0', 'true', 'yes')

    needs = {
        'Medical':             _truthy(row.get('need_medical',     0)),
        'Police Station':      _truthy(row.get('need_police',      0)),
        'Fire Station':        _truthy(row.get('need_firestation', 0)),
        'Evacuation Facility': _truthy(row.get('need_evac',        0)),
    }

    EMOJI = {
        'Medical':             '🏥',
        'Police Station':      '🚔',
        'Fire Station':        '🚒',
        'Evacuation Facility': '🏠',
    }

    needed_labels = [f"{EMOJI[k]} {k}" for k, v in needs.items() if v]
    summary = (
        f"\"{row['name']}\" needs: " + ("  ".join(needed_labels) if needed_labels else "None")
    )

    return {
        'id':          int(row['id']),
        'name':        str(row['name']),
        'severity':    str(row.get('severity', '')),
        'num_victims': int(row.get('num_victims', 0)),
        'needs':       needs,
        'summary':     summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  NEW ② — Slice top-N per category (post-sort)
# ─────────────────────────────────────────────────────────────────────────────

def get_top_n_per_category(facilities_by_category, n=1, accident_id=None, acc_file=ACC_FILE):
    """
    Return only the top-N closest facilities per category, optionally
    filtered to the categories the accident actually needs.

    Parameters
    ----------
    facilities_by_category : dict   Output of sort_facilities_by_distance()
    n                       : int   1 = single closest (on-click), 5 = filtered view
    accident_id             : int   If provided, only include needed categories
    acc_file                : str   Path to accidents.csv

    Returns
    -------
    dict  { category: [facility_dict, ...] }  — at most N entries each
    """
    acc_info = None
    if accident_id is not None:
        acc_info = get_accident_needed_facilities(accident_id=accident_id, acc_file=acc_file)

    result = {}
    for category, facilities in facilities_by_category.items():
        # If we know which facilities the accident needs, skip unneeded categories
        if acc_info is not None:
            col = CATEGORY_TO_NEED_COL.get(category)
            # Map category → generic need key used in acc_info['needs']
            generic = next(
                (need for need, col2 in {
                    'Medical':             'need_medical',
                    'Police Station':      'need_police',
                    'Fire Station':        'need_firestation',
                    'Evacuation Facility': 'need_evac',
                }.items() if col2 == col),
                None
            )
            if generic and not acc_info['needs'].get(generic, False):
                continue  # accident doesn't need this category

        result[category] = facilities[:n]

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  NEW ③ — Map highlight renderer
# ─────────────────────────────────────────────────────────────────────────────

def highlight_facilities_on_map(ax, fig, facilities_by_category, node_map,
                                 existing_plots=None, accident_info=None):
    """
    Plot facility markers on the map for the supplied facilities_by_category
    dict (already sliced to top-1 or top-5 by the caller).

    Parameters
    ----------
    ax                    : matplotlib Axes
    fig                   : matplotlib Figure
    facilities_by_category: dict   { category: [facility_dict, ...] }
    node_map              : dict   { str(id): (x, y) }
    existing_plots        : list   Previously returned plot handles to clear first
    accident_info         : dict   Output of get_accident_needed_facilities()
                                   Used to annotate the accident name + needs on the map.

    Returns
    -------
    list  New plot handles (store these so you can clear them next call)
    """
    # Clear previous facility highlights
    if existing_plots:
        for handle in existing_plots:
            try:
                handle.remove()
            except Exception:
                pass

    new_plots = []

    for category, facilities in facilities_by_category.items():
        style = CATEGORY_MARKER_STYLE.get(category, DEFAULT_MARKER_STYLE)

        for rank, fac in enumerate(facilities):
            fac_id = str(fac.get('id', ''))
            if fac_id not in node_map:
                continue

            x, y = node_map[fac_id]
            dist  = fac.get('distance', '?')
            fname = fac.get('name', fac_id)

            # Plot marker
            (plot,) = ax.plot(
                x, y,
                marker=style['marker'],
                color=style['color'],
                markersize=style['markersize'],
                markeredgecolor='white',
                markeredgewidth=0.8,
                zorder=90,
                linestyle='None',
            )
            new_plots.append(plot)

            # Annotation: "Hospital A\n0.42 km  #1"
            rank_label = f"#{rank + 1}" if len(facilities) > 1 else ""
            ann_text   = f"{fname}\n{dist} km  {rank_label}".strip()
            ann = ax.annotate(
                ann_text,
                xy=(x, y),
                xytext=(6, 6),
                textcoords='offset points',
                fontsize=7,
                color=style['color'],
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, ec=style['color']),
                zorder=91,
            )
            new_plots.append(ann)

    # ── Accident name + needs banner ─────────────────────────────────────
    if accident_info:
        summary = accident_info.get('summary', '')
        if summary:
            # Place a text box in the upper-left axes area
            txt = ax.text(
                0.01, 0.99, summary,
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', fc='#2c2c2c', alpha=0.85, ec='#e74c3c'),
                color='white',
                zorder=95,
            )
            new_plots.append(txt)

    fig.canvas.draw_idle()
    return new_plots


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry — unchanged signature, backward-compatible
# ─────────────────────────────────────────────────────────────────────────────

def sort_facilities_by_distance(master_registry, node_map, accident_coords,
                                 edges_df=None, accident_node_id=None, workspace=None):
    def _log(message):
        if workspace and hasattr(workspace, 'logger'):
            workspace.logger.log(message)
        elif workspace and hasattr(workspace, 'terminal') and hasattr(workspace.terminal, 'log'):
            workspace.terminal.log(message)
        else:
            print(message)

    # Build NetworkX graph for road distance if edge data is provided
    G = None
    if edges_df is not None:
        G = nx.Graph()
        try:
            for _, row in edges_df.iterrows():
                G.add_edge(int(row['from']), int(row['to']), weight=float(row['weight']))
        except Exception as e:
            print(f"Warning: Could not build road network graph: {e}")

    ax, ay = accident_coords
    facilities_by_category = {}

    for item_id, data in master_registry.items():
        facility_copy = data.copy()

        category = facility_copy.get('category', 'Unknown')
        if not category or category == 'Unknown':
            continue

        if str(item_id) in node_map:
            fx, fy = node_map[str(item_id)]
        else:
            continue

        dist = 0
        if G is not None and accident_node_id is not None:
            try:
                dist = nx.shortest_path_length(
                    G,
                    source=int(accident_node_id),
                    target=int(item_id),
                    weight='weight'
                )
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                dist = math.hypot(fx - ax, fy - ay)
        else:
            dist = math.hypot(fx - ax, fy - ay)

        facility_copy['distance'] = round(dist, 2)

        if category not in facilities_by_category:
            facilities_by_category[category] = []
        facilities_by_category[category].append(facility_copy)

    # Apply merge sort to each category
    for category in facilities_by_category:
        facilities_by_category[category] = merge_sort(
            facilities_by_category[category],
            key='distance',
            log_fn=_log,
            label=category
        )

    return facilities_by_category