import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte
import warnings
import math
import matplotlib.colors as mcolors
import cv2
from sklearn.manifold import TSNE
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
from scipy.spatial.distance import cdist
from scipy.signal import find_peaks
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import time
from numba import njit
from scipy.spatial import cKDTree
from mayavi import mlab
from scipy.ndimage import zoom

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------------

# Function to constrain CX and CY values to the unit circle
def ConstrainInUnit(CX, CY):
    r = math.sqrt(CX**2 + CY**2)
    if r > 1:
        CX /= r
        CY /= r
    return CX, CY

# Convert to color based on CX, CY (using HCL color space approximation)
def GBCtoHCL2(CX, CY):
    # Check if the point lies on the edge (similar to CX * CX + CY * CY > 0.999999)
    if CX * CX + CY * CY > 0.999999:
        return (0, 0, 0)  # Return RGB black as a tuple
    
    # Calculate hue
    h = math.atan2(CY, CX) + math.pi / 2
    if h < 0:
        h += math.pi * 2
    if h > math.pi * 2:
        h -= math.pi * 2

    # Convert radians to degrees
    h = h / math.pi * 180
    
    # Saturation
    s = math.sqrt(CX**2 + CY**2)
    
    # Lightness (fixed at 0.55)
    l = 0.55

    # Convert hue back to [0, 360] for matplotlib
    h = h / 360.0  # Normalize to [0, 1] range for matplotlib
    return mcolors.hsv_to_rgb((h, s, l))

# Function to perform geometric transformation on the supplied data
def GBC(datam, rotate_var):
    m = len(datam)
    n = len(datam[0])
    
    # Initialize the angle array
    angle = np.zeros(n)
    angle[0] = math.pi / 2 + rotate_var
    
    # Initialize the GBCL array with m + n rows and 2 + n columns
    GBCL = [[0 for _ in range(2 + n)] for _ in range(m + n)]
    
    # Populate the GBCL array
    for i in range(m + n):
        for k in range(2, 2 + n):
            if i < m:
                GBCL[i][k] = float(datam[i][k - 2])
    
    # Populate the first 2 dimensions of the first of the last n rows
    GBCL[m][0] = math.cos(angle[0])
    GBCL[m][1] = math.sin(angle[0])
    
    # Populate the first 2 dimensions of the remaining n-1 rows
    for i in range(1, n):
        angle[i] = angle[i - 1] - 2 * math.pi / n
        GBCL[m + i][0] = math.cos(angle[i]) * 0.997
        GBCL[m + i][1] = math.sin(angle[i]) * 0.997
    
    # Adjust the angles if needed
    for i in range(n):
        if angle[i] < 0:
            angle[i] += 2 * math.pi
        if angle[i] > 2 * math.pi:
            angle[i] -= 2 * math.pi
    
    # Sort the angles
    angle.sort()
    
    # Loop through the original data
    for i in range(m):
        tempsum = sum(float(datam[i][j]) for j in range(n))
        
        if tempsum == 0:
            GBCL[i][0] = 0
            GBCL[i][1] = 0
        else:
            for k in range(n):
                GBCL[i][0] += (float(datam[i][k]) / tempsum) * GBCL[m + k][0]
                GBCL[i][1] += (float(datam[i][k]) / tempsum) * GBCL[m + k][1]
            
            tempangle = math.atan2(GBCL[i][1], GBCL[i][0])
            if tempangle < 0:
                tempangle += 2 * math.pi
            
            flag = False
            tempA = 0
            tempB = 0
            
            for j in range(n - 1):
                if (tempangle > angle[j] or tempangle == angle[j]) and (tempangle < angle[j + 1]):
                    tempA = angle[j + 1]
                    tempB = angle[j]
                    flag = True
                    break
            
            if not flag:
                tempA = angle[0] + 2 * math.pi
                tempB = angle[n - 1]
            
            lth = (math.sqrt(GBCL[i][0] ** 2 + GBCL[i][1] ** 2) / 
                   math.cos((tempA - tempB) / 2) * 
                   math.cos(-(tempA + tempB) / 2 + tempangle))
            
            GBCL[i][0] = lth * math.cos(tempangle)
            GBCL[i][1] = lth * math.sin(tempangle)
 
    return GBCL

