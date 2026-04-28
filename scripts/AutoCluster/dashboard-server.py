import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn import metrics
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte
import warnings
import math
import matplotlib.colors as mcolors
import cv2
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, ctx, ClientsideFunction
from scipy.spatial.distance import cdist
from scipy.signal import find_peaks
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import time
import json
from numba import njit
import torch
import torch.nn as nn
import torch.optim as optim
import pickle
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from scipy.spatial import cKDTree
import urllib.parse

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

# Zoom in on the center of the image
def cropImage(image, zoom_factor):
    # Calculate new dimensions for cropping
    width, height = image.shape[:2]
    center_x, center_y = width // 2, height // 2

    # Calculate new dimensions for cropping
    crop_width = int(width / zoom_factor)
    crop_height = int(height / zoom_factor)

    # Define crop box around the center
    left = center_x - crop_width // 2
    right = center_x + crop_width // 2
    top = center_y - crop_height // 2
    bottom = center_y + crop_height // 2

    # Ensure that the crop box is within bounds of the original image
    left = max(left, 0)
    right = min(right, width)
    top = max(top, 0)
    bottom = min(bottom, height)

    # Crop the image using numpy slicing
    cropped_image = image[top:bottom, left:right]

    # Resize the cropped image back to the original size
    resized_image = cv2.resize(cropped_image, (width, height), interpolation=cv2.INTER_LINEAR)

    return resized_image

# -------------------------------------------------------------------------------

