import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte
from skimage.color import label2rgb
import math
import random
import matplotlib.colors as mcolors
import warnings
import matplotlib.patheffects as patheffects
import cv2
from sklearn.metrics.pairwise import cosine_distances

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
def GBCtoHCL_ring(CX, CY):
    if CX * CX + CY * CY > 0.999999:
        return mcolors.to_rgba((0, 0, 0))  # Return black (similar to d3.rgb(0, 0, 0))

    # Compute the hue angle
    h = math.atan2(CY, CX) + math.pi / 2
    if h < 0:
        h = h + 2 * math.pi
    if h > 2 * math.pi:
        h = h - 2 * math.pi

    # Convert hue to degrees
    h = (h / math.pi) * 180

    # Saturation (distance from the origin)
    s = math.sqrt(CX**2 + CY**2)

    # Lightness (constant value)
    l = 0.55

    # Normalize hue to [0, 1] for HSL color space (as used by matplotlib)
    h /= 360.0
    s = s  # Maintain saturation as calculated
    l = l  # Use constant lightness

    # Convert HSL to RGB using matplotlib
    return mcolors.hex2color("#C7D9E8")

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

# Convert to color based on CX, CY (using HCL color space approximation)
def CoordToColor(CX, CY):
    CX, CY = ConstrainInUnit(CX, CY)
    return GBCtoHCL2(CX, CY)

# Function to get color from ratio
def getColorfromRatio(ratio):
    ss = GBC(np.array([ratio]), 0.0)[0][:2]

    color = CoordToColor(ss[0], ss[1])

    return (np.array(color)[:3] * 255).astype(int)

# Function to apply additive log-ratio (ALR) transformation
def alr_transform(image):
    # Avoid division by zero by adding a small constant (epsilon)
    epsilon = 1e-10
    # Use the last channel as the reference channel for ALR
    reference_channel = image[..., -1]
    # Perform ALR transformation on all other channels relative to the reference channel
    alr_image = np.log((image[..., :-1] + epsilon) / (reference_channel[..., np.newaxis] + epsilon))
    return alr_image

def initialize_cluster_centers(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform grid.
    """
    rows, cols, _ = data.shape
    centers = []
    for r in range(grid_spacing // 2, rows, grid_spacing):
        for c in range(grid_spacing // 2, cols, grid_spacing):
            centers.append([r, c] + list(data[r, c]))
    return np.array(centers)

def calculate_distance(pixel, center, spatial_weight, feature_weight):
    """
    Compute the combined distance between a pixel and a cluster center.
    """
    spatial_dist = np.linalg.norm(pixel[:2] - center[:2])
    feature_dist = np.linalg.norm(pixel[2:] - center[2:])
    return np.sqrt((spatial_dist / spatial_weight)**2 + (feature_dist / feature_weight)**2)

# Custom SLIC function with cosine distance metric
def custom_slic(data, num_superpixels, spatial_weight=5):
    """
    Perform SLIC segmentation on 4D input data (metal concentrations per pixel).
    """
    rows, cols, num_features = data.shape
    grid_spacing = int(np.sqrt((rows * cols) / num_superpixels))
    feature_weight = np.std(data.reshape(-1, num_features), axis=0).mean()

    # Initialize cluster centers
    cluster_centers = initialize_cluster_centers(data, num_superpixels, grid_spacing)
    labels = -1 * np.ones((rows, cols), dtype=int)
    distances = np.full((rows, cols), np.inf)

    # Iterate until convergence
    for _ in range(20):  # Number of iterations
        for idx, center in enumerate(cluster_centers):
            r, c = int(center[0]), int(center[1])
            for dr in range(-grid_spacing, grid_spacing + 1):
                for dc in range(-grid_spacing, grid_spacing + 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        pixel = [rr, cc] + list(data[rr, cc])
                        distance = calculate_distance(pixel, center, spatial_weight, feature_weight)
                        if distance < distances[rr, cc]:
                            distances[rr, cc] = distance
                            labels[rr, cc] = idx

        # Update cluster centers
        new_centers = np.zeros_like(cluster_centers)
        counts = np.zeros(cluster_centers.shape[0], dtype=int)
        for r in range(rows):
            for c in range(cols):
                label = labels[r, c]
                new_centers[label][:2] += [r, c]
                new_centers[label][2:] += data[r, c]
                counts[label] += 1

        for i in range(len(cluster_centers)):
            if counts[i] > 0:
                new_centers[i] /= counts[i]

        cluster_centers = new_centers

    return labels, cluster_centers

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

# Updated weight function to include both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""
    # Mean color difference
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    # Variance difference
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)

    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    
    return {'weight': total_weight}

# Update the merge function to store variance during merging
def merge_mean_color_and_variance(graph, src, dst):
    """Merging two regions, updating both mean color and variance."""
    # Merge color statistics
    graph.nodes[dst]['total color'] += graph.nodes[src]['total color']
    graph.nodes[dst]['pixel count'] += graph.nodes[src]['pixel count']
    graph.nodes[dst]['mean color'] = (graph.nodes[dst]['total color'] /
                                      graph.nodes[dst]['pixel count'])

    # Merge variance statistics
    total_pixels_dst = graph.nodes[dst]['pixel count']
    total_pixels_src = graph.nodes[src]['pixel count']
    
    # Weighted update for variance
    graph.nodes[dst]['variance'] = ((total_pixels_dst * graph.nodes[dst]['variance'] +
                                     total_pixels_src * graph.nodes[src]['variance']) /
                                    (total_pixels_dst + total_pixels_src))
    
# Updated weight function to include both mean log-ratio (ALR) and variance differences
def weight_mean_alr_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean log-ratio (ALR) and variance similarity."""
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_alr_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)

    total_weight = mean_alr_weight + var_weight
    
    return {'weight': total_weight}

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../../xray_volume.npy')

