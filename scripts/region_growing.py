import numpy as np
from queue import Queue
import random

def calculate_threshold(volume, k=1.0):
    """
    Calculate threshold using statistical method.
    
    Args:
    - volume (np.ndarray): 4D array representing the volume (depth, height, width, channels).
    - k (float): Multiplication factor for the standard deviation.
    
    Returns:
    - float: Threshold value.
    """
    # Flatten the volume and calculate differences between adjacent voxels
    depth, height, width, channels = volume.shape
    diffs = []
    
    directions = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]
    
    for z in range(depth):
        for y in range(height):
            for x in range(width):
                for dz, dy, dx in directions:
                    nz, ny, nx = z + dz, y + dy, x + dx
                    if 0 <= nz < depth and 0 <= ny < height and 0 <= nx < width:
                        diff = np.linalg.norm(volume[z, y, x] - volume[nz, ny, nx])
                        diffs.append(diff)
    
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs)
    
    return mean_diff + k * std_diff

def region_growing_3d_multivariate(volume, k=1.0, min_region_size=10):
    """
    Perform region growing on a 3D multivariate volume with random seed initialization and iterative growth.
    
    Args:
    - volume (np.ndarray): 4D array representing the volume (depth, height, width, channels).
    - k (float): Multiplication factor for threshold calculation.
    - min_region_size (int): Minimum size for a region to not be considered an outlier.
    
    Returns:
    - np.ndarray: 3D array with labeled segmented regions.
    """
    # Get the dimensions of the volume
    depth, height, width, channels = volume.shape
    
    # Create a labeled volume to mark the segmented regions
    labeled_volume = np.zeros((depth, height, width), dtype=np.int32)

    print("Calculating Threshold")
    
    # Calculate the threshold using a statistical method
    threshold = calculate_threshold(volume, k)

    print("Threshold:", threshold)
    
    # Directions for 26-connectivity (adjacent voxels including edges and corners)
    directions = [(-1, -1, -1), (-1, -1, 0), (-1, -1, 1),
                  (-1, 0, -1), (-1, 0, 0), (-1, 0, 1),
                  (-1, 1, -1), (-1, 1, 0), (-1, 1, 1),
                  (0, -1, -1), (0, -1, 0), (0, -1, 1),
                  (0, 0, -1), (0, 0, 1),
                  (0, 1, -1), (0, 1, 0), (0, 1, 1),
                  (1, -1, -1), (1, -1, 0), (1, -1, 1),
                  (1, 0, -1), (1, 0, 0), (1, 0, 1),
                  (1, 1, -1), (1, 1, 0), (1, 1, 1)]
    
    region_label = 1
    voxels_to_process = set((z, y, x) for z in range(depth) for y in range(height) for x in range(width))
    
    while voxels_to_process:
        seed = random.choice(list(voxels_to_process))
        queue = Queue()
        queue.put(seed)

        print("Seed:", seed)
        
        seed_value = volume[seed]
        region_voxels = []
        
        while not queue.empty():
            z, y, x = queue.get()
            
            if labeled_volume[z, y, x] != 0:
                continue
            
            labeled_volume[z, y, x] = region_label
            region_voxels.append((z, y, x))
            voxels_to_process.discard((z, y, x))
            
            for dz, dy, dx in directions:
                nz, ny, nx = z + dz, y + dy, x + dx
                
                if 0 <= nz < depth and 0 <= ny < height and 0 <= nx < width:
                    if labeled_volume[nz, ny, nx] == 0:
                        neighbor_value = volume[nz, ny, nx]
                        distance = np.linalg.norm(seed_value - neighbor_value)
                        
                        if distance <= threshold:
                            queue.put((nz, ny, nx))
        
        if len(region_voxels) < min_region_size:
            for z, y, x in region_voxels:
                labeled_volume[z, y, x] = -1  # Label as outlier
        else:
            region_label += 1
    
    return labeled_volume

def calculate_threshold_2d(volume, k=1.0):
    """
    Calculate threshold using statistical method for 2D data.
    
    Args:
    - volume (np.ndarray): 3D array representing the volume (height, width, channels).
    - k (float): Multiplication factor for the standard deviation.
    
    Returns:
    - float: Threshold value.
    """
    # Flatten the volume and calculate differences between adjacent voxels
    height, width, channels = volume.shape
    diffs = []
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for y in range(height):
        for x in range(width):
            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    diff = np.linalg.norm(volume[y, x] - volume[ny, nx])
                    diffs.append(diff)
    
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs)
    
    return mean_diff + k * std_diff

def region_growing_2d_multivariate(volume, k=1.0, min_region_size=10):
    """
    Perform region growing on a 2D multivariate volume with random seed initialization and iterative growth.
    
    Args:
    - volume (np.ndarray): 3D array representing the volume (height, width, channels).
    - k (float): Multiplication factor for threshold calculation.
    - min_region_size (int): Minimum size for a region to not be considered an outlier.
    
    Returns:
    - np.ndarray: 2D array with labeled segmented regions.
    """
    # Get the dimensions of the volume
    height, width, channels = volume.shape
    
    # Create a labeled volume to mark the segmented regions
    labeled_volume = np.zeros((height, width), dtype=np.int32)

    print("Calculating Threshold")
    
    # Calculate the threshold using a statistical method
    threshold = calculate_threshold_2d(volume, k)

    print("Threshold:", threshold)
    
    # Directions for 8-connectivity (adjacent voxels including edges and corners)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1), (0, 1),
                  (1, -1), (1, 0), (1, 1)]
    
    region_label = 1
    voxels_to_process = set((y, x) for y in range(height) for x in range(width))
    
    while voxels_to_process:
        seed = random.choice(list(voxels_to_process))
        queue = Queue()
        queue.put(seed)

        print("Seed:", seed)
        
        seed_value = volume[seed]
        region_voxels = []
        
        while not queue.empty():
            y, x = queue.get()
            
            if labeled_volume[y, x] != 0:
                continue
            
            labeled_volume[y, x] = region_label
            region_voxels.append((y, x))
            voxels_to_process.discard((y, x))
            
            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                
                if 0 <= ny < height and 0 <= nx < width:
                    if labeled_volume[ny, nx] == 0:
                        neighbor_value = volume[ny, nx]
                        distance = np.linalg.norm(seed_value - neighbor_value)
                        
                        if distance <= threshold:
                            queue.put((ny, nx))
        
        if len(region_voxels) < min_region_size:
            for y, x in region_voxels:
                labeled_volume[y, x] = -1  # Label as outlier
        else:
            region_label += 1

    return labeled_volume

# Example usage
# Example 3D volume with multivariate data (depth, height, width, channels)
# volume = np.load("../xray_volume.npy")
# labeled_volume = region_growing_3d_multivariate(volume, k=1.0, min_region_size=10)

# # Save the labeled volume
# print("Labeled Volume Shape:", labeled_volume.shape)
# np.save('../label_volume.npy', labeled_volume)

# Example 2D slice with multivariate data (height, width, channels)
volume = np.load("../xray_volume.npy")
slice_data = volume[0]
labeled_slice = region_growing_2d_multivariate(slice_data, k=1.0, min_region_size=10)

# Save the labeled volume
print("Labeled Slice Shape:", labeled_slice.shape)
np.save('../label_slice.npy', labeled_slice)