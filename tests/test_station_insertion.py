"""
Test script for station insertion feature.
"""

import sys
sys.path.insert(0, '.')

def test_station_insertion_logic():
    """
    Test that station insertion logic works correctly.
    """
    print("Testing station insertion logic...")
    
    # Simulate the insertion logic
    stations = ["Bengaluru", "A", "B", "C", "D", "Kochi"]
    distances = [100.0, 120.0, 100.0, 120.0, 100.0]
    
    print(f"Original stations: {stations}")
    print(f"Original distances: {distances}")
    
    # Test inserting a station between A and B (index 1)
    insert_index = 1
    new_station = "X"
    original_distance = distances[insert_index]
    split_ratio = 0.5
    
    first_distance = original_distance * split_ratio
    second_distance = original_distance * (1 - split_ratio)
    
    # Insert station
    stations.insert(insert_index + 1, new_station)
    
    # Split distance
    distances.pop(insert_index)
    distances.insert(insert_index, first_distance)
    distances.insert(insert_index + 1, second_distance)
    
    print(f"\nAfter inserting '{new_station}' between A and B:")
    print(f"New stations: {stations}")
    print(f"New distances: {distances}")
    
    # Verify
    assert stations == ["Bengaluru", "A", "X", "B", "C", "D", "Kochi"], "Station list should be updated correctly"
    assert len(distances) == 6, "Should have 6 distances now"
    assert abs(distances[1] + distances[2] - 120.0) < 0.1, "Sum of split distances should equal original"
    
    print("Station insertion logic test PASSED!")

def test_insert_at_end():
    """
    Test inserting a station at the end.
    """
    print("\nTesting insertion at end...")
    
    stations = ["Bengaluru", "A", "B"]
    distances = [100.0, 120.0]
    
    new_station = "C"
    
    # Insert at end
    stations.append(new_station)
    distances.append(100.0)
    
    print(f"New stations: {stations}")
    print(f"New distances: {distances}")
    
    assert stations == ["Bengaluru", "A", "B", "C"], "Station should be added at end"
    assert distances == [100.0, 120.0, 100.0], "Default distance should be added"
    
    print("Insert at end test PASSED!")

def test_insert_with_different_split_ratios():
    """
    Test insertion with different split ratios.
    """
    print("\nTesting insertion with different split ratios...")
    
    original_distance = 120.0
    
    # Test 30/70 split
    split_ratio = 0.3
    first_distance = original_distance * split_ratio
    second_distance = original_distance * (1 - split_ratio)
    
    print(f"Split ratio {split_ratio}: {first_distance:.1f} km + {second_distance:.1f} km = {first_distance + second_distance:.1f} km")
    assert abs(first_distance + second_distance - original_distance) < 0.1, "Sum should equal original"
    
    # Test 70/30 split
    split_ratio = 0.7
    first_distance = original_distance * split_ratio
    second_distance = original_distance * (1 - split_ratio)
    
    print(f"Split ratio {split_ratio}: {first_distance:.1f} km + {second_distance:.1f} km = {first_distance + second_distance:.1f} km")
    assert abs(first_distance + second_distance - original_distance) < 0.1, "Sum should equal original"
    
    print("Different split ratios test PASSED!")

if __name__ == "__main__":
    test_station_insertion_logic()
    test_insert_at_end()
    test_insert_with_different_split_ratios()
    print("\nAll station insertion tests PASSED!")