def initialize_cluster_centers1(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform grid.
    """
    rows, cols, _ = data.shape
    centers = []
    for r in range(grid_spacing // 2, rows, grid_spacing):
        for c in range(grid_spacing // 2, cols, grid_spacing):
            centers.append([r, c] + list(data[r, c]))
    return np.array(centers, dtype=np.float32)


@njit
def calculate_distance1(pixel, center, spatial_weight, feature_weight):
    """
    Compute the combined distance between a pixel and a cluster center.
    Uses Numba to accelerate this function.
    """
    spatial_dist = np.sqrt((pixel[0] - center[0])**2 + (pixel[1] - center[1])**2)
    feature_dist = np.sqrt(np.sum((pixel[2:] - center[2:])**2))
    return np.sqrt((spatial_dist / spatial_weight)**2 + (feature_dist / feature_weight)**2)


@njit
def assign_pixels_to_clusters1(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing):
    """
    Assign each pixel to the nearest cluster center within its search window.
    Uses Numba for faster execution.
    """
    rows, cols, _ = data.shape
    for idx, center in enumerate(cluster_centers):
        r, c = int(center[0]), int(center[1])
        
        # Search window around the cluster center
        r_min = max(r - grid_spacing, 0)
        r_max = min(r + grid_spacing + 1, rows)
        c_min = max(c - grid_spacing, 0)
        c_max = min(c + grid_spacing + 1, cols)

        for rr in range(r_min, r_max):
            for cc in range(c_min, c_max):
                pixel = np.array([rr, cc] + list(data[rr, cc]))
                distance = calculate_distance1(pixel, center, spatial_weight, feature_weight)
                if distance < distances[rr, cc]:
                    distances[rr, cc] = distance
                    labels[rr, cc] = idx


@njit
def update_cluster_centers1(data, labels, cluster_centers):
    """
    Compute new cluster centers based on the average of assigned pixels.
    Uses Numba for efficiency.
    """
    num_clusters = len(cluster_centers)
    num_features = data.shape[2]
    
    new_centers = np.zeros_like(cluster_centers)
    counts = np.zeros(num_clusters, dtype=np.int32)

    rows, cols = labels.shape
    for r in range(rows):
        for c in range(cols):
            label = labels[r, c]
            new_centers[label][:2] += np.array([r, c], dtype=np.float32)
            new_centers[label][2:] += data[r, c]
            counts[label] += 1

    for i in range(num_clusters):
        if counts[i] > 0:
            new_centers[i] /= counts[i]

    return new_centers


def custom_slic1(data, num_superpixels, spatial_weight=5, max_iter=20):
    """
    Perform optimized SLIC segmentation on 4D input data (metal concentrations per pixel).
    """
    rows, cols, num_features = data.shape
    grid_spacing = int(np.sqrt((rows * cols) / num_superpixels))
    feature_weight = np.std(data.reshape(-1, num_features), axis=0).mean()

    # Initialize cluster centers
    cluster_centers = initialize_cluster_centers1(data, num_superpixels, grid_spacing)
    labels = -1 * np.ones((rows, cols), dtype=np.int32)
    distances = np.full((rows, cols), np.inf, dtype=np.float32)

    # Iterate until convergence
    for _ in range(max_iter):
        assign_pixels_to_clusters1(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing)
        cluster_centers = update_cluster_centers1(data, labels, cluster_centers)

    return labels, cluster_centers

# ===============================================================================

def initialize_cluster_centers(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform grid, ignoring zero-value pixels.
    """
    rows, cols, _ = data.shape
    centers = []
    for r in range(grid_spacing // 2, rows, grid_spacing):
        for c in range(grid_spacing // 2, cols, grid_spacing):
            if not np.all(data[r, c] == 0):  # Ignore zero-value pixels
                centers.append([r, c] + list(data[r, c]))
    return np.array(centers, dtype=np.float32)

@njit
def calculate_distance(pixel, center, spatial_weight, feature_weight):
    """
    Compute the combined distance between a pixel and a cluster center.
    """
    spatial_dist = np.sqrt((pixel[0] - center[0])**2 + (pixel[1] - center[1])**2)
    feature_dist = np.sqrt(np.sum((pixel[2:] - center[2:])**2))
    return np.sqrt((spatial_dist / spatial_weight)**2 + (feature_dist / feature_weight)**2)

@njit
def assign_pixels_to_clusters(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing):
    """
    Assign each pixel to the nearest cluster center within its search window, ignoring zero-value pixels.
    """
    rows, cols, _ = data.shape
    for idx, center in enumerate(cluster_centers):
        r, c = int(center[0]), int(center[1])
        
        # Search window around the cluster center
        r_min = max(r - grid_spacing, 0)
        r_max = min(r + grid_spacing + 1, rows)
        c_min = max(c - grid_spacing, 0)
        c_max = min(c + grid_spacing + 1, cols)

        for rr in range(r_min, r_max):
            for cc in range(c_min, c_max):
                if np.all(data[rr, cc] == 0):
                    continue  # Ignore zero-value pixels
                
                pixel = np.array([rr, cc] + list(data[rr, cc]))
                distance = calculate_distance(pixel, center, spatial_weight, feature_weight)
                if distance < distances[rr, cc]:
                    distances[rr, cc] = distance
                    labels[rr, cc] = idx

@njit
def update_cluster_centers(data, labels, cluster_centers):
    """
    Compute new cluster centers based on the average of assigned pixels.
    """
    num_clusters = len(cluster_centers)
    num_features = data.shape[2]
    
    new_centers = np.zeros_like(cluster_centers)
    counts = np.zeros(num_clusters, dtype=np.int32)

    rows, cols = labels.shape
    for r in range(rows):
        for c in range(cols):
            label = labels[r, c]
            if label == -1:
                continue  # Skip unassigned pixels
            new_centers[label][:2] += np.array([r, c], dtype=np.float32)
            new_centers[label][2:] += data[r, c]
            counts[label] += 1

    for i in range(num_clusters):
        if counts[i] > 0:
            new_centers[i] /= counts[i]

    return new_centers

def custom_slic(data, num_superpixels, spatial_weight=5, max_iter=20):
    """
    Perform optimized SLIC segmentation on 4D input data (metal concentrations per pixel),
    ensuring zero-value pixels are ignored in segmentation and grouped into a single superpixel at the end.
    """
    rows, cols, num_features = data.shape
    grid_spacing = int(np.sqrt((rows * cols) / num_superpixels))
    feature_weight = np.std(data.reshape(-1, num_features), axis=0).mean()

    # Initialize cluster centers
    cluster_centers = initialize_cluster_centers(data, num_superpixels, grid_spacing)
    labels = -1 * np.ones((rows, cols), dtype=np.int32)
    distances = np.full((rows, cols), np.inf, dtype=np.float32)

    # Iterate until convergence
    for _ in range(max_iter):
        assign_pixels_to_clusters(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing)
        cluster_centers = update_cluster_centers(data, labels, cluster_centers)
    
    # Assign all zero-value pixels to a single superpixel label
    zero_pixel_label = (np.max(labels) + 1)  # Assign a new label
    for r in range(rows):
        for c in range(cols):
            # if np.all(data[r, c] == 0):
            if np.all(np.abs(data[r, c]) < 1e-15):
                labels[r, c] = zero_pixel_label

    # Ensure all pixels are assigned to a cluster
    unassigned = np.where(labels == -1)
    if unassigned[0].size > 0:
        tree = cKDTree(cluster_centers[:, :2])
        points = np.column_stack(unassigned)
        _, nearest_labels = tree.query(points)
        labels[unassigned] = nearest_labels

    return labels, cluster_centers

# ===============================================================================

# Set seed for reproducibility
torch.manual_seed(0)

# --------------------------------------------------------------------------------

def create_channel_histogram(flattened_data, channel_index, bins=200, use_log_histogram=True):
    # Histogram always uses the full spectrum of nonzero voxels.
    nonzero_indices = ~np.all(np.isclose(flattened_data, 0), axis=1)
    nonzero_data = flattened_data[nonzero_indices]

    if nonzero_data.size == 0:
        return [], np.array([])

    histogram_array = nonzero_data[:, channel_index]
    hist_count, bin_edges = np.histogram(histogram_array, bins=bins)
    hist_count = hist_count.astype(float)

    zero_counts = np.isclose(hist_count, 0)
    if use_log_histogram:
        hist_count[~zero_counts] = np.log10(hist_count[~zero_counts])

    max_count = hist_count.max()
    if np.isclose(max_count, 0):
        hist = [0 for _ in hist_count]
    else:
        hist = [int(v / max_count * 100) for v in hist_count.tolist()]

    return hist, bin_edges

# --------------------------------------------------------------------------------

# Load volume data
# dataset = "CeCoFeGd"
# volume = np.load('../../xray_volume.npy')
# channel_names = ["Ce", "Co", "Fe", "Gd"]

dataset = "thigh_sarcoma"
volume = np.load('../../thigh_sarcoma_volume.npy')
channel_names = ["CT", "MRI-T1", "MRI-T2", "PET"]

# --------------------------------------------------------------------------------

if dataset == "thigh_sarcoma":
    # Switch 1st and 2nd channels for better visualization
    volume = volume[:, :, :, [1, 0, 2, 3]]
    channel_names = ["MRI-T1", "CT", "MRI-T2", "PET"]

    # Normalize each channel to [0, 1] range
    for i in range(volume.shape[3]):
        channel = volume[:, :, :, i]

        max_val = channel.max()
        min_val = channel.min()

        volume[:, :, :, i] = (
            (1 - 0) * (channel.astype(np.float64) - min_val)
            / (max_val - min_val)
        ) + 0

    # Keep only voxels whose PET value falls in the first 10% of PET histogram bins.
    pet_channel_index = channel_names.index("PET")
    pet_histogram, pet_bin_edges = create_channel_histogram(
        volume.reshape(-1, volume.shape[-1]),
        pet_channel_index,
        bins=200,
        use_log_histogram=True
    )

    if len(pet_bin_edges) > 0:
        first_pet_bin_count = max(1, int(np.ceil((len(pet_bin_edges) - 1) * 0.10)))
        pet_cutoff = pet_bin_edges[first_pet_bin_count]
        nonzero_voxel_mask = ~np.all(np.isclose(volume, 0), axis=3)
        first_pet_histogram_mask = (
            nonzero_voxel_mask
            & (volume[:, :, :, pet_channel_index] >= pet_bin_edges[0])
            & (volume[:, :, :, pet_channel_index] <= pet_cutoff)
        )
        volume[~first_pet_histogram_mask] = 0

    # Rescale channel values to [0, 1] range after filtering
    for i in range(volume.shape[3]):
        channel = volume[:, :, :, i]

        max_val = channel.max()
        min_val = channel.min()

        if max_val > min_val:  # Avoid division by zero
            volume[:, :, :, i] = (
                (1 - 0) * (channel.astype(np.float64) - min_val)
                / (max_val - min_val)
            ) + 0

# -------------------------------------------------------------------------------

def get_feature_column_names(feature_count):
    if len(channel_names) == feature_count:
        return channel_names

    return [f'Feature Dimension {i+1}' for i in range(feature_count)]

# -------------------------------------------------------------------------------

# Function to create original slice
def create_original_slice(axis, slice_num):
    # Extract slice from volume
    if axis == "x":
        image = volume[slice_num, :, :]
    elif axis == "y":
        image = volume[:, slice_num, :]
    else:
        image = volume[:, :, slice_num]

    print(image.shape)

    # -------------------------------------------------------------------------------
    # Zoom in on the center of the image
    # -------------------------------------------------------------------------------

    # Define a zoom factor (increase this value to zoom in more)
    if dataset == "CeCoFeGd":
        zoom_factor = 1.4  # Adjust this value as needed for better visualization
        resized_image = cropImage(image, zoom_factor)
    else:
        resized_image = image

    # -------------------------------------------------------------------------------

    # Create an input image to store the colors for each pixel
    input_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    input_image = input_image[:, :, :3]

    # Loop though each pixel in the image and assign custom colors
    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            # If all channels are 0, assign black color
            if np.all(resized_image[i][j] == 0):
                input_image[i][j] = [0, 0, 0]
            else:
                input_image[i][j] = getColorfromRatio(resized_image[i][j])

    # -------------------------------------------------------------------------------

    # Create a plotly figure
    fig = px.imshow(input_image)

    # Update the layout of the figure
    fig.update_layout(
        margin=dict(l=25, r=25, b=25, t=25),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    # Return the figure
    return fig, resized_image, input_image

# Function to create superpixels
def create_superpixels(resized_image, input_image, num_superpixels,dropzero_checkbox):
    if 'enable' in dropzero_checkbox:
        segments, cluster_centers = custom_slic(resized_image, num_superpixels)
    else:
        segments, cluster_centers = custom_slic1(resized_image, num_superpixels)

    # segments = segmentation.slic(input_image, n_segments=num_superpixels, compactness=30, start_label=0)

    print("Segment Range:", np.min(segments), np.max(segments))

    boundary_image = mark_boundaries(input_image, segments)

    # Get the shape of the image
    height, width = boundary_image.shape[:2]

    # Create a scatter trace for displaying segment IDs on hover
    segment_coords = []
    segment_ids = []

    for i in range(height):
        for j in range(width):
            segment_coords.append((i, j))
            segment_ids.append(segments[i, j])

    # Create a Plotly scatter plot for segment IDs at each pixel location
    scatter_trace = {
        'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
        'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
        'mode': 'markers',
        'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
        'text': [seg_id for seg_id in segment_ids],  # Text for hover
        'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
    }

    # Create a plotly figure
    fig = px.imshow(boundary_image)

    # Add the scatter trace to the figure
    fig.add_traces([scatter_trace])

    # Update the layout of the figure
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        coloraxis_showscale=False
    )

    trace_info = {"segment_coords": segment_coords, "segment_ids": list(map(int, segment_ids))}

    # Return the figure
    return fig, segments, boundary_image, trace_info

# Function to create PCA plot
def create_pca_plot(segment_vectors, segmentColorDict, hovered_segment_id, encoded_features, autoencoder_checkbox):
    if 'enable' in autoencoder_checkbox:
        segment_vectors = encoded_features

    # Perform PCA for dimensionality reduction
    pca = PCA(n_components=2, random_state=42)
    reduced_data = pca.fit_transform(segment_vectors)

    # Create dummy labels for visualization (use actual labels if available)
    segment_labels = np.arange(len(reduced_data))

    # Create a DataFrame for easier plotting
    df_pca = pd.DataFrame(reduced_data, columns=['PCA Dimension 1', 'PCA Dimension 2'])
    df_pca['Segment ID'] = segment_labels

    # Extract colors for each segment in the same order as `segment_ids`
    color_array = [tuple(segmentColorDict[seg_id].tolist()) for seg_id in segment_labels]

    # Convert to 0-255 range
    color_array = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in color_array]

    # Format as "rgb(R, G, B)"
    color_array = [f'rgb{color}' for color in color_array]

    # Normalized levels
    normalized_levels = np.linspace(0, 1, len(reduced_data))

    # Create color scale of format [[level, color], ...]
    color_scale = [[level, color] for level, color in zip(normalized_levels, color_array)]

    fig = px.scatter(
        df_pca,
        x='PCA Dimension 1',
        y='PCA Dimension 2',
        hover_data=['Segment ID'],
    )

    fig.update_traces(marker=dict(color=segment_labels, colorscale=color_scale))

    fig.update_layout(
        xaxis_title={
            'font': {
                'color': 'white'
            }
        },
        yaxis_title={
            'font': {
                'color': 'white'
            }
        },
        xaxis={
            'tickfont': {
                'color': 'white'
            }
        },
        yaxis={
            'tickfont': {
                'color': 'white'
            }
        }
    )
    
    fig.update_layout(clickmode='event')

    # if hovered_segment_id is not None:
    #     # Highlight the corresponding segment in the PCA plot
    #     highlighted_segment = df_pca[df_pca['Segment ID'] == hovered_segment_id]

    #     # Dim non-selected segments
    #     fig.update_traces(marker=dict(opacity=0.3), selector=dict(mode='markers'))

    #     fig.add_trace(
    #         go.Scatter(
    #             x=highlighted_segment['PCA Dimension 1'],
    #             y=highlighted_segment['PCA Dimension 2'],
    #             mode='markers',
    #             marker=dict(size=15, color='black', opacity=1),
    #             hoverinfo='skip',  # Hide hover info for the highlighted segment,
    #             showlegend=False  # Hide legend for the highlighted segment
    #         )
    #     )

    return fig, df_pca

# Function to create t-SNE plot
def create_tsne_plot(segment_vectors, segmentColorDict, hovered_segment_id, encoded_features, autoencoder_checkbox):
    if 'enable' in autoencoder_checkbox:
        segment_vectors = encoded_features

    # Perform t-SNE for dimensionality reduction
    tsne = TSNE(n_components=2, random_state=42)
    reduced_data = tsne.fit_transform(segment_vectors)

    # Create dummy labels for visualization (use actual labels if available)
    segment_labels = np.arange(len(reduced_data))

    # Create a DataFrame for easier plotting
    df_tsne = pd.DataFrame(reduced_data, columns=['t-SNE Dimension 1', 't-SNE Dimension 2'])
    df_tsne['Segment ID'] = segment_labels

    # -------------------------------------------------------------------------------

    # Create Radviz color scale

    # Extract colors for each segment in the same order as `segment_ids`
    color_array = [tuple(segmentColorDict[seg_id].tolist()) for seg_id in segment_labels]

    # Convert to 0-255 range
    color_array = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in color_array]

    # Format as "rgb(R, G, B)"
    color_array = [f'rgb{color}' for color in color_array]

    # Normalized levels
    normalized_levels = np.linspace(0, 1, len(reduced_data))

    # Create color scale of format [[level, color], ...]
    color_scale = [[level, color] for level, color in zip(normalized_levels, color_array)]

    # -------------------------------------------------------------------------------

    fig = px.scatter(
        df_tsne,
        x='t-SNE Dimension 1',
        y='t-SNE Dimension 2',
        hover_data=['Segment ID']
    )

    fig.update_traces(marker=dict(color=segment_labels, colorscale=color_scale))

    fig.update_layout(
        xaxis_title={
            'font': {
                'color': 'white'
            }
        },
        yaxis_title={
            'font': {
                'color': 'white'
            }
        },
        xaxis={
            'tickfont': {
                'color': 'white'
            }
        },
        yaxis={
            'tickfont': {
                'color': 'white'
            }
        }
    )

    fig.update_layout(clickmode='event')

    # if hovered_segment_id is not None:
    #     # Highlight the corresponding segment in the t-SNE plot
    #     highlighted_segment = df_tsne[df_tsne['Segment ID'] == hovered_segment_id]

    #     # Dim non-selected segments
    #     fig.update_traces(marker=dict(opacity=0.3), selector=dict(mode='markers'))

    #     fig.add_trace(
    #         go.Scatter(
    #             x=highlighted_segment['t-SNE Dimension 1'],
    #             y=highlighted_segment['t-SNE Dimension 2'],
    #             mode='markers',
    #             marker=dict(size=15, color='black', opacity=1),
    #             hoverinfo='skip',  # Hide hover info for the highlighted segment,
    #             showlegend=False  # Hide legend for the highlighted segment
    #         )
    #     )

    return fig, df_tsne

# Function create parallel coordinates plot
def create_parallel_coordinates_plot(segment_vectors, segmentColorDict, hovered_segment_id, encoded_features, autoencoder_checkbox):
    if 'enable' in autoencoder_checkbox:
        segment_vectors = encoded_features

        latent_dim = segment_vectors.shape[1]

        df_parallel = pd.DataFrame(segment_vectors, columns=[f'Latent Dimension {i+1}' for i in range(latent_dim)])

    else:
        # Create a DataFrame for easier plotting
        df_parallel = pd.DataFrame(
            segment_vectors,
            columns=get_feature_column_names(segment_vectors.shape[1])
        )

    # Add Segment ID column
    df_parallel['Segment ID'] = np.arange(len(segment_vectors))

    # Extract colors for each segment in the same order as `segment_ids`
    color_array = [tuple(segmentColorDict[seg_id].tolist()) for seg_id in df_parallel['Segment ID']]
    # Convert to 0-255 range
    color_array = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in color_array]
    # Format as "rgb(R, G, B)"
    color_array = [f'rgb{color}' for color in color_array]

    # Normalized levels
    normalized_levels = np.linspace(0, 1, len(segment_vectors))

    # Create color scale of format [[level, color], ...]
    color_scale = [[level, color] for level, color in zip(normalized_levels, color_array)]

    color_column = 'Segment ID'

    # Generate dimensions dynamically from df, excluding the color column
    dimensions = list([
        dict(label=col, values=df_parallel[col]) 
        if col != color_column 
        else dict(label=col, values=df_parallel[col], tickvals=np.linspace(0, len(df_parallel[color_column].unique()) - 1, num=5, dtype=int))
        for col in df_parallel.columns
    ])

    # Create the figure dynamically
    fig = go.Figure(data=[
        go.Parcoords(
            line=dict(
                color=df_parallel[color_column], 
                # colorscale=color_scale  
            ),
            dimensions=dimensions
        )
    ])

    fig.update_layout(
        font=dict(color="white")
    )

    # if hovered_segment_id is not None:
    #     # Highlight the corresponding segment in the parallel coordinates plot
    #     highlighted_segment = df_parallel[df_parallel['Segment ID'] == hovered_segment_id]

    #     # Dim non-selected segments
    #     fig.update_traces(line=dict(color='rgba(0, 0, 0, 0.1)'), selector=dict(mode='lines'))

    #     fig.add_trace(
    #         go.Scatter(
    #             x=highlighted_segment.columns[:-1],
    #             y=highlighted_segment.iloc[0, :-1],
    #             mode='lines',
    #             line=dict(color='black', width=2),
    #             hoverinfo='skip',  # Hide hover info for the highlighted segment,
    #             showlegend=False  # Hide legend for the highlighted segment
    #         )
    #     )

    return fig, df_parallel

