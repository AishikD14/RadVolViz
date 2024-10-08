import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pyvista as pv
import vtk
from scipy.ndimage import binary_dilation

# Function to load and parse the JSON file
def load_array_from_file(filename):
    with open(filename, 'r') as file:
        array = json.load(file)
    return array

# Recursive function to get the shape of an n-dimensional array
def get_shape(arr):
    shape = []
    while isinstance(arr, list):
        shape.append(len(arr))
        arr = arr[0] if len(arr) > 0 else []
    return shape

# Find the number of unique values in the array
def find_unique_values(arr):
    unique_values = set()
    for item in arr:
        if isinstance(item, list):
            unique_values.update(find_unique_values(item))
        else:
            unique_values.add(item)
    return unique_values

# Function to count the number of occurrences of each unique value in the array
def count_occurrences(arr):
    occurrences = {}
    for item in arr:
        if isinstance(item, list):
            sub_occurrences = count_occurrences(item)
            for key, value in sub_occurrences.items():
                occurrences[key] = occurrences.get(key, 0) + value
        else:
            occurrences[item] = occurrences.get(item, 0) + 1
    return occurrences

# Example function to compute similarity (e.g., Euclidean distance between 4D channel values)
def is_similar(voxel1, voxel2, threshold=0.1):
    distance = np.linalg.norm(voxel1[:4] - voxel2[:4])
    return distance < threshold

# Function to apply region growing
def region_growing(volume, seed_coords, cluster_id, visited, threshold=0.1):
    visited[seed_coords] = True
    cluster_label = cluster_id

    print("Growing region from seed:", seed_coords)

    # Define 6-connected neighborhood (up, down, left, right, front, back)
    neighbors = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]
    
    stack = [seed_coords]
    
    while stack:
        x, y, z = stack.pop()
        
        for dx, dy, dz in neighbors:
            nx, ny, nz = x + dx, y + dy, z + dz
            if 0 <= nx < volume.shape[0] and 0 <= ny < volume.shape[1] and 0 <= nz < volume.shape[2]:
                if not visited[nx, ny, nz]:
                    visited[nx, ny, nz] = True
                    
                    # Check similarity based on 4 channel values and ensure unclustered voxel (label 0)
                    if volume[nx, ny, nz, 4] == 0 and is_similar(volume[x, y, z], volume[nx, ny, nz], threshold):
                        volume[nx, ny, nz, 4] = cluster_label  # Assign the current cluster ID
                        volume[nx, ny, nz, :4] = volume[x, y, z, :4]  # Assign the 4 channel values to prevent drift in original values
                        stack.append((nx, ny, nz))            # Add this voxel to the stack for further growth
    
    return volume

# Full region-growing across the entire 3D volume
def apply_region_growing(volume, threshold=0.1):
    cluster_ids = [1, 2, 3, 4, 5]  # Cluster IDs to grow
    visited = np.zeros(volume.shape[:3], dtype=bool)  # Keep track of visited voxels
    for x in range(volume.shape[0]):
        for y in range(volume.shape[1]):
            for z in range(volume.shape[2]):
                cluster_id = volume[x, y, z, 4]  # Check cluster ID in 5th value
                if cluster_id in cluster_ids:
                    # Apply region growing from this voxel if it's a valid cluster seed
                    volume = region_growing(volume, (x, y, z), cluster_id, visited, threshold)
    return volume

# -----------------------------------------------------------------------------------------------

# Example: Parse the 'array3D.json' file
# filename = 'clusteredData2.json'
filename = 'clusteredDataRatio4.json'
parsed_array = load_array_from_file(filename)

shape = get_shape(parsed_array)

# Extract only the cluster IDs from the parsed array and mantain the 3D structure
# 4th dimension is a list whose last value is the cluster ID, replace it with the cluster ID
clusterData = np.zeros((shape[0], shape[1], shape[2]), dtype=int)
metalData = np.zeros((shape[0], shape[1], shape[2], 5))
for i in range(shape[0]):
    for j in range(shape[1]):
        for k in range(shape[2]):
            clusterData[i][j][k] = parsed_array[i][j][k][-1]
            if parsed_array[i][j][k][-1] == 50:
                metalData[i][j][k] =[0, 0, 0, 0, 50]
            else:
                metalData[i][j][k] = parsed_array[i][j][k][2:]

