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

# Function to apply additive log-ratio (ALR) transformation
def alr_transform(image):
    # Avoid division by zero by adding a small constant (epsilon)
    epsilon = 1e-10
    # Use the last channel as the reference channel for ALR
    reference_channel = image[..., -1]
    # Perform ALR transformation on all other channels relative to the reference channel
    alr_image = np.log((image[..., :-1] + epsilon) / (reference_channel[..., np.newaxis] + epsilon))
    return alr_image

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

def find_optimal_threshold(distances, bins=50):
    hist, bin_edges = np.histogram(distances, bins=bins, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Find peaks in the histogram
    peaks, _ = find_peaks(hist)
    
    if len(peaks) > 0:
        elbow_index = peaks[0]  # Take the first significant peak
        optimal_threshold = bin_centers[elbow_index]
    else:
        optimal_threshold = np.percentile(distances, 5)  # Default to lower 5th percentile if no clear peak
    
    # Plot histogram and chosen threshold
    plt.figure(figsize=(8, 6))
    plt.hist(distances, bins=bins, alpha=0.7, color='blue', density=True)
    plt.axvline(optimal_threshold, color='red', linestyle='dashed', linewidth=2, label=f'Threshold: {optimal_threshold:.4f}')
    plt.xlabel("Distance")
    plt.ylabel("Density")
    plt.title("Optimal Distance Threshold Selection")
    plt.legend()
    plt.show()
    
    return optimal_threshold

# -------------------------------------------------------------------------------

def initialize_cluster_centers2(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers on a uniform grid, ensuring all parts of the image are covered.
    """
    rows, cols, _ = data.shape
    # Calculate the approximate number of centers along each dimension
    num_centers_per_row = int(np.sqrt(num_superpixels))
    num_centers_per_col = num_superpixels // num_centers_per_row

    # Adjust spacing to fit the image dimensions
    row_spacing = rows // num_centers_per_row
    col_spacing = cols // num_centers_per_col

    centers = []
    for i in range(num_centers_per_row):
        for j in range(num_centers_per_col):
            r = min(row_spacing * i + row_spacing // 2, rows - 1)
            c = min(col_spacing * j + col_spacing // 2, cols - 1)
            centers.append([r, c] + list(data[r, c]))

    return np.array(centers)


def initialize_cluster_centers1(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform grid, ensuring even distribution.
    """
    rows, cols, _ = data.shape
    print("Rows:", rows, "Cols:", cols)
    centers = []

    # Calculate approximate number of centers per row and column
    num_centers_per_row = int(np.sqrt(num_superpixels * (rows / cols)))
    num_centers_per_col = int(np.sqrt(num_superpixels * (cols / rows)))

    # Adjust grid spacing for uniform distribution
    row_spacing = rows // num_centers_per_row
    col_spacing = cols // num_centers_per_col

    # Generate centers across the grid
    for r in range(row_spacing // 2, rows, row_spacing):
        for c in range(col_spacing // 2, cols, col_spacing):
            centers.append([r, c] + list(data[r, c]))
            if len(centers) >= num_superpixels:
                return np.array(centers)

    return np.array(centers)


def initialize_cluster_centers(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform grid.
    """
    rows, cols, _ = data.shape
    centers = []
    for r in range(grid_spacing // 2, rows, grid_spacing):
        for c in range(grid_spacing // 2, cols, grid_spacing):
            centers.append([r, c] + list(data[r, c]))
            # if len(centers) >= num_superpixels:  # Stop when enough centers are created
            #     return np.array(centers)
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

# -------------------------------------------------------------------------------

# Define the custom weight function based on both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""
    
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)
    
    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    # print(total_weight)
    
    return {'weight': total_weight}

# Define the merging function to handle both mean color and variance updates
def merge_mean_color_and_variance(graph, src, dst):
    """Merging two regions, updating both mean color and variance."""
    graph.nodes[dst]['total color'] += graph.nodes[src]['total color']
    graph.nodes[dst]['pixel count'] += graph.nodes[src]['pixel count']
    graph.nodes[dst]['mean color'] = (graph.nodes[dst]['total color'] /
                                      graph.nodes[dst]['pixel count'])

    # Merge variance using weighted average based on pixel counts
    total_pixels_dst = graph.nodes[dst]['pixel count']
    total_pixels_src = graph.nodes[src]['pixel count']
    
    graph.nodes[dst]['variance'] = ((total_pixels_dst * graph.nodes[dst]['variance'] +
                                     total_pixels_src * graph.nodes[src]['variance']) /
                                    (total_pixels_dst + total_pixels_src))
    
    # Update mean intensity
    graph.nodes[dst]['mean intensity'] = (graph.nodes[dst]['mean intensity'] * total_pixels_dst +
                                          graph.nodes[src]['mean intensity'] * total_pixels_src) / \
                                          (total_pixels_dst + total_pixels_src)

# Step 4: Iterative Merging Process
def iterative_merge(image, labels, rag, iterations, threshold):
    """Perform iterative merging of regions for a specified number of iterations."""
    init_label = None
    iter = 0

    while 1:
        print(f"Iteration: {iter + 1}")

        # Perform one iteration of merging based on mean color and variance similarity
        labels = graph.merge_hierarchical(
            labels, rag, thresh=threshold, rag_copy=False, in_place_merge=True,
            merge_func=merge_mean_color_and_variance, weight_func=weight_mean_color_and_variance
        )

        # Check if the labels have converged (no change in labels)
        if np.array_equal(labels, init_label):
            break
        else:
            init_label = labels.copy()

        num_regions = len(np.unique(labels))
        print(f"Remaining regions after merging: {num_regions}")

        if num_regions == 1:
            break

        # Rebuild the RAG based on the newly merged labels
        rag = graph.rag_mean_color(image, labels)
        
        # Reinitialize variance for the updated regions
        for region in rag.nodes:
            mask = (labels == region)
            pixels = image[mask]
            variance = np.var(pixels, axis=0)
            rag.nodes[region]['variance'] = variance
            rag.nodes[region]['mean intensity'] = np.mean(color.rgb2gray(pixels))

        # Update edge weights based on the new mean color and variance
        for src, dst in rag.edges():
            rag.edges[src, dst]['weight'] = weight_mean_color_and_variance(rag, src, dst, None)['weight']

        iter += 1

        if iter >= iterations:
            break

    return labels, iter

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../../xray_volume.npy')

# -------------------------------------------------------------------------------

# Clustering Algorithm in Use
k_means = True
region_growing = False
gmm_model = False

# High-dimensional Visualization in Use
t_sne = True
pca = False

# Colormap for the Visualization
random_colormap = False
radviz_colormap = True

# -------------------------------------------------------------------------------

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150]
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

    # Loop though each pixel in the image and assign custom colors
    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            # If all channels are 0, assign black color
            if np.all(resized_image[i][j] == 0):
                input_image[i][j] = [0, 0, 0]
            else:
                input_image[i][j] = getColorfromRatio(resized_image[i][j])

    # -------------------------------------------------------------------------------

    # Apply SLIC segmentation on the RGB values from RadViz
    # segments = segmentation.slic(input_image, n_segments=200, compactness=30, start_label=1)

    # Apply ALR transformation to the 4-channel ratio data
    # alr_image = alr_transform(resized_image)

    # Apply SLIC segmentation on the transformed image (now shape is (256, 256, 3))
    # segments = segmentation.slic(alr_image, n_segments=400, compactness=10, sigma=1)

    segments, cluster_centers = custom_slic(resized_image, 450)

    # print(segments.shape)
    # print(cluster_centers.shape)
    print(len(cluster_centers))
    print(segments)
    print("Segment range:", segments.min(), "to", segments.max())

    # -------------------------------------------------------------------------------

    plt.figure(figsize=(12, 5))

    # Visualize the Original image 
    plt.subplot(1, 2, 1)
    plt.imshow(input_image)  
    plt.title('Original Image')
    plt.axis('off')

    # 3. Visualize the superpixel-boundary marked image
    plt.subplot(1, 2, 2)
    plt.imshow(mark_boundaries(input_image, segments))
    plt.title('Superpixel Boundaries')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    # plt.show()

    # quit()

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and metal values per pixel as the value
    segmentDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentDict:
                segmentDict[segments[i][j]] = []
            segmentDict[segments[i][j]].append(resized_image[i][j])

    # print(segmentDict.keys())

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and pixel coordinates as the value
    segmentCordDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentCordDict:
                segmentCordDict[segments[i][j]] = []
            segmentCordDict[segments[i][j]].append((i, j))

    # print(segmentCordDict.keys())

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

    # print(segmentColorDict.keys())

    # -------------------------------------------------------------------------------

    unique_segments = np.unique(segments)  # Get unique segment IDs
    segment_vectors = []
    
    # Loop through each segment ID and compute mean feature vector
    for segment_id in unique_segments:
        mask = (segments == segment_id)  # Mask for current segment
        mean_color = np.mean(resized_image[mask], axis=0)  # Mean of pixel values in this segment
        segment_vectors.append(mean_color)

    # Convert the list of vectors to a NumPy array
    segment_vectors = np.array(segment_vectors)

    print("Segment vector shape ", segment_vectors.shape)

    # -------------------------------------------------------------------------------

    if t_sne:

        # Perform t-SNE for dimensionality reduction
        tsne = TSNE(n_components=2, random_state=42)
        reduced_data = tsne.fit_transform(segment_vectors)

        # Create dummy labels for visualization (use actual labels if available)
        segment_labels = np.arange(len(reduced_data))

        # Extract colors for each segment in the same order as `segment_ids`
        color_array = np.array([segmentColorDict[seg_id] for seg_id in segment_labels])

        # Create a scatter plot of the t-SNE reduced data
        plt.figure(figsize=(10, 8))

        if random_colormap:
            scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=segment_labels, cmap='viridis', alpha=0.7)
            plt.colorbar(scatter)

        elif radviz_colormap:
            scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=color_array, alpha=0.7)

        plt.title('t-SNE Visualization of Segments')
        plt.xlabel('t-SNE Component 1')
        plt.ylabel('t-SNE Component 2')
        plt.grid(True)
        # plt.show()
        # quit()

    # -------------------------------------------------------------------------------

    if pca:

        # Perform PCA for dimensionality reduction
        pca = PCA(n_components=2, random_state=42)
        reduced_data = pca.fit_transform(segment_vectors)

        # Create dummy labels for visualization (use actual labels if available)
        segment_labels = np.arange(len(reduced_data))

        # Extract colors for each segment in the same order as `segment_ids`
        color_array = np.array([segmentColorDict[seg_id] for seg_id in segment_labels])

        # Create a scatter plot of the PCA reduced data
        plt.figure(figsize=(10, 8))

        if random_colormap:
            scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=segment_labels, cmap='viridis', alpha=0.7)
            plt.colorbar(scatter)

        elif radviz_colormap:
            scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=color_array, alpha=0.7)

        plt.title('PCA Visualization of Segments')
        plt.xlabel('PCA Component 1')
        plt.ylabel('PCA Component 2')
        plt.grid(True)
        # plt.show()
        # quit()

    # -------------------------------------------------------------------------------

    # Perform bivariate analysis of the 4 features of the segment_vectors data using a scatter plot matrix
    # df = pd.DataFrame(segment_vectors, columns=['Feature 1', 'Feature 2', 'Feature 3', 'Feature 4'])
    # fig = px.scatter_matrix(df, title='Scatter Plot Matrix of Segment Features')
    # fig.show()
    # quit()

    # -------------------------------------------------------------------------------

    if random_colormap:

        # Map the color from the T-SNE or PCA plot back to the original image to see which segments correspond to which colors

        # Get the colormap
        cmap = plt.get_cmap('viridis')

        # Normalize the segment labels to the range [0, 1]
        norm = plt.Normalize(vmin=min(segment_labels), vmax=max(segment_labels))

        # Map segment labels to colors
        segment_colors = cmap(norm(segment_labels))

        # Convert the RGBA values to integers in the range [0, 255]
        segment_colors_255 = (segment_colors[:, :3] * 255).astype(np.uint8)

        # print("Shape of colors for first t-sne is ", segment_colors_255.shape)

        # Create an image to store the colors for each pixel
        mapback_image = np.zeros_like(resized_image, dtype=np.uint8)
        # Drop the alpha channel
        mapback_image = mapback_image[:, :, :3]

        for i in range(resized_image.shape[0]):
            for j in range(resized_image.shape[1]):
                mapback_image[i][j] = segment_colors_255[segments[i][j]]

        # Display the original image and the mapped image
        plt.figure(figsize=(12, 5))

        # Visualize the Original image
        plt.subplot(1, 2, 1)
        # plt.imshow(input_image)
        plt.imshow(mark_boundaries(input_image, segments))
        plt.title('Original Image')
        plt.axis('off')

        # Visualize the Mapped image
        plt.subplot(1, 2, 2)
        plt.imshow(mapback_image)
        plt.title('Mapped Image')
        plt.axis('off')

        # Set an overall title for the figure
        plt.suptitle(f'Volume Slice {x}')

        plt.tight_layout()
        # plt.show()
    
    # -------------------------------------------------------------------------------

    if k_means:

        # Implementation of K-means clustering algorithm

        # Create the elbow plot to determine the optimal number of clusters
        distortions = []
        K = range(1, 11)
        for k in K:
            kmeanModel = KMeans(n_clusters=k, random_state=42)
            kmeanModel.fit(segment_vectors)
            distortions.append(kmeanModel.inertia_)

        # Plot the elbow plot
        plt.figure(figsize=(8, 6))

        plt.plot(K, distortions, 'bx-')
        plt.xlabel('k')
        plt.ylabel('Distortion')
        plt.title('Elbow Method for Optimal k')
        # plt.show()

        # -------------------------------------------------------------------------------

        # Perform K-means clustering on the segment vectors to get an initial set of clusters

        # Number of clusters
        num_clusters = 5

        # Perform K-means clustering
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(segment_vectors)

        colormap = plt.get_cmap("tab10")

        # Create a scatter plot of the t-SNE reduced data with cluster labels
        plt.figure(figsize=(10, 8))
        for i in range(num_clusters):  # 5 clusters
            plt.scatter(reduced_data[cluster_labels == i, 0], reduced_data[cluster_labels == i, 1], color=colormap(i), label=f'Cluster {i+1}')

        # Add legend
        plt.legend()

        plt.title('t-sne Visualization of Segments after K-means Clustering')
        plt.xlabel('t-sne Component 1')
        plt.ylabel('t-sne Component 2')
        plt.grid(True)
        # plt.show()

        # -------------------------------------------------------------------------------

        # Extract the color codes for the final clusters to create the final segmented image

        # Get unique cluster IDs from the cluster labels and store the corresponding colors in a dictionary
        cluster_color_dict = dict()
        for cluster_id in np.unique(cluster_labels):
            cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), colormap(cluster_id)[:3]))

        print("Cluster Color Dictionary for K-means clusters: ", cluster_color_dict)
        print("---------------------------------")
        # quit()

    # -------------------------------------------------------------------------------

    if region_growing:

        # Implementation of Region Growing Algorithm

        # Calculate the pairwise distance between all segments based on their centroids and plot a histogram

        # Initialize the distance matrix
        distance_matrix = np.zeros((len(segment_vectors), len(segment_vectors)))

        # Compute pairwise distances between all segments
        for i in range(len(segment_vectors)):
            for j in range(i + 1, len(segment_vectors)):
                distance = np.linalg.norm(segment_vectors[i] - segment_vectors[j])
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance

        # Flatten the distance matrix to get pairwise distances
        pairwise_distances = distance_matrix.flatten()

        # Plot a histogram of pairwise distances
        plt.figure(figsize=(12, 5))
        plt.hist(pairwise_distances, bins=50)
        plt.xlabel('Distance')
        plt.ylabel('Frequency')
        plt.title('Histogram of Pairwise Distances between Segment Centroids')
        # plt.show()

        # threshold = find_optimal_threshold(pairwise_distances)
        # print("Optimal threshold:", threshold)

        # -------------------------------------------------------------------------------

        # Function to determine if two segments should be merged based on distance
        def should_merge(segment_a, segment_b, threshold=0.006):
            # Convert lists of NumPy arrays into single NumPy arrays
            segment_a_array = np.vstack(segment_a)  # Stack all arrays in segment_a into one array
            segment_b_array = np.vstack(segment_b)  # Stack all arrays in segment_b into one array
            centroid_a = segment_a_array.mean(axis=0)  # Compute centroid of segment A
            centroid_b = segment_b_array.mean(axis=0)  # Compute centroid of segment B
            distance = np.linalg.norm(centroid_a - centroid_b)  # Euclidean distance
            return distance < threshold

        # Function to merge multiple segments into one
        def merge_segments(segments, segmentDict):
            new_segment = np.vstack([segmentDict[seg] for seg in segments])  # Combine all points
            return new_segment

        # Initialize tracking structures
        remaining_segments = list(segmentDict.keys())  # Start with all initial segments
        initial_segment_clusters = {seg_id: {seg_id} for seg_id in remaining_segments}  # Track initial clusters

        prevCount = len(remaining_segments)

        print("---------------------------------")
        print("Starting Iterative Merging Process...")

        # Iterative merging process
        while len(remaining_segments) > 5:
            print("Remaining segments: ", len(remaining_segments))

            new_remaining_segments = []   # To store updated list of remaining segments after merging
            already_merged = set()        # Track which segments have been merged in this iteration
            
            for i in range(len(remaining_segments)):
                if remaining_segments[i] in already_merged:
                    continue
                
                seg_i = remaining_segments[i]
                merge_candidates = [seg_i]
                
                for j in range(i + 1, len(remaining_segments)):
                    seg_j = remaining_segments[j]
                    
                    if should_merge(segmentDict[seg_i], segmentDict[seg_j]):
                        merge_candidates.append(seg_j)
                        already_merged.add(seg_j)
                
                if len(merge_candidates) > 1:
                    # Merge all candidates into a new segment
                    new_segment = merge_segments(merge_candidates, segmentDict)
                    new_segment_id = len(segmentDict)   # Assign a new ID to the merged segment
                    segmentDict[new_segment_id] = new_segment
                    
                    # Update cluster tracking
                    initial_cluster_set = set()
                    for seg in merge_candidates:
                        initial_cluster_set.update(initial_segment_clusters[seg])
                    initial_segment_clusters[new_segment_id] = initial_cluster_set
                    
                    new_remaining_segments.append(new_segment_id)
                else:
                    new_remaining_segments.append(seg_i)
            
            remaining_segments = new_remaining_segments

            if prevCount == len(remaining_segments):  # No change in the number of segments
                break
            else:
                prevCount = len(remaining_segments)

        # Final clusters and their corresponding initial segments
        final_clusters = {seg_id: initial_segment_clusters[seg_id] for seg_id in remaining_segments}

        print("Total Clusters:", len(remaining_segments))
        print("Final Segments:", remaining_segments)
        print("---------------------------------")
        print("Initial Segment Clusters:", final_clusters)
        print("---------------------------------")

        # -------------------------------------------------------------------------------

        # Modify the t-sne plot to show the final clusters after merging

        # Create a new scatter plot of the t-SNE reduced data

        # Create a list of cluster IDs for each segment
        cluster_labels = np.zeros(len(segment_labels), dtype=int) - 1  # Initialize with -1
        for cluster_id, segment_ids in final_clusters.items():
            for segment_id in segment_ids:
                cluster_labels[segment_id] = cluster_id

        # Create a scatter plot of the t-SNE reduced data with cluster labels
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=cluster_labels, cmap='viridis', alpha=0.7)

        # Add color bar and legend
        plt.colorbar(scatter)
        plt.title('t-SNE Visualization of Segments (After Region Growing)')
        plt.xlabel('t-SNE Component 1')
        plt.ylabel('t-SNE Component 2')
        plt.grid(True)
        # plt.show()

        # -------------------------------------------------------------------------------

        # Extract the color codes for the final clusters to create the final segmented image

        # Get the colormap
        cmap = plt.get_cmap('viridis')

        # Normalize the segment labels to the range [0, 1]
        norm = plt.Normalize(vmin=min(cluster_labels), vmax=max(cluster_labels))

        # Map segment labels to colors
        cluster_colors = cmap(norm(cluster_labels))

        # Convert the RGBA values to integers in the range [0, 255]
        cluster_colors_255 = (cluster_colors[:, :3] * 255).astype(np.uint8)

        # Get unique cluster IDs from the cluster labels and store the corresponding colors in a dictionary
        cluster_color_dict = dict()
        for cluster_id in np.unique(cluster_labels):
            if cluster_id != -1:
                cluster_color_dict[cluster_id] = cluster_colors_255[cluster_labels == cluster_id][0]

        print("Cluster Color Dictionary for Region Growing Clusters: ", cluster_color_dict)
        print("---------------------------------")

    # -------------------------------------------------------------------------------

    if gmm_model:

        # Implementation of Gaussian Mixture Model (GMM) Clustering Algorithm

        # Perform GMM clustering on the segment vectors to get an initial set of clusters

        # Number of clusters
        num_clusters = 5

        # Perform GMM clustering
        gmm = GaussianMixture(n_components=num_clusters, random_state=42)
        cluster_labels = gmm.fit_predict(segment_vectors)

        colormap = plt.get_cmap("tab10")

        # Create a scatter plot of the t-SNE reduced data with cluster labels
        plt.figure(figsize=(10, 8))
        for i in range(num_clusters):  # 5 clusters
            plt.scatter(reduced_data[cluster_labels == i, 0], reduced_data[cluster_labels == i, 1], color=colormap(i), label=f'Cluster {i+1}')

        # Add legend
        plt.legend()

        plt.title('t-sne Visualization of Segments after GMM Clustering')
        plt.xlabel('t-sne Component 1')
        plt.ylabel('t-sne Component 2')
        plt.grid(True)
        # plt.show()
        # quit()

        # -------------------------------------------------------------------------------

        # Extract the color codes for the final clusters to create the final segmented image

        # Get unique cluster IDs from the cluster labels and store the corresponding colors in a dictionary
        cluster_color_dict = dict()
        for cluster_id in np.unique(cluster_labels):
            cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), colormap(cluster_id)[:3]))

        print("Cluster Color Dictionary for GMM clusters: ", cluster_color_dict)
        print("---------------------------------")

    # -------------------------------------------------------------------------------

    # Create the final segmented image using the cluster colors

    # Create an image to store the colors for each pixel
    final_segmented_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    final_segmented_image = final_segmented_image[:, :, :3]

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            final_segmented_image[i][j] = cluster_color_dict[cluster_labels[segments[i][j]]]

    # Display the original image and the final segmented image
    plt.figure(figsize=(12, 5))

    # Visualize the Original image
    plt.subplot(1, 2, 1)
    plt.imshow(input_image)
    plt.title('Original Image')
    plt.axis('off')

    # Visualize the Final Segmented image
    plt.subplot(1, 2, 2)
    plt.imshow(final_segmented_image)
    plt.title('Final Segmented Image')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    # plt.show()
    # quit()

    # -------------------------------------------------------------------------------

    # Plot final image with superpixel boundaries on top

    plt.figure(figsize=(12, 5))

    # Visualize the Original image 
    plt.subplot(1, 2, 1)
    plt.imshow(final_segmented_image)  
    plt.title('Original Image')
    plt.axis('off')

    # 3. Visualize the superpixel-boundary marked image
    plt.subplot(1, 2, 2)
    plt.imshow(mark_boundaries(final_segmented_image, segments, color=(0, 0, 0)))
    plt.title('Superpixel Boundaries')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    # plt.show()
    # quit()

    # -------------------------------------------------------------------------------

    # Create a graph-based representation of the image using the mean color and variance of each segment

    # Create a Region Adjacency Graph (RAG) based on the segments
    rag = graph.rag_mean_color(final_segmented_image, segments)

    # Add mean color and variance attributes to the graph nodes
    for region in rag.nodes:
        mask = (segments == region)
        pixels = final_segmented_image[mask]

        mean_color = np.mean(pixels, axis=0)
        variance = np.var(pixels, axis=0)
        rag.nodes[region]['mean color'] = mean_color
        rag.nodes[region]['variance'] = variance
        rag.nodes[region]['total color'] = np.sum(pixels, axis=0)
        rag.nodes[region]['pixel count'] = len(pixels)
        rag.nodes[region]['mean intensity'] = np.mean(color.rgb2gray(pixels))

    # Update edge weights based on the mean color and variance of the regions
    for src, dst in rag.edges():
        rag.edges[src, dst]['weight'] = weight_mean_color_and_variance(rag, src, dst, None)['weight']

    # -------------------------------------------------------------------------------

    # Threshold selection based on edge weights

    edge_weights = np.array([rag[u][v]['weight'] for u, v in rag.edges])
    print(f"Min weight: {min(edge_weights)}, Max weight: {max(edge_weights)}")

    plt.figure(figsize=(12, 5))
    plt.hist(edge_weights, bins=50)
    plt.xlabel("Edge Weight (Dissimilarity)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Edge Weights")
    # plt.show()
    # quit()

    # threshold = np.percentile(edge_weights, 70)  # Example: using the 75th percentile
    # print(f"Chosen Threshold: {threshold}")

    # Extract sorted unique weights
    # sorted_weights = np.sort(np.unique(edge_weights))

    # # Compute the difference between consecutive weights
    # weight_diffs = np.diff(sorted_weights)

    # # Find the index of the largest gap
    # max_gap_index = np.argmax(weight_diffs)

    # Optimal threshold = value before the largest gap
    # optimal_threshold = sorted_weights[max_gap_index]
    # print(f"Optimal threshold based on largest gap: {optimal_threshold}")

    # from skimage.filters import threshold_otsu

    # # Compute Otsu's threshold
    # threshold_otsu_val = threshold_otsu(np.array(edge_weights))
    # print(f"Optimal threshold from Otsu's method: {threshold_otsu_val}")

    # -------------------------------------------------------------------------------

    # Perform iterative merging of regions based on mean color and variance similarity for 1 iteration

    final_labels, num_iterations = iterative_merge(final_segmented_image, segments, rag, iterations=1, threshold=30)

    # -------------------------------------------------------------------------------

    # Plot the final segmented image with superpixel boundaries

    plt.figure(figsize=(12, 5))

    # Visualize the Original image
    plt.subplot(1, 3, 1)
    plt.imshow(final_segmented_image)
    plt.title('Original Image')
    plt.axis('off')

    # Visualize the superpixel-boundary marked image
    plt.subplot(1, 3, 2)
    plt.imshow(mark_boundaries(final_segmented_image, segments, color=(0, 0, 0)))
    plt.title('SLIC Superpixel')
    plt.axis('off')

    # Visualize the Final Segmented image with superpixel boundaries
    plt.subplot(1, 3, 3)
    plt.imshow(mark_boundaries(final_segmented_image, final_labels, color=(0, 0, 0)))
    plt.title('Hierarchical Clustering for 1 Iteration')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    plt.show()
    quit()

    # -----------------------------------------------------------------------------------------------------------------------------------------------

    # Visualize the final segmented image with superpixel boundaries for 2nd round
    plt.close('all')  # Closes all open figures

    print("-------------------------------------------------------------------------------------------------")
    print("Segment range:", final_labels.min(), "to", final_labels.max())

    plt.figure(figsize=(12, 5))

    # Visualize the Original image 
    plt.subplot(1, 2, 1)
    plt.imshow(final_segmented_image)  
    plt.title('Original Image')
    plt.axis('off')

    # Visualize the superpixel-boundary marked image
    plt.subplot(1, 2, 2)
    plt.imshow(mark_boundaries(final_segmented_image, final_labels, color=(0, 0, 0)))
    plt.title('Superpixel Boundaries')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    # plt.show()

    # -------------------------------------------------------------------------------

    unique_segments = np.unique(final_labels)  # Get unique segment IDs
    segment_vectors = []
    
    # Loop through each segment ID and compute mean feature vector
    for segment_id in unique_segments:
        mask = (final_labels == segment_id)  # Mask for current segment
        mean_color = np.mean(final_segmented_image[mask], axis=0)  # Mean of pixel values in this segment
        segment_vectors.append(mean_color)

    # Convert the list of vectors to a NumPy array
    segment_vectors = np.array(segment_vectors)

    print("Segment vector shape ", segment_vectors.shape)

    # -------------------------------------------------------------------------------

    # Perform t-SNE for dimensionality reduction
    tsne = TSNE(n_components=2)
    reduced_data = tsne.fit_transform(segment_vectors)

    # Create dummy labels for visualization (use actual labels if available)
    segment_labels = np.arange(len(reduced_data))

    # Create a scatter plot of the t-SNE reduced data
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=segment_labels, cmap='viridis', alpha=0.7)

    # Add color bar and legend
    plt.colorbar(scatter)
    plt.title('t-SNE Visualization of Segments 2nd Round')
    plt.xlabel('t-SNE Component 1')
    plt.ylabel('t-SNE Component 2')
    plt.grid(True)
    # plt.show()
    
    # -------------------------------------------------------------------------------

    # Map the color from the T-SNE plot back to the original image to see which segments correspond to which colors

    # Get the colormap
    cmap = plt.get_cmap('viridis')

    # Normalize the segment labels to the range [0, 1]
    norm = plt.Normalize(vmin=min(segment_labels), vmax=max(segment_labels))

    # Map segment labels to colors
    segment_colors = cmap(norm(segment_labels))

    # Convert the RGBA values to integers in the range [0, 255]
    segment_colors_255 = (segment_colors[:, :3] * 255).astype(np.uint8)

    # print("Shape of colors for first t-sne is ", segment_colors_255.shape)

    # Create an image to store the colors for each pixel
    mapback_image = np.zeros_like(final_segmented_image, dtype=np.uint8)
    # Drop the alpha channel
    mapback_image = mapback_image[:, :, :3]

    for i in range(final_segmented_image.shape[0]):
        for j in range(final_segmented_image.shape[1]):
            mapback_image[i][j] = segment_colors_255[final_labels[i][j]]

    # Display the original image and the mapped image
    plt.figure(figsize=(12, 5))

    # Visualize the Original image
    plt.subplot(1, 2, 1)
    plt.imshow(mark_boundaries(final_segmented_image, final_labels, color=(0, 0, 0)))
    plt.title('Original Image')
    plt.axis('off')

    # Visualize the Mapped image
    plt.subplot(1, 2, 2)
    plt.imshow(mapback_image)
    plt.title('Mapped Image')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    plt.show()