# Function to create cluster stats plot for KMeans clustering
def create_cluster_stats_plot(segment_vectors, clustering, cluster_number, cluster_stats, encoded_features, autoencoder_checkbox):
    distortions = []
    K = range(2, 11)

    if 'enable' in autoencoder_checkbox:
        segment_vectors = encoded_features

    if clustering == 'gmm':
        for k in K:
            gmm = GaussianMixture(n_components=k, random_state=42)

            if cluster_stats == 'Elbow':
                gmm.fit(segment_vectors)
                distortions.append(gmm.bic(segment_vectors))
            elif cluster_stats == 'Silhouette':
                cluster_labels = gmm.fit_predict(segment_vectors)
                silhouette_score = metrics.silhouette_score(segment_vectors, cluster_labels)
                distortions.append(silhouette_score)
            elif cluster_stats == 'DBI':
                cluster_labels = gmm.fit_predict(segment_vectors)
                davies_bouldin_score = metrics.davies_bouldin_score(segment_vectors, cluster_labels)            
                distortions.append(davies_bouldin_score)

        if cluster_stats == 'Elbow':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'BIC'}, markers=True)
        elif cluster_stats == 'Silhouette':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Silhouette Score'}, markers=True)
        elif cluster_stats == 'DBI':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Davies-Bouldin Score'}, markers=True)

        # Highlight the point where K = cluster_number
        highlight_x = cluster_number
        highlight_y = distortions[K.index(cluster_number)]

        # Add a scatter point for K=cluster_number
        fig.add_trace(go.Scatter(
            x=[highlight_x],
            y=[highlight_y],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            name=' (Selected)',
            showlegend=False,
            hovertemplate=f'No of Cluster={cluster_number}'
        ))

        fig.update_layout(
            xaxis_title={
                'font': {
                    # 'color': 'white'
                    'color': '#eeeeee'
                }
            },
            yaxis_title={
                'font': {
                    # 'color': 'white'
                    'color': '#eeeeee'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            # Set the background color to light gray
            plot_bgcolor='#222831',
        )

        # Color the line
        fig.update_traces(line=dict(color='#00adb5'))

        fig.update_layout(clickmode='event')

        return fig
    
    elif clustering == 'kmeans':
        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=42)

            if cluster_stats == 'Elbow':
                kmeans.fit(segment_vectors)
                distortions.append(kmeans.inertia_)
            elif cluster_stats == 'Silhouette':
                cluster_labels = kmeans.fit_predict(segment_vectors)
                silhouette_score = metrics.silhouette_score(segment_vectors, cluster_labels)
                distortions.append(silhouette_score)
            elif cluster_stats == 'DBI':
                cluster_labels = kmeans.fit_predict(segment_vectors)
                davies_bouldin_score = metrics.davies_bouldin_score(segment_vectors, cluster_labels)
                distortions.append(davies_bouldin_score)

        if cluster_stats == 'Elbow':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Distortion'}, markers=True)
        elif cluster_stats == 'Silhouette':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Silhouette Score'}, markers=True)
        elif cluster_stats == 'DBI':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Davies-Bouldin Score'}, markers=True)

        # Highlight the point where K = cluster_number
        highlight_x = cluster_number
        highlight_y = distortions[K.index(cluster_number)]

        # Add a scatter point for K=cluster_number
        fig.add_trace(go.Scatter(
            x=[highlight_x],
            y=[highlight_y],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            name=' (Selected)',
            showlegend=False,
            hovertemplate=f'No of Cluster={cluster_number}'
        ))

        fig.update_layout(
            xaxis_title={
                'font': {
                    'color': '#eeeeee'
                }
            },
            yaxis_title={
                'font': {
                    'color': '#eeeeee'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            # Set the background color to light gray
            plot_bgcolor='#222831',
        )

        # Color the line
        fig.update_traces(line=dict(color='#00adb5'))

        fig.update_layout(clickmode='event')

    return fig

# Function to create clusters
def create_clusters(segment_vectors, clustering, cluster_number, encoded_features, autoencoder_checkbox):
    num_clusters = cluster_number

    if 'enable' in autoencoder_checkbox:
        segment_vectors = encoded_features

    if clustering == 'gmm':
        gmm = GaussianMixture(n_components=num_clusters, random_state=42)
        cluster_labels = gmm.fit_predict(segment_vectors)

    elif clustering == 'kmeans':
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(segment_vectors)

    # Initialize selected clusters for swapping
    cluster_color_dict = {}

    colormap = plt.cm.get_cmap("tab10")

    cluster_colors = {}
    for i in range(num_clusters): 
        color = colormap(i)
        cluster_colors[i] = color

    cluster_color_dict = cluster_colors

    for cluster_id in np.unique(cluster_labels):
        cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), cluster_color_dict[cluster_id][:3]))

    return cluster_labels, cluster_color_dict