print(clusterData.shape)

shape = clusterData.shape

# Example: Find the unique values in the parsed array
unique_values = find_unique_values(clusterData.tolist())

# Display the unique values
print(len(unique_values))
print(unique_values)

# Example: Count the occurrences of each unique value in the parsed array
occurrences = count_occurrences(clusterData.tolist())

# Display the occurrences
print(occurrences)

# -----------------------------------------------------------------------------------------------

# Apply region growing algorithm
# print("Applying region growing...")

# threshold = 0.1  # Set similarity threshold
# volume_with_regions = apply_region_growing(metalData, threshold)

# # Save the labeled volume
# np.save("labeled_volume4.npy", volume_with_regions)

# print("Region growing completed.")

# quit()

# -----------------------------------------------------------------------------------------------

# Load the labeled volume
volume_with_regions = np.load("labeled_volume4.npy")

# Extract only the cluster IDs from the parsed array and mantain the 3D structure
# 4th dimension is a list whose last value is the cluster ID, replace it with the cluster ID
clusterData1 = np.zeros((shape[0], shape[1], shape[2]), dtype=int)
for i in range(shape[0]):
    for j in range(shape[1]):
        for k in range(shape[2]):
            # clusterData1[i][j][k] = parsed_array[i][j][k][-1]
            clusterData1[i][j][k] = volume_with_regions[i][j][k][4]

# -----------------------------------------------------------------------------------------------

diff_plot = True

# Compare all the values in the original and labeled volumes and print the number of differences 
print("Number of differences:", np.sum(clusterData != clusterData1))

# Mark the differences in the labeled volume wtih cluster number 6, keep the clusters with label 50 intact

if diff_plot:
    clusterData1[clusterData != clusterData1] = 6

# -----------------------------------------------------------------------------------------------

volume = np.array(clusterData.tolist()).reshape(shape)
volume1 = np.array(clusterData1.tolist()).reshape(shape)

# -----------------------------------------------------------------------------------------------

# Define the colormap for the clusters
if diff_plot:
    cmap = mcolors.ListedColormap(['gray', 'red', 'blue', 'green', 'orange', 'purple', 'yellow', 'black'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 50.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
else:
    cmap = mcolors.ListedColormap(['gray', 'red', 'blue', 'green', 'orange', 'purple', 'black'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 50.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Loop over each z-axis slice
slice_allowed = [90, 100, 130, 150, 170]
# slice_allowed = [130]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue
    slice_data = volume[x, :, :]
    slice_data1 = volume1[x, :, :]

    # Create a plot with two subplots
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    # Plot the original slice
    ax[0].imshow(slice_data, cmap=cmap, norm=norm)
    ax[0].set_title(f"Clustered Slice {x+1} along x-axis")
    ax[0].set_xlabel("Width (pixels)")
    ax[0].set_ylabel("Height (pixels)")
    ax[0].grid(False)
    ax[0].set_xticks([])
    ax[0].set_yticks([])
    ax[0].set_aspect('equal')

    # Plot the labeled slice
    ax[1].imshow(slice_data1, cmap=cmap, norm=norm)
    ax[1].set_title(f"Cluster + Region Growing Slice {x+1} along x-axis")
    ax[1].set_xlabel("Width (pixels)")
    ax[1].set_ylabel("Height (pixels)")
    ax[1].grid(False)
    ax[1].set_xticks([])
    ax[1].set_yticks([])
    ax[1].set_aspect('equal')

    # Create a colorbar axis at the bottom of both subplots
    cbar_ax = fig.add_axes([0.25, 0.1, 0.5, 0.03])  # [left, bottom, width, height]

    cmap1 = mcolors.ListedColormap(['gray', 'red', 'blue', 'green', 'orange', 'purple', 'black'])
    bounds1 = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 50.5]
    norm1 = mcolors.BoundaryNorm(bounds1, cmap1.N)

    # Plot the colorbar
    if diff_plot:
        cbar = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap1, norm=norm1), cax=cbar_ax, orientation='horizontal')
        cbar.set_ticks([0, 1, 2, 3, 4, 5, 50])
        cbar.set_label('Cluster IDs')
    else:
        cbar = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=cbar_ax, orientation='horizontal')
        cbar.set_ticks([0, 1, 2, 3, 4, 5, 50])
        cbar.set_label('Cluster IDs')

    # Show the plot
    plt.tight_layout(rect=[0, 0.15, 1, 1])
    plt.show()

    # ############################################################################

    # NOT IN USE
    
    # Plot the slice
    # plt.figure(figsize=(6, 6))
    # plt.imshow(slice_data, cmap=cmap, norm=norm)
    # plt.title(f"Slice {x+1} along x-axis")
    # plt.colorbar(ticks=[0, 1, 2, 3, 4, 5, 50], label='Cluster IDs')

    # ############################################################################