# Normalize the value of each voxel so that the sum of all channels is 1
# volume = volume / 255

# -------------------------------------------------------------------------------

# Create a list having all the voxels
voxels = []
for x in range(volume.shape[0]):
    for y in range(volume.shape[1]):
        for z in range(volume.shape[2]):
            voxels.append(volume[x][y][z])

# Convert the list to a numpy array
voxels = np.array(voxels)
print(voxels.shape)

# Drop all the voxels having all the channels as 0
voxels = voxels[~np.all(voxels == 0, axis=1)]
print(voxels.shape)

# Downsample the voxels to 69317
# voxels = voxels[:69317]
# print(voxels.shape)
# print(voxels[0])

# -------------------------------------------------------------------------------

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [130]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue

    image = volume[x, :, :]
    print(image.shape)

    # -------------------------------------------------------------------------------
    # Zoom in on the center of the image
    # -------------------------------------------------------------------------------

    # Define a zoom factor (increase this value to zoom in more)
    zoom_factor = 1.4

    resized_image = cropImage(image, zoom_factor)

    # -------------------------------------------------------------------------------

    # Create an input image to store the colors for each pixel
    input_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    input_image = input_image[:, :, :3]

    # Loop though each pixel in the image and assign custom colors based on Radviz
    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            # If all channels are 0, assign black color
            if np.all(resized_image[i][j] == 0):
                input_image[i][j] = [0, 0, 0]
            else:
                input_image[i][j] = getColorfromRatio(resized_image[i][j])

    # -------------------------------------------------------------------------------

    # Apply SLIC segmentation on the RGB values fro RadViz
    # segments = segmentation.slic(resized_image, n_segments=200, compactness=30, start_label=1)

    segments, cluster_centers = custom_slic(resized_image, 450)

    # -------------------------------------------------------------------------------

    # Create a Region Adjacency Graph (RAG) based on the superpixels
    rag = graph.rag_mean_color(input_image, segments)

    # Initialize variance for each node in the RAG
    for region in rag.nodes:
        # Extract the pixels of the current superpixel
        mask = (segments == region)
        pixels = input_image[mask]

        # Calculate variance for each color channel (R, G, B)
        variance = np.var(pixels, axis=0)
        
        # Store variance in the RAG
        rag.nodes[region]['variance'] = variance

    # -------------------------------------------------------------------------------

    # Apply hierarchical merging using the mean color similarity
    labels = graph.merge_hierarchical(segments, rag, thresh=2.5, rag_copy=False,
                                    in_place_merge=True,
                                    merge_func=merge_mean_color_and_variance,
                                    weight_func=weight_mean_color_and_variance)

    # -------------------------------------------------------------------------------

    plt.figure(figsize=(16, 5))

    # Visualize the Original image 
    plt.subplot(1, 3, 1)
    plt.imshow(input_image) 
    plt.title('Original Image')
    plt.axis('off')

    # Visualize the superpixel-boundary marked image
    plt.subplot(1, 3, 2)
    plt.imshow(mark_boundaries(input_image, segments))
    plt.title('SLIC Superpixel')
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(mark_boundaries(input_image, labels))
    plt.title('Hierarchical Clustering Segmentation')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    plt.show()