# Function to create cluster vector plot
def create_cluster_vector_plot(segment_vectors, cluster_labels, visualization, hovered_segment_id, encoded_features, autoencoder_checkbox):
    # if 'enable' in autoencoder_checkbox:
    #     segment_vectors = encoded_features

    # Create a DataFrame for easier plotting
    if visualization == 'pca':
        # Perform PCA for dimensionality reduction
        pca = PCA(n_components=2, random_state=42)
        reduced_data = pca.fit_transform(segment_vectors)

        # Create a DataFrame for easier plotting
        df = pd.DataFrame(reduced_data, columns=['PCA Dimension 1', 'PCA Dimension 2'])

    elif visualization == 'tsne':
        # Perform t-SNE for dimensionality reduction
        tsne = TSNE(n_components=2, random_state=42)
        reduced_data = tsne.fit_transform(segment_vectors)

        # Create a DataFrame for easier plotting
        df = pd.DataFrame(reduced_data, columns=['t-SNE Dimension 1', 't-SNE Dimension 2'])

    elif visualization == 'PC':
        reduced_data = segment_vectors

        # Create a DataFrame for easier plotting
        # if 'enable' in autoencoder_checkbox:
        #     latent_dim = reduced_data.shape[1]

        #     df = pd.DataFrame(reduced_data, columns=[f'Latent Dimension {i+1}' for i in range(latent_dim)])

        # else:
        #     df = pd.DataFrame(reduced_data, columns=['Ce', 'Co', 'Fe', 'Gd'])

        df = pd.DataFrame(
            reduced_data,
            columns=get_feature_column_names(reduced_data.shape[1])
        )

    df['Cluster ID'] = cluster_labels
    # Convert Cluster ID to a string to ensure it's treated as categorical
    df['Cluster ID'] = df['Cluster ID'].astype(str)
    df['Cluster-ID'] = df['Cluster ID'].astype(int)

    segment_labels = np.arange(len(reduced_data))
    df['Segment ID'] = segment_labels

    # Extract Tab10 colors from Matplotlib
    tab10_colors = [plt.get_cmap("tab10")(i) for i in range(len(df['Cluster ID'].unique()))]
    tab10_colors = ["rgb({}, {}, {})".format(int(r*255), int(g*255), int(b*255)) for r, g, b, _ in tab10_colors]

    # Normalized levels
    normalized_levels = np.linspace(0, 1, len(tab10_colors))

    # Create color scale of format [[level, color], ...]
    color_scale = [[level, color] for level, color in zip(normalized_levels, tab10_colors)]

    if visualization == 'pca':
        fig = px.scatter(
            df,
            x='PCA Dimension 1',
            y='PCA Dimension 2',
            color='Cluster ID',
            category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
            hover_data=['Cluster ID', 'Segment ID'],
            labels={"Cluster ID": "Cluster ID"},
            color_discrete_sequence=tab10_colors
        )

    elif visualization == 'tsne':
        fig = px.scatter(
            df,
            x='t-SNE Dimension 1',
            y='t-SNE Dimension 2',
            color='Cluster ID',
            category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
            hover_data=['Cluster ID', 'Segment ID'],
            labels={"Cluster ID": "Cluster ID"},
            color_discrete_sequence=tab10_colors
        )

    elif visualization == 'PC':

        df_copy = df.copy()

        df_copy.drop(columns=['Segment ID', 'Cluster ID'], inplace=True)

        color_column = 'Cluster-ID'

        # Generate dimensions dynamically from df_copy, excluding the color column
        dimensions = list([
            dict(label=col, values=df_copy[col]) 
            if col != color_column 
            else dict(label=col, values=df_copy[col], tickvals=np.arange(len(df_copy[color_column].unique())))
            for col in df_copy.columns
        ])

        # Create the figure dynamically
        fig = go.Figure(data=[
            go.Parcoords(
                line=dict(
                    color=df_copy[color_column], 
                    colorscale=color_scale  
                ),
                dimensions=dimensions
            )
        ])

        fig.update_layout(
            font=dict(color="white")
        )

    if visualization == 'pca' or visualization == 'tsne':
        fig.update_layout(
            xaxis_title={
                'font': {
                    'color': 'white'
                }
            },
            yaxis_title={
                'font': {
                    'color': 'white'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                }
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                }
            }
        )

        fig.update_layout(clickmode='event+select')

        if hovered_segment_id is not None:

            # Highlight the corresponding segment in the t-SNE plot
            highlighted_segment = df[df['Segment ID'] == hovered_segment_id]

            # Dim non-selected segments
            fig.update_traces(marker=dict(opacity=0.3), selector=dict(mode='markers'))

            # Add a trace for the highlighted segment
            fig.add_trace(
                go.Scatter(
                    x=highlighted_segment['t-SNE Dimension 1' if visualization == 'tsne' else 'PCA Dimension 1'],
                    y=highlighted_segment['t-SNE Dimension 2' if visualization == 'tsne' else 'PCA Dimension 2'],
                    mode='markers',
                    marker=dict(size=15, color='black', opacity=1),
                    hoverinfo='skip',  # Hide hover info for the highlighted segment,
                    showlegend=False  # Hide legend for the highlighted segment
                )
            )

    return fig, df

# Function to create final segmented slice
def create_final_image(cluster_labels, cluster_color_dict, resized_image, segments, selected_segment_ids, segmentCordDict):
    # Create an image to store the colors for each pixel
    final_segmented_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    final_segmented_image = final_segmented_image[:, :, :3]

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] >= len(cluster_labels):
                final_segmented_image[i][j] = (0, 0, 0)
            else:
                final_segmented_image[i][j] = cluster_color_dict[cluster_labels[segments[i][j]]]

    # Get all segment IDs
    all_segment_ids = set(segmentCordDict.keys())

    # Determine unselected segments
    unselected_segment_ids = all_segment_ids - set(selected_segment_ids)

    # Dim non-selected segments
    for segment_id in unselected_segment_ids:
        for cord in segmentCordDict[segment_id]:
            # Get original pixel value
            original_pixel = final_segmented_image[cord[0]][cord[1]]
            
            # Apply dimming (reduce intensity)
            final_segmented_image[cord[0]][cord[1]] = (np.array(original_pixel) * 0.2).astype(np.uint8)

    # Create a plotly figure
    fig = px.imshow(final_segmented_image)

    # Update the layout of the figure
    fig.update_layout(
        margin=dict(l=25, r=25, b=25, t=25),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig

# -------------------------------------------------------------------------------

class Autoencoder(nn.Module):
    def __init__(self, input_dim, latent_dim=3):
        super(Autoencoder, self).__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, latent_dim)  # Compress to latent space
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return encoded, decoded

def compute_superpixel_features(image_4ch, superpixels, dropzero_checkbox):
    if 'enable' in dropzero_checkbox:
        num_superpixels = np.max(superpixels)  # Number of unique superpixels
    else:
        num_superpixels = np.max(superpixels) + 1  # Number of unique superpixels

    num_channels = image_4ch.shape[-1]
    features = np.zeros((num_superpixels, num_channels * 2))  # Mean + Std

    for sp_id in range(num_superpixels):
        mask = (superpixels == sp_id)
        pixels = image_4ch[mask]
        if pixels.size > 0:
            features[sp_id, :num_channels] = np.mean(pixels, axis=0)
            features[sp_id, num_channels:] = np.std(pixels, axis=0)

    return features  # Shape: (num_superpixels, 8)