# -----------------------------------------------------------------------------------------------

# Define the colormap for the clusters
# colors = ['gray', 'red', 'blue', 'green', 'orange', 'purple', 'black']
# cmap = mcolors.ListedColormap([
#     [0.5, 0.5, 0.5, 1.0],  # gray (Cluster ID = 0, fully transparent)
#     [1.0, 0.0, 0.0, 1.0],  # red (Cluster ID = 1)
#     [0.0, 0.0, 1.0, 1.0],  # blue (Cluster ID = 2)
#     [0.0, 1.0, 0.0, 1.0],  # green (Cluster ID = 3)
#     [1.0, 0.65, 0.0, 1.0], # orange (Cluster ID = 4)
#     [0.5, 0.0, 0.5, 1.0],  # purple (Cluster ID = 5)
#     [0.0, 0.0, 0.0, 0.0]   # fully transparent (Cluster ID = 50)
# ])

# if diff_plot:
#     colors = ['gray', 'red', 'blue', 'green', 'orange', 'purple', 'yellow', 'black']
#     cmap = mcolors.ListedColormap([
#         [0.5, 0.5, 0.5, 1.0],  # gray (Cluster ID = 0, fully transparent)
#         [1.0, 0.0, 0.0, 1.0],  # red (Cluster ID = 1)
#         [0.0, 0.0, 1.0, 1.0],  # blue (Cluster ID = 2)
#         [0.0, 1.0, 0.0, 1.0],  # green (Cluster ID = 3)
#         [1.0, 0.65, 0.0, 1.0], # orange (Cluster ID = 4)
#         [0.5, 0.0, 0.5, 1.0],  # purple (Cluster ID = 5)
#         [1.0, 1.0, 0.0, 1.0],  # yellow (Cluster ID = 6)
#         [0.0, 0.0, 0.0, 0.0]   # fully transparent (Cluster ID = 50)
#     ])

# # Prepare the 3D volume
# dims = volume.shape

# # Create a grid structure to hold the volume data
# grid = pv.UniformGrid()

# # Set the dimensions: (nx, ny, nz)
# grid.dimensions = dims

# # Set up the spacing (optional, can set actual voxel size here)
# grid.spacing = (1, 1, 1)

# # Assign the volume data to the grid as scalar values
# grid.point_data["Cluster IDs"] = volume1.flatten(order="F")  # Flatten in Fortran order for VTK compatibility

# # Create a custom opacity transfer function
# # Ensure both Cluster 0 and Cluster 50 are fully transparent
# opacity_transfer_function = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0])  # Clusters 0 and 50 are fully transparent

# # Create a plotter for rendering
# plotter = pv.Plotter()

# # Add the volume to the plotter with the custom colormap and opacity function
# plotter.add_volume(grid, scalars="Cluster IDs", cmap=cmap, clim=[0, len(colors)-1], opacity=opacity_transfer_function, show_scalar_bar=False)

# # Set plotter options
# plotter.add_axes()  # Optional: Add axes for better visualization
# plotter.show_bounds(grid="back")  # Show grid bounds

# # Render the entire volume
# plotter.show()