# Convert to color based on CX, CY (using HCL color space approximation)
def CoordToColor(CX, CY):
    CX, CY = ConstrainInUnit(CX, CY)
    return GBCtoHCL2(CX, CY)

# Function to get color from ratio
def getColorfromRatio(ratio):
    ss = GBC(np.array([ratio]), 0.0)[0][:2]

    color = CoordToColor(ss[0], ss[1])

    return (np.array(color)[:3] * 255).astype(int)

def cropVolume(volume, zoom_factor):
    # Calculate new dimensions for cropping
    depth, height, width = volume.shape[:3]
    center_d, center_h, center_w = depth // 2, height // 2, width // 2

    # Calculate crop dimensions
    crop_depth = int(depth / zoom_factor)
    crop_height = int(height / zoom_factor)
    crop_width = int(width / zoom_factor)

    # Define crop box around the center
    d_min = max(center_d - crop_depth // 2, 0)
    d_max = min(center_d + crop_depth // 2, depth)
    h_min = max(center_h - crop_height // 2, 0)
    h_max = min(center_h + crop_height // 2, height)
    w_min = max(center_w - crop_width // 2, 0)
    w_max = min(center_w + crop_width // 2, width)

    # Crop the volume
    cropped_volume = volume[d_min:d_max, h_min:h_max, w_min:w_max]

    # Resize back to original size
    resized_volume = zoom(cropped_volume, (depth / cropped_volume.shape[0],
                                           height / cropped_volume.shape[1],
                                           width / cropped_volume.shape[2],
                                           1),
                          order=1)  # Linear interpolation for smooth resizing

    return resized_volume

# -------------------------------------------------------------------------------

def initialize_cluster_centers(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform 3D grid, ignoring zero-value voxels.
    """
    depth, rows, cols, _ = data.shape
    centers = []
    for d in range(grid_spacing // 2, depth, grid_spacing):
        for r in range(grid_spacing // 2, rows, grid_spacing):
            for c in range(grid_spacing // 2, cols, grid_spacing):
                if not np.all(data[d, r, c] == 0):  # Ignore zero-value voxels
                    centers.append([d, r, c] + list(data[d, r, c]))
    return np.array(centers, dtype=np.float32)

@njit
def calculate_distance(voxel, center, spatial_weight, feature_weight):
    """
    Compute the combined distance between a voxel and a cluster center in 3D.
    """
    spatial_dist = np.sqrt((voxel[0] - center[0])**2 + (voxel[1] - center[1])**2 + (voxel[2] - center[2])**2)
    feature_dist = np.sqrt(np.sum((voxel[3:] - center[3:])**2))
    return np.sqrt((spatial_dist / spatial_weight)**2 + (feature_dist / feature_weight)**2)

@njit
def assign_voxels_to_clusters(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing):
    """
    Assign each voxel to the nearest cluster center within its search window, ignoring zero-value voxels.
    """
    depth, rows, cols, _ = data.shape
    for idx, center in enumerate(cluster_centers):
        d, r, c = int(center[0]), int(center[1]), int(center[2])
        
        # Search window around the cluster center
        d_min = max(d - grid_spacing, 0)
        d_max = min(d + grid_spacing + 1, depth)
        r_min = max(r - grid_spacing, 0)
        r_max = min(r + grid_spacing + 1, rows)
        c_min = max(c - grid_spacing, 0)
        c_max = min(c + grid_spacing + 1, cols)

        for dd in range(d_min, d_max):
            for rr in range(r_min, r_max):
                for cc in range(c_min, c_max):
                    if np.all(data[dd, rr, cc] == 0):
                        continue  # Ignore zero-value voxels
                    
                    voxel = np.array([dd, rr, cc] + list(data[dd, rr, cc]))
                    distance = calculate_distance(voxel, center, spatial_weight, feature_weight)
                    if distance < distances[dd, rr, cc]:
                        distances[dd, rr, cc] = distance
                        labels[dd, rr, cc] = idx

@njit
def update_cluster_centers(data, labels, cluster_centers):
    """
    Compute new cluster centers based on the average of assigned voxels.
    """
    num_clusters = len(cluster_centers)
    num_features = data.shape[3]
    
    new_centers = np.zeros_like(cluster_centers)
    counts = np.zeros(num_clusters, dtype=np.int32)

    depth, rows, cols = labels.shape
    for d in range(depth):
        for r in range(rows):
            for c in range(cols):
                label = labels[d, r, c]
                if label == -1:
                    continue  # Skip unassigned voxels
                new_centers[label][:3] += np.array([d, r, c], dtype=np.float32)
                new_centers[label][3:] += data[d, r, c]
                counts[label] += 1

    for i in range(num_clusters):
        if counts[i] > 0:
            new_centers[i] /= counts[i]

    return new_centers

def custom_slic(data, num_superpixels, spatial_weight=5, max_iter=20):
    """
    Perform optimized SLIC segmentation on 4D volumetric data,
    ensuring zero-value voxels are ignored in segmentation and grouped into a single supervoxel at the end.
    """
    depth, rows, cols, num_features = data.shape
    grid_spacing = int(np.cbrt((depth * rows * cols) / num_superpixels))
    feature_weight = np.std(data.reshape(-1, num_features), axis=0).mean()

    # Initialize cluster centers
    cluster_centers = initialize_cluster_centers(data, num_superpixels, grid_spacing)
    labels = -1 * np.ones((depth, rows, cols), dtype=np.int32)
    distances = np.full((depth, rows, cols), np.inf, dtype=np.float32)

    print("Starting SLIC segmentation...")

    # Iterate until convergence
    for _ in range(max_iter):
        assign_voxels_to_clusters(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing)
        cluster_centers = update_cluster_centers(data, labels, cluster_centers)
    
    # Assign all zero-value voxels to a single supervoxel label
    zero_voxel_label = (np.max(labels) + 1)
    for d in range(depth):
        for r in range(rows):
            for c in range(cols):
                if np.all(np.abs(data[r, c]) < 1e-15):
                    labels[d, r, c] = zero_voxel_label

    # Ensure all voxels are assigned to a cluster
    unassigned = np.where(labels == -1)
    if unassigned[0].size > 0:
        tree = cKDTree(cluster_centers[:, :3])
        points = np.column_stack(unassigned)
        _, nearest_labels = tree.query(points)
        labels[unassigned] = nearest_labels

    return labels, cluster_centers

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../../xray_volume.npy')

# -------------------------------------------------------------------------------

color_assignment = False
superpixel_generation = False

# -------------------------------------------------------------------------------
# Zoom in on the center of the volume
# -------------------------------------------------------------------------------

# Define a zoom factor (increase this value to zoom in more)
zoom_factor = 1.4

resized_volume = cropVolume(volume, zoom_factor)  # Adjust zoom factor as needed

# -------------------------------------------------------------------------------

if color_assignment:

    start_time = time.time()

    # Create an input volume to store the custom colors
    input_volume = np.zeros_like(resized_volume, dtype=np.uint8)

    print(input_volume.shape)

    # Drop the one channel to store RGB values
    input_volume = input_volume[:, :, :, :3]

    print("Starting color assignment...")
    print("This may take a while...")

    # Loop though each pixel in the image and assign custom colors
    for i in range(resized_volume.shape[0]):
        for j in range(resized_volume.shape[1]):
            for k in range(resized_volume.shape[2]):
                print(i, j, k)
                if np.all(resized_volume[i][j][k] == 0):
                    input_volume[i, j, k] = (0, 0, 0)
                else:
                    input_volume[i, j, k] = getColorfromRatio(resized_volume[i][j][k])

    print("Color assignment complete.")
    print("Color assignment time:", time.time() - start_time)

    # Save the input volume with custom colors
    np.save('../../xray_volume_custom_colors.npy', input_volume)

    print("Input volume with custom colors saved.")

    quit()

else:

    # Load the input volume with custom colors 
    input_volume = np.load('../../xray_volume_custom_colors.npy')

    print("Input volume with custom colors loaded.")

    print(input_volume.shape)

# -------------------------------------------------------------------------------

if superpixel_generation:
    start_time = time.time()

    # Call the custom SLIC function
    num_superpixels = 500
    labels, cluster_centers = custom_slic(resized_volume, num_superpixels)

    print("SLIC segmentation complete.")
    print("Superpixel generation time:", time.time() - start_time)

    print("Number of superpixels:", len(cluster_centers))
    print("Range of labels:", np.min(labels), np.max(labels))

    # Save the labels
    np.save('../../xray_volume_labels.npy', labels)

    print("Labels saved.")

    quit()

else:

    # Load the labels
    labels = np.load('../../xray_volume_labels.npy')

    print("Labels loaded.")

    print("Number of superpixels:", len(np.unique(labels)))
    print("Range of labels:", np.min(labels), np.max(labels))

# -------------------------------------------------------------------------------

# Plot a single slice of the 3D volume with custom colors

# Select the slice to visualize
slice_idx = 130

input_slice = input_volume[slice_idx, :, :]

# Drop last segment as it is zero value voxels

# Get the labels for the selected slice
slice_labels = labels[slice_idx, :, :]

# Create a figure
# fig = plt.figure(figsize=(10, 10))
# plt.imshow(input_slice)
# plt.axis('off')
# plt.title('Custom SLIC segmentation')
# # plt.show()

plt.figure(figsize=(12, 5))

# Visualize the Original image 
plt.subplot(1, 2, 1)
plt.imshow(input_slice)  
plt.title('Original Image')
plt.axis('off')

# 3. Visualize the superpixel-boundary marked image
plt.subplot(1, 2, 2)
plt.imshow(mark_boundaries(input_slice, slice_labels))
plt.title('Superpixel Boundaries')
plt.axis('off')

# Set an overall title for the figure
plt.suptitle(f'Volume Slice {slice_idx}')

plt.tight_layout()
plt.show()

quit()

# -------------------------------------------------------------------------------

# import pyvista as pv

# # Assume 'volume' is (X, Y, Z, 3)
# grid = pv.ImageData(dimensions=input_volume.shape[:3])
# grid.point_data["colors"] = input_volume.reshape(-1, 3) / 255.0  # Normalize RGB

# plotter = pv.Plotter()

# # opacity_values = np.linspace(0, 1, 256)  # Gradually increase opacity
# # opacity_values[:50] = 0  # Make very dark pixels fully transparent

# # plotter.add_mesh(grid, scalars="colors", rgb=True, opacity=opacity_values)

# plotter.add_mesh(grid, scalars="colors", rgb=True, opacity="sigmoid")

# def clip_volume(value):
#     print(value)

#     """Update the volume to only show from the selected X value onward."""
#     camera_position = plotter.camera_position  # Store current camera view
#     grid_clipped = grid.clip_box(bounds=(value, input_volume.shape[0], 0, input_volume.shape[1], 0, input_volume.shape[2]))
    
#     plotter.clear()  # Clear previous plot
#     plotter.add_mesh(grid_clipped, scalars="colors", rgb=True, opacity="sigmoid")  # Re-add clipped volume
#     plotter.camera_position = camera_position  # Restore view

# # ✅ Add the slider **only once**
# plotter.add_slider_widget(clip_volume, [0, input_volume.shape[0]], title="X-Axis Clip")

# plotter.show()

# -------------------------------------------------------------------------------