def cluster_autoencoded_features(model, data_tensor, n_clusters=5):
    with torch.no_grad():
        encoded_features, _ = model(data_tensor)

    encoded_features = encoded_features.numpy()
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(encoded_features)
    return kmeans.labels_, encoded_features

def setup_model(input_dimension, dropzero_checkbox):
    # Model Setup
    input_dim = input_dimension
    latent_dim=2

    # Load the trained autoencoder model
    model = Autoencoder(input_dim, latent_dim)

    if 'enable' in dropzero_checkbox:
        model.load_state_dict(torch.load('autoencoder_mean_nozero.pth', map_location=torch.device('cuda' if torch.cuda.is_available() else 'cpu')))
    else:
        model.load_state_dict(torch.load('autoencoder_mean.pth', map_location=torch.device('cuda' if torch.cuda.is_available() else 'cpu')))
        
    model.eval()

    return model

# -------------------------------------------------------------------------------

# Initialize Dash app
# app = dash.Dash(__name__)
app = DashProxy(__name__, transforms=[MultiplexerTransform()])  # Helps to generate the same output from multiple callbacks

# Layout of the app
app.layout = html.Div(
    id="dashboard-server",
    children = [
        html.Div(
            children=[
                # Control Panel
                html.Div(
                    children=[
                        html.H2(children='Control Panel'),

                        # Radio Button for selection of axis for slicing
                        html.Label('Select axis for slicing volume:'),
                        dcc.RadioItems(
                            id='axis-radio',
                            options=[
                                {'label': 'X Axis', 'value': 'x'},
                                {'label': 'Y Axis', 'value': 'y'},
                                {'label': 'Z Axis', 'value': 'z'}
                            ],
                            value = 'x'
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Slider for selecting slice
                        html.Label('Select slice to visualize:'),
                        dcc.Slider(
                            id='slice-slider',
                            min=1,
                            max=volume.shape[0],
                            # min=45,
                            # max=160,
                            step=1,
                            value=75,
                            marks={1: str(1), volume.shape[0]: str(volume.shape[0])},
                            # marks={
                            #     45: {'label': str(45)},
                            #     160: {'label': str(160)}
                            # },
                            tooltip={"placement": "bottom", "always_visible": True},
                            allow_direct_input=False,
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Slider for selecting superpixel count
                        html.Label('Select number of superpixels:'),
                        dcc.Slider(
                            id='superpixel-input',
                            min=100,
                            max=600,
                            step=1,
                            value=450,
                            marks={
                                100: {'label': str(100)},
                                600: {'label': str(600)}
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                            allow_direct_input=False
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable zero-value pixels dropping
                        dcc.Checklist(
                            id='dropzero-checkbox',
                            options=[
                                {'label': 'Drop zero-value pixels', 'value': 'enable'}
                            ],
                            value=['enable']
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Radio Button for selection Visualization Technique
                        html.Label('Select Visualization Technique:'),
                        dcc.RadioItems(
                            id='visualization-radio',
                            options=[
                                {'label': 'PCA', 'value': 'pca'},
                                {'label': 't-SNE', 'value': 'tsne'},
                                {'label': 'Parallel Coordinates', 'value': 'PC'}
                            ],
                            value='PC'
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),
                        
                        # -------------------------------------------------------------------------------

                        # Radio Button for selection Clustering Technique
                        html.Label('Select Clustering Technique:'),
                        dcc.RadioItems(
                            id='clustering-radio',
                            options=[
                                {'label': 'KMeans', 'value': 'kmeans'},
                                {'label': 'GMM', 'value': 'gmm'}
                            ],
                            value='kmeans'
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable clustering
                        dcc.Checklist(
                            id='clustering-checkbox',
                            options=[
                                {'label': 'Enable Clustering', 'value': 'enable'}
                            ],
                            value=[]
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable Autoencoder feature extraction
                        dcc.Checklist(
                            id='autoencoder-checkbox',
                            options=[
                                {'label': 'Enable Autoencoder', 'value': 'enable'}
                            ],
                            value=[]
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Radio Button for viewing Cluster Statistics
                        html.Label('View Cluster Statistics:'),
                        dcc.RadioItems(
                            id='cluster-stats-radio',
                            options=[
                                {'label': 'Elbow Plot', 'value': 'Elbow'},
                                {'label': 'Silhouette Score', 'value': 'Silhouette'},
                                {'label': 'Davies-Bouldin Index', 'value': 'DBI'}
                            ],
                            value='Elbow'
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Add trame button
                        html.Div(
                            children=[
                                html.Button('Visualize in 3D', id='trame-button', n_clicks=0),
                            ],
                            className='trame-button-container',
                            style={'display': 'none'}
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # Add break
                        html.Br(),

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Add reset button
                        html.Div(
                            children=[
                                html.Button('Reset Dashboard', id='reset-button', n_clicks=0),
                            ],
                            className='reset-button-container'
                        ),
                    
                    ],
                    className="control-panel"
                ),

                # -------------------------------------------------------------------------------

                # Display Panel
                html.Div(
                    children=[

                        # Top Half Display
                        html.Div(
                            children=[

                                # Original Slice
                                html.Div(
                                    children=[
                                        html.H3(children='Original Slice'),
                                        dcc.Loading(
                                            id="loading-spinner1",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="slice-plot",
                                                    className="slice-plot-class",    
                                                )  # Graph component wrapped in the loading spinner
                                            ]
                                        ),
                                    ],
                                    className="original-slice"
                                ),

                                # -------------------------------------------------------------------------------

                                # Superpixel Segmentation
                                html.Div(
                                    children=[
                                        html.H3(children='Superpixel Segmentation'),
                                        dcc.Loading(
                                            id="loading-spinner2",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="superpixel-plot",
                                                    className="superpixel-plot-class",
                                                    clear_on_unhover=True
                                                )
                                            ]
                                        ),
                                    ],
                                    className="superpixel-segmentation"
                                ),

                                # -------------------------------------------------------------------------------

                                # Final Segmented Slice
                                html.Div(
                                    children=[
                                        html.H3(children='Final Segmented Slice'),
                                        html.Div(
                                            "Enable clustering to view final segmented slice",
                                            id="final-segmented-slice-text"
                                        ),
                                        html.Div(
                                            children=[
                                                dcc.Graph(
                                                    id='final-plot',
                                                    className="final-plot-class",
                                                ),
                                            ],
                                        ),
                                    ],
                                    className="final-segmented-slice"
                                ),

                            ],
                            className="top-half-display"
                        ),

                        # -------------------------------------------------------------------------------

                        # Bottom Half Display
                        html.Div(
                            children=[

                                # Vector Space Visualization
                                html.Div(
                                    children=[
                                        html.H3(children='Vector Space Visualization'),
                                        dcc.Loading(
                                            id="loading-spinner3",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="vector-plot",
                                                    className="vector-plot-class",
                                                    clear_on_unhover=True
                                                ),  # Graph component wrapped in the loading spinner
                                            ]
                                        ),
                                    ],
                                    id="vector-space-visualization"
                                ),

                                # -------------------------------------------------------------------------------

                                # Vector Space Visualization with Clustering
                                html.Div(
                                    children=[
                                        html.H3(children='Clustered Vector Space Visualization'),
                                        dcc.Loading(
                                            id="loading-spinner4",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="cluster-vector-plot",
                                                    className="cluster-vector-plot-class",
                                                    clear_on_unhover=True
                                                )  # Graph component wrapped in the loading spinner
                                            ]
                                        ),
                                    ],
                                    id="cluster-vector-space-visualization"
                                ),

                                # -------------------------------------------------------------------------------

                                # Cluster Stats Plot for Clustering
                                html.Div(
                                    children=[
                                        html.H3(id="cluster-stats-label", children='Elbow Plot for Clustering'),
                                        dcc.Loading(
                                            id="loading-spinner5",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="elbow-plot",
                                                    className="elbow-plot-class",
                                                )  # Graph component wrapped in the loading spinner
                                            ]
                                        ),
                                    ],
                                    className="elbow-plot"
                                ),
                            ],
                            className="bottom-half-display"
                        ),
                        
                        # -------------------------------------------------------------------------------

                        # Container for embedded 3D content
                        html.Div(id='content-div'),  
                    ],
                    className="display-panel"
                ),

            ], 
            style={'display': 'flex'}
        ),

        # Dummy Div to store intermediate data
        html.Div(id='dummy', style={'display': 'none'}),

        # -------------------------------------------------------------------------------

        # Hidden store to hold intermediate data
        dcc.Store(id='slice-data'),
        dcc.Store(id='superpixel-data'),
        dcc.Store(id='vector-data'),
        dcc.Store(id='cluster-data'),
        dcc.Store(id='cluster-number', data=5),
        dcc.Store(id='class-tracker'),

        # Hidden div to open up app using url query string
        dcc.Location(id="url", refresh=False),
    ]
)

# -------------------------------------------------------------------------------

