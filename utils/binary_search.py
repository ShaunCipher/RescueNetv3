def binary_search(arr, target, key):
    left = 0
    right = len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_value = arr[mid][key]

        if mid_value == target:
            return mid

        elif mid_value < target:
            left = mid + 1

        else:
            right = mid - 1

    return -1


if __name__ == "__main__":
    facilities = [
        {"facility_id": 101},
        {"facility_id": 102},
        {"facility_id": 103}
    ]

    print(binary_search(facilities, 102, "facility_id"))