# Callback for Slice Plot
@app.callback(
    [Output('slice-plot', 'figure'), Output('slice-data', 'data'), Output('class-tracker', 'data')],
    [Input('axis-radio', 'value'), Input('slice-slider', 'value')]
)
def update_slice_plot(axis, slice_num):
    print("------------------------------------------------------------------------------------------------------------")
    print("Updating slice plot...")
    start_time = time.time()
    
    original_slice_fig, resized_image, input_image = create_original_slice(axis, slice_num)
    
    print('Slice plot ready in:', time.time() - start_time)
    return original_slice_fig, json.dumps({'resized_image': resized_image.tolist(), 'input_image': input_image.tolist()}), ".slice-plot-class"

# -------------------------------------------------------------------------------

# Callback for Superpixel Plot
@app.callback(
    [Output('superpixel-plot', 'figure'), Output('superpixel-data', 'data'), Output('clustering-checkbox', 'value'), Output('class-tracker', 'data'), Output('vector-data', 'data')],
    [Input('slice-data', 'data'), Input('vector-plot', 'clickData'), Input('cluster-vector-plot', 'clickData'), Input('superpixel-input', 'value'), Input('dropzero-checkbox', 'value'), Input('vector-plot', 'restyleData'), Input('cluster-vector-plot', 'restyleData'), Input('visualization-radio', 'value'), Input('clustering-checkbox', 'value'), Input('autoencoder-checkbox', 'value'), Input('elbow-plot', 'clickData'), Input('clustering-radio', 'value')],
    [State('superpixel-data', 'data'), State('vector-data', 'data')]
)
def update_superpixel_plot(jsonified_slice_data, vector_click_data1, vector_click_data2, num_superpixels, dropzero_checkbox, restyle_data1, restyle_data2, visualization, clustering_checkbox, autoencoder_checkbox, click_data, clustering, jsonified_superpixel_data, jsonified_vector_data):
    print("--------------------------------")
    print("Updating superpixel plot...")
    start_time = time.time()
    
    ctx_id = ctx.triggered_id.split('.')[0]

    if ctx_id == 'vector-plot' or ctx_id == 'cluster-vector-plot':

        if visualization == "PC":
            if restyle_data1 is not None or restyle_data2 is not None:
                if restyle_data1 is not None and ctx_id == 'vector-plot':
                    restyle_data = restyle_data1
                elif restyle_data2 is not None and ctx_id == 'cluster-vector-plot':
                    restyle_data = restyle_data2

                for key, val in restyle_data[0].items():
                    if 'constraintrange' in key:
                        print(restyle_data)

                        vector_data = json.loads(jsonified_vector_data)
                        superpixel_data = json.loads(jsonified_superpixel_data)

                        segments = np.array(superpixel_data['segments'])
                        highlighted_image = np.array(superpixel_data['image'])
                        segment_coords = superpixel_data['trace_info']['segment_coords']
                        segment_IDs = superpixel_data['trace_info']['segment_ids']
                        segment_IDs = [np.int32(num) for num in segment_IDs]

                        # Retrieve DataFrame
                        df_original = pd.read_json(vector_data["dataframe"], orient="split")
                        updated_filters = vector_data["filters"].copy()

                        # Extract dimension index and label
                        dimension_index = int(key.split('[')[1].split(']')[0])
                        dimension_label = df_original.columns[dimension_index]

                        if val is None or val == []:  # If filter is removed, delete it
                            updated_filters.pop(dimension_label, None)
                        else:
                            updated_filters[dimension_label] = val[0]

                        print(updated_filters)

                        # Filter the DataFrame based on the updated filters
                        filtered_df  = df_original.copy()

                        print("Applying filters...")

                        # Apply all active filters
                        for column_name, filter_ranges in updated_filters.items():
                            print("Filter ranges", filter_ranges)

                            multiple_filter = False

                            if isinstance(filter_ranges[0], list):
                                multiple_filter = True

                            if multiple_filter:
                                # Take into account multiple filters for the same column
                                mask = np.zeros(len(filtered_df), dtype=bool)
                                for filter in filter_ranges:
                                    mask |= (filtered_df[column_name] >= filter[0]) & (filtered_df[column_name] <= filter[1])
                                    
                            else:
                                mask = (filtered_df[column_name] >= filter_ranges[0]) & (filtered_df[column_name] <= filter_ranges[1])
                                
                            filtered_df = filtered_df[mask]

                        # Extract the segment IDs
                        segment_ids = filtered_df['Segment ID'].tolist()

                        highlighted_image[~np.isin(segments, segment_ids)] *= 0.3  # Dim non-selected segments

                        # Create a new figure with highlighted segment
                        superpixel_fig = px.imshow(highlighted_image)

                        # Create a Plotly scatter plot for segment IDs at each pixel location
                        scatter_trace = {
                            'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
                            'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
                            'mode': 'markers',
                            'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
                            'text': [seg_id for seg_id in segment_IDs],  # Text for hover
                            'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
                        }

                        # Add the scatter trace to the figure
                        superpixel_fig.add_traces([scatter_trace])

                        # Update the layout of the figure
                        superpixel_fig.update_layout(
                            margin=dict(l=0, r=0, b=0, t=0),
                            xaxis=dict(visible=False),
                            yaxis=dict(visible=False),
                            coloraxis_showscale=False
                        )

                        print('Superpixel plot ready in:', time.time() - start_time)

                        # Create vector_data JSON
                        vector_data["filters"] = updated_filters

                        return superpixel_fig, dash.no_update, dash.no_update, dash.no_update, json.dumps(vector_data)

        if vector_click_data1 is None and vector_click_data2 is None:
            if jsonified_superpixel_data is not None:
                superpixel_data = json.loads(jsonified_superpixel_data)

                segments = np.array(superpixel_data['segments'])
                boundary_image = np.array(superpixel_data['image'])
                segment_coords = superpixel_data['trace_info']['segment_coords']
                segment_ids = superpixel_data['trace_info']['segment_ids']
                segment_ids = [np.int32(num) for num in segment_ids]

                # Create a Plotly scatter plot for segment IDs at each pixel location
                scatter_trace = {
                    'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
                    'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
                    'mode': 'markers',
                    'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
                    'text': [seg_id for seg_id in segment_ids],  # Text for hover
                    'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
                }

                # Create a plotly figure
                superpixel_fig = px.imshow(boundary_image)

                # Add the scatter trace to the figure
                superpixel_fig.add_traces([scatter_trace])

                # Update the layout of the figure
                superpixel_fig.update_layout(
                    margin=dict(l=0, r=0, b=0, t=0),
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    coloraxis_showscale=False
                )

                print('Superpixel plot ready in:', time.time() - start_time)

                return superpixel_fig, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        else:
            if ctx_id == 'vector-plot':
                clicked_segment_id = vector_click_data1['points'][0]['marker.color']
            elif ctx_id == 'cluster-vector-plot':
                clicked_segment_id = vector_click_data2['points'][0]['customdata'][1]

            if jsonified_superpixel_data is not None:
                superpixel_data = json.loads(jsonified_superpixel_data)

                segments = np.array(superpixel_data['segments'])
                highlighted_image = np.array(superpixel_data['image'])
                segment_coords = superpixel_data['trace_info']['segment_coords']
                segment_IDs = superpixel_data['trace_info']['segment_ids']
                segment_IDs = [np.int32(num) for num in segment_IDs]

                highlighted_image[segments != clicked_segment_id] *= 0.3  # Dim non-selected segments

                # Create a new figure with highlighted segment
                superpixel_fig = px.imshow(highlighted_image)

                # Create a Plotly scatter plot for segment IDs at each pixel location
                scatter_trace = {
                    'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
                    'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
                    'mode': 'markers',
                    'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
                    'text': [seg_id for seg_id in segment_IDs],  # Text for hover
                    'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
                }

                # Add the scatter trace to the figure
                superpixel_fig.add_traces([scatter_trace])

                # Update the layout of the figure
                superpixel_fig.update_layout(
                    margin=dict(l=0, r=0, b=0, t=0),
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    coloraxis_showscale=False
                )

                print('Superpixel plot ready in:', time.time() - start_time)

                return superpixel_fig, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    elif ctx_id == 'visualization-radio' or ctx_id == 'clustering-checkbox' or ctx_id == 'autoencoder-checkbox' or ctx_id == 'elbow-plot' or ctx_id == 'clustering-radio':
        if jsonified_vector_data is None:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        vector_data = json.loads(jsonified_vector_data)
        # filters = vector_data['filters']

        # if visualization == "PC" and filters == {}:
        #     print('Superpixel plot ready in:', time.time() - start_time)
        #     return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Clear data selection from superpixel plot
        superpixel_data = json.loads(jsonified_superpixel_data)

        segments = np.array(superpixel_data['segments'])
        boundary_image = np.array(superpixel_data['image'])
        segment_coords = superpixel_data['trace_info']['segment_coords']
        segment_ids = superpixel_data['trace_info']['segment_ids']
        segment_ids = [np.int32(num) for num in segment_ids]

        # Create a Plotly scatter plot for segment IDs at each pixel location
        scatter_trace = {
            'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
            'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
            'mode': 'markers',
            'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
            'text': [seg_id for seg_id in segment_ids],  # Text for hover
            'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
        }

        # Create a plotly figure
        superpixel_fig = px.imshow(boundary_image)

        # Add the scatter trace to the figure
        superpixel_fig.add_traces([scatter_trace])

        # Update the layout of the figure
        superpixel_fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            coloraxis_showscale=False
        )

        print('Superpixel plot ready in:', time.time() - start_time)

        return superpixel_fig, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    else:

        slice_data = json.loads(jsonified_slice_data)

        # Convert stored lists back to numpy arrays
        resized_image = np.array(slice_data['resized_image'])
        input_image = np.array(slice_data['input_image'], dtype=np.uint8)
        
        superpixel_fig, segments, boundary_image, trace_info = create_superpixels(resized_image, input_image, num_superpixels, dropzero_checkbox)

        # Compute superpixel features for testing data
        superpixel_features = compute_superpixel_features(resized_image, segments, dropzero_checkbox)

        # Load the scaler
        if 'enable' in dropzero_checkbox:
            with open("scaler_autoencoder_mean_nozero.pkl", "rb") as f:
                loaded_scaler = pickle.load(f)
        else:
            with open("scaler_autoencoder_mean.pkl", "rb") as f:
                loaded_scaler = pickle.load(f)

        # Normalize the data
        test_data_normalized = loaded_scaler.transform(superpixel_features)

        # Convert to PyTorch tensor
        test_data_tensor = torch.tensor(test_data_normalized, dtype=torch.float32)

        # Setup the model
        model = setup_model(test_data_tensor.shape[1], dropzero_checkbox)

        with torch.no_grad():
            encoded_features, _ = model(test_data_tensor)

        encoded_features = encoded_features.numpy()
        
        print('Superpixel plot ready in:', time.time() - start_time)

        return superpixel_fig, json.dumps({'segments': segments.tolist(), 'image': boundary_image.tolist(), 'trace_info': trace_info, 'encoded_features': encoded_features.tolist()}), [], ".superpixel-plot-class", dash.no_update

# -------------------------------------------------------------------------------

# Callback for Vector Space Visualization Plot
@app.callback(
    [Output('vector-plot', 'figure'), Output('vector-data', 'data'), Output('class-tracker', 'data')],
    [Input('slice-data', 'data'), Input('superpixel-data', 'data'), Input('visualization-radio', 'value'), Input('clustering-checkbox', 'value'), Input('autoencoder-checkbox', 'value')],
    [State('vector-data', 'data'), State('dropzero-checkbox', 'value')]
)
def update_vector_plot(jsonified_slice_data, jsonified_superpixel_data, visualization, checkbox_value, autoencoder_checkbox, jsonified_vector_data, dropzero_checkbox):
    if checkbox_value == ['enable']:
        return dash.no_update, dash.no_update, dash.no_update
    
    print("--------------------------------")
    print("Updating vector plot...")
    start_time = time.time()

    slice_data = json.loads(jsonified_slice_data)
    superpixel_data = json.loads(jsonified_superpixel_data)

    # Convert stored lists back to numpy arrays
    resized_image = np.array(slice_data['resized_image'])
    input_image = np.array(slice_data['input_image'], dtype=np.uint8)
    segments = np.array(superpixel_data['segments'])
    encoded_features = np.array(superpixel_data['encoded_features'])

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and pixel colors as the value
    segmentColorDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentColorDict:
                segmentColorDict[segments[i][j]] = []
            segmentColorDict[segments[i][j]].append(input_image[i][j] / 255.0)

    # Replace the segment ID with the mean color of the segment
    for key in segmentColorDict.keys():
        segmentColorDict[key] = np.mean(segmentColorDict[key], axis=0)

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and pixel coordinates as the value
    segmentCordDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentCordDict:
                segmentCordDict[segments[i][j]] = []
            segmentCordDict[segments[i][j]].append((i, j))

    # -------------------------------------------------------------------------------
    
    unique_segments = np.unique(segments)  # Get unique segment IDs
    segment_vectors = []

    # Drop last segment as it is the zero-value pixel superpixel
    if 'enable' in dropzero_checkbox:
        unique_segments = unique_segments[:-1]
    
    # Loop through each segment ID and compute mean feature vector
    for segment_id in unique_segments:
        mask = (segments == segment_id)  # Mask for current segment
        mean_color = np.mean(resized_image[mask], axis=0)  # Mean of pixel values in this segment
        segment_vectors.append(mean_color)

    # Convert the list of vectors to a NumPy array
    segment_vectors = np.array(segment_vectors)

    # -------------------------------------------------------------------------------

    if visualization == 'pca':
        vector_space_fig, df = create_pca_plot(segment_vectors, segmentColorDict, None, encoded_features, autoencoder_checkbox)

    elif visualization == 'tsne':
        vector_space_fig, df = create_tsne_plot(segment_vectors, segmentColorDict, None, encoded_features, autoencoder_checkbox)

    elif visualization == 'PC':
        vector_space_fig, df = create_parallel_coordinates_plot(segment_vectors, segmentColorDict, None, encoded_features, autoencoder_checkbox)
    
    print('Vector plot ready in:', time.time() - start_time)

    segmentColorDict_data = {int(key): value.tolist() for key, value in segmentColorDict.items()}

    segmentCordDict_data = {int(key): value for key, value in segmentCordDict.items()}

    return vector_space_fig, json.dumps({'segment_vectors': segment_vectors.tolist(), 'segmentColorDict': segmentColorDict_data, "segmentCordDict": segmentCordDict_data, "dataframe": df.to_json(orient="split"), "filters": {}, "clicks": []}), ".vector-plot-class"

# -------------------------------------------------------------------------------

# Callback for Cluster Stats Plot
@app.callback(
    [Output('elbow-plot', 'figure'), Output('cluster-number', 'data'), Output('cluster-stats-label', 'children'), Output('class-tracker', 'data')],
    [Input('vector-data', 'data'), Input('clustering-radio', 'value'), Input('elbow-plot', 'clickData'), Input('cluster-stats-radio', 'value'), Input('autoencoder-checkbox', 'value')],
    [State('cluster-number', 'data'), State('superpixel-data', 'data')],
    prevent_initial_call=True
)
def update_cluster_stats_plot(jsonified_vector_data, clustering, click_data, cluster_stats, autoencoder_checkbox, cluster_number_data, jsonified_superpixel_data):
    ctx_id = ctx.triggered_id.split('.')[0]

    print("--------------------------------")
    print("Updating cluster stats plot...")
    start_time = time.time()

    vector_data = json.loads(jsonified_vector_data)
    superpixel_data = json.loads(jsonified_superpixel_data)

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])
    encoded_features = np.array(superpixel_data['encoded_features'])

    # -------------------------------------------------------------------------------

    if ctx_id == "elbow-plot" and click_data is not None:
        cluster_number = click_data['points'][0]['x']

        if cluster_number == cluster_number_data:
            print('Cluster stats plot ready in:', time.time() - start_time)
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        else:
            final_cluster_number_data = cluster_number

    else:
        final_cluster_number_data = cluster_number_data

    elbow_fig = create_cluster_stats_plot(segment_vectors, clustering, final_cluster_number_data, cluster_stats, encoded_features, autoencoder_checkbox)

    plot_label = cluster_stats + ' Plot for Clustering'

    print('Cluster stats plot ready in:', time.time() - start_time)

    if cluster_number_data == final_cluster_number_data:
        return elbow_fig, dash.no_update, plot_label, ".elbow-plot-class"
    else:
        return elbow_fig, final_cluster_number_data, plot_label, ".elbow-plot-class"

# -------------------------------------------------------------------------------

# Callback for enabling/disabling clustering
@app.callback(
    [Output('final-plot', 'style'), Output('final-segmented-slice-text', 'style'), Output('vector-space-visualization', 'style'), Output('cluster-vector-space-visualization', 'style')],
    [Input('clustering-checkbox', 'value')]
)
def enable_clustering(checkbox_value):
    if 'enable' in checkbox_value:
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'inline-block'}
    else:
        return {'display': 'none'}, {'display': 'flex'}, {'display': 'inline-block'}, {'display': 'none'}

# -------------------------------------------------------------------------------

# Callback for performing clustering
@app.callback(
    Output('cluster-data', 'data'),
    [Input('clustering-radio', 'value'), Input('cluster-number', 'data'), Input('autoencoder-checkbox', 'value'), Input('clustering-checkbox', 'value')],
    [State('superpixel-data', 'data'), State('vector-data', 'data')],
    prevent_initial_call=True
)
def perform_clustering(clustering, cluster_number, autoencoder_checkbox, clustering_checkbox, jsonified_superpixel_data, jsonified_vector_data):
    if jsonified_superpixel_data is None or jsonified_vector_data is None:
        return dash.no_update

    if 'enable' not in clustering_checkbox:
        return dash.no_update
    
    print("--------------------------------")
    print("Performing clustering...")
    start_time = time.time()

    vector_data = json.loads(jsonified_vector_data)
    superpixel_data = json.loads(jsonified_superpixel_data)

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])
    encoded_features = np.array(superpixel_data['encoded_features'])

    # -------------------------------------------------------------------------------

    cluster_labels, cluster_color_dict = create_clusters(segment_vectors, clustering, cluster_number, encoded_features, autoencoder_checkbox)

    print('Clustering done in:', time.time() - start_time)

    return json.dumps({'cluster_labels': cluster_labels.tolist(), 'cluster_color_dict': cluster_color_dict})

# -------------------------------------------------------------------------------

# Callback for updating vector plot with clustering
@app.callback(
    [Output('cluster-vector-plot', 'figure'), Output('class-tracker', 'data'), Output('vector-data', 'data')],
    [Input('cluster-data', 'data'), Input('visualization-radio', 'value'), Input('clustering-checkbox', 'value'), Input('autoencoder-checkbox', 'value'), Input('superpixel-data', 'data')],
    [State('vector-data', 'data')], 
    prevent_initial_call=True
)
def update_cluster_vector_plot(jsonified_cluster_data, visualization, checkbox_value, autoencoder_checkbox, jsonified_superpixel_data, jsonified_vector_data):
    if checkbox_value == []:
        return dash.no_update, dash.no_update, dash.no_update
    
    if jsonified_vector_data is None or jsonified_cluster_data is None or jsonified_superpixel_data is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    print("--------------------------------")
    print("Updating cluster vector plot...")
    start_time = time.time()

    vector_data = json.loads(jsonified_vector_data)
    cluster_data = json.loads(jsonified_cluster_data)
    superpixel_data = json.loads(jsonified_superpixel_data)

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])
    cluster_labels = np.array(cluster_data['cluster_labels'])
    encoded_features = np.array(superpixel_data['encoded_features'])

    cluster_vector_plot_fig, df = create_cluster_vector_plot(segment_vectors, cluster_labels, visualization, None, encoded_features, autoencoder_checkbox)

    print('Cluster vector plot ready in:', time.time() - start_time)

    # Create vector_data JSON
    vector_data["dataframe"] = df.to_json(orient="split")
    vector_data["filters"] = {}

    return cluster_vector_plot_fig, ".cluster-vector-plot-class", json.dumps(vector_data)

# -------------------------------------------------------------------------------

# Callback for Final Segmented Slice
@app.callback(
    [Output('final-plot', 'figure'), Output('class-tracker', 'data')],
    [Input('cluster-data', 'data'), Input('slice-data', 'data'), Input('superpixel-data', 'data'), Input('cluster-vector-plot', 'restyleData'), Input('visualization-radio', 'value')],
    [State('class-tracker', 'data'), State('vector-data', 'data'), State('clustering-checkbox', 'value')],
    prevent_initial_call=True
)
def update_final_plot(jsonified_cluster_data, jsonified_slice_data, jsonified_superpixel_data, restyle_data, visualization, class_tracker, jsonified_vector_data, clustering_checkbox):
    if jsonified_cluster_data is None or jsonified_slice_data is None or jsonified_superpixel_data is None:
        return dash.no_update, dash.no_update

    if 'enable' not in clustering_checkbox:
        return dash.no_update, dash.no_update

    print("--------------------------------")
    print("Updating final segmented slice...")
    start_time = time.time()

    cluster_data = json.loads(jsonified_cluster_data)
    slice_data = json.loads(jsonified_slice_data)
    superpixel_data = json.loads(jsonified_superpixel_data)
    vector_data = json.loads(jsonified_vector_data)

    # Convert stored lists back to numpy arrays
    cluster_labels = np.array(cluster_data['cluster_labels'])
    cluster_color_dict = cluster_data['cluster_color_dict']
    resized_image = np.array(slice_data['resized_image'])
    segments = np.array(superpixel_data['segments'])

    # Convert the keys of the dictionary to integers
    cluster_color_dict = {int(k): v for k, v in cluster_color_dict.items()}

    # convert the values of the dictionary to tuples
    cluster_color_dict = {k: tuple(v) for k, v in cluster_color_dict.items()}

    # -------------------------------------------------------------------------------

    ctx_id = ctx.triggered_id.split('.')[0]

    if ctx_id == 'cluster-vector-plot' and visualization == 'PC':
        if restyle_data is not None:
            for key, val in restyle_data[0].items():
                if 'constraintrange' in key:
                    print(restyle_data)

                    # Retrieve DataFrame
                    df_original = pd.read_json(vector_data["dataframe"], orient="split")
                    updated_filters = vector_data["filters"].copy()
                    segmentCordDict = vector_data["segmentCordDict"]
                    segmentCordDict = {np.int32(key): np.array(value) for key, value in segmentCordDict.items()}

                    # Extract dimension index and label
                    dimension_index = int(key.split('[')[1].split(']')[0])
                    dimension_label = df_original.columns[dimension_index]

                    if val is None or val == []:  # If filter is removed, delete it
                        updated_filters.pop(dimension_label, None)
                    else:
                        updated_filters[dimension_label] = val[0]

                    print(updated_filters)

                    # Filter the DataFrame based on the updated filters
                    filtered_df  = df_original.copy()

                    print("Applying filters...")

                    # Apply all active filters
                    for column_name, filter_ranges in updated_filters.items():
                        print("Filter ranges", filter_ranges)

                        multiple_filter = False

                        if isinstance(filter_ranges[0], list):
                            multiple_filter = True

                        if multiple_filter:
                            # Take into account multiple filters for the same column
                            mask = np.zeros(len(filtered_df), dtype=bool)
                            for filter in filter_ranges:
                                mask |= (filtered_df[column_name] >= filter[0]) & (filtered_df[column_name] <= filter[1])
                                
                        else:
                            mask = (filtered_df[column_name] >= filter_ranges[0]) & (filtered_df[column_name] <= filter_ranges[1])
                            
                        filtered_df = filtered_df[mask]

                    # Extract the segment IDs
                    selected_segment_ids = filtered_df['Segment ID'].tolist()

                    final_fig = create_final_image(cluster_labels, cluster_color_dict, resized_image, segments, selected_segment_ids, segmentCordDict)

                    return final_fig, dash.no_update

    else:

        final_fig = create_final_image(cluster_labels, cluster_color_dict, resized_image, segments, [], {})

        if class_tracker != ".cluster-vector-plot-class":
            # Delay the update of the class tracker to allow the cluster vector plot to be rendered first
            time.sleep(1)

        print('Final segmented slice ready in:', time.time() - start_time)

        return final_fig, ".final-plot-class"

# -------------------------------------------------------------------------------

# Callback for resetting the dashboard
@app.callback(
    [Output('axis-radio', 'value'), Output('slice-slider', 'value'), Output('cluster-number', 'data'), Output('visualization-radio', 'value'), Output('cluster-stats-radio', 'value'), Output('clustering-radio', 'value'), Output('autoencoder-checkbox', 'value'), Output('clustering-checkbox', 'value')],
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_dashboard(n_clicks):
    if n_clicks > 0:
        return "x", 130, 5, "PC", "Elbow", "kmeans", [], []

# -------------------------------------------------------------------------------
# Visualize 3D volume inside Dash app
@app.callback(
    Output('content-div', 'children'),
    Input('trame-button', 'n_clicks'),
    [State('axis-radio', 'value'), State('slice-slider', 'value')],
    prevent_initial_call=True
)
def embed_page(n_clicks, slice_axis, selected_slice):
    print("--------------------------------")
    print("Visualizing in 3D...")
    print(f"Slice axis: {slice_axis}, Selected slice: {selected_slice}")
    print("--------------------------------")

    query_params = urllib.parse.urlencode({
        'timestamp': time.time(),
        'slice_axis': slice_axis,
        'selected_slice': selected_slice,
    })

    return html.Iframe(
        src=f'http://localhost:8080?{query_params}',
        style={
            'width': '100%',
            'height': '600px',
            'border': 'none'
        }
    )

# -------------------------------------------------------------------------------

# Clientside callback to trigger JavaScript
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="changeStyle"),
    Output("dummy", "children"),  # Dummy output
    Input("class-tracker", "data"),
    prevent_initial_call=True
)

# -------------------------------------------------------------------------------
# Function to open up 2D view from 3D view with query parameters
@app.callback(
    [Output('axis-radio', 'value'), Output('slice-slider', 'value')],
    Input("url", "search")  # This is the query string part (e.g., ?axis=x&index=3)
)
def display_query_params(search):
    if search:
        params = urllib.parse.parse_qs(search.lstrip('?'))
        axis = params.get("axis", ["z"])[0]
        index = params.get("index", ["0"])[0]
        data = params.get("data", [""])[0]
        print(f"Axis: {axis}, Index: {index}, Data: {data}")
        return axis, int(index)
    
    return dash.no_update, dash.no_update

# --------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True, use_reloader=True)
    app.run(dev_tools_hot_reload=True, debug=True)  # Disable hot reload to prevent multiple threads
