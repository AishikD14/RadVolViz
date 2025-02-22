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
import dash
from dash import dcc, html, Input, Output
from scipy.spatial.distance import cdist
from scipy.signal import find_peaks
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import time
import torch
import torch.nn as nn
import torch.optim as optim

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

def compute_superpixel_features(image_4ch, superpixels):
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

def cluster_autoencoded_features(model, features, n_clusters=5):
    features = torch.tensor(features, dtype=torch.float32)
    with torch.no_grad():
        encoded_features, _ = model(features)

    encoded_features = encoded_features.numpy()
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(encoded_features)
    return kmeans.labels_, encoded_features

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../../xray_volume.npy')

# -------------------------------------------------------------------------------

# Loop over each x-axis slice
slice_allowed = [80, 90, 100, 130, 150]
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

    segments, cluster_centers = custom_slic(resized_image, 450)
    # segments = segmentation.slic(input_image, n_segments=450, compactness=30, start_label=0)

    print(segments.shape)
    # print(cluster_centers.shape)
    # print(len(cluster_centers))
    print(segments)
    print("Segment range:", segments.min(), "to", segments.max())

    # -------------------------------------------------------------------------------

    # Compute Features
    superpixel_features = compute_superpixel_features(resized_image, segments)

    print(superpixel_features.shape)

    # -------------------------------------------------------------------------------

    # Set seed for reproducibility
    torch.manual_seed(0)

    class Autoencoder(nn.Module):
        def __init__(self, input_dim, latent_dim=3):
            super(Autoencoder, self).__init__()
            # Encoder
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 16),
                nn.ReLU(),
                nn.Linear(16, latent_dim)  # Compress to latent space
            )
            # Decoder
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 16),
                nn.ReLU(),
                nn.Linear(16, input_dim)
            )

        def forward(self, x):
            encoded = self.encoder(x)
            decoded = self.decoder(encoded)
            return encoded, decoded

    # Model Setup
    def train_autoencoder(features, latent_dim=3, epochs=100, lr=0.001):
        features = torch.tensor(features, dtype=torch.float32)
        model = Autoencoder(features.shape[1], latent_dim)
        optimizer = optim.Adam(model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        for epoch in range(epochs):
            optimizer.zero_grad()
            encoded, decoded = model(features)
            loss = criterion(decoded, features)
            loss.backward()
            optimizer.step()

            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {loss.item()}")

        return model
    
    # -------------------------------------------------------------------------------

    # Step 3: Train Autoencoder
    autoencoder_model = train_autoencoder(superpixel_features)

    # -------------------------------------------------------------------------------

    # Cluster & Visualize
    cluster_labels1, encoded_feats = cluster_autoencoded_features(autoencoder_model, superpixel_features)

    # Visualize t-SNE
    tsne = TSNE(n_components=2, random_state=42)
    reduced_data = tsne.fit_transform(encoded_feats)

    cluster_color_dict = {}

    colormap = plt.cm.get_cmap("tab10")

    plt.figure(figsize=(12, 5))
    
    cluster_colors = {}
    for i in range(5):  # 5 clusters
        color = colormap(i)
        cluster_colors[i] = color
        plt.scatter(reduced_data[cluster_labels1 == i, 0], reduced_data[cluster_labels1 == i, 1], label=f'Cluster {i+1}')

    plt.legend()
    plt.title('t-sne Visualization of Segments after K-means Clustering')
    plt.xlabel('t-sne Component 1')
    plt.ylabel('t-sne Component 2')
    plt.grid(True)
    # plt.show()

    cluster_color_dict = cluster_colors

    for cluster_id in np.unique(cluster_labels1):
        cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), cluster_color_dict[cluster_id][:3]))

    # -------------------------------------------------------------------------------

    # Evaluate the clustering
    distortions = []
    distortions1 = []
    distortions2 = []
    K = range(2, 11)

    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(encoded_feats)
        distortions.append(kmeans.inertia_)

    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42)     
        cluster_labels = kmeans.fit_predict(encoded_feats)   
        silhouette_score = metrics.silhouette_score(encoded_feats, cluster_labels)
        distortions1.append(silhouette_score)
        davies_bouldin_score = metrics.davies_bouldin_score(encoded_feats, cluster_labels)
        distortions2.append(davies_bouldin_score)

    # Plot the elbow plot
    plt.figure(figsize=(8, 6))

    plt.plot(K, distortions, 'bx-')
    plt.xlabel('k')
    plt.ylabel('Distortion')
    plt.title('Cluster Stats Plot')

    # Plot the elbow plot
    plt.figure(figsize=(8, 6))

    plt.plot(K, distortions1, 'ro-')
    plt.xlabel('k')
    plt.ylabel('silhouette_score')
    plt.title('Cluster Stats Plot')

    # Plot the elbow plot
    plt.figure(figsize=(8, 6))

    plt.plot(K, distortions2, 'go-')
    plt.xlabel('k')
    plt.ylabel('davies_bouldin_score')
    plt.title('Cluster Stats Plot')

    # -------------------------------------------------------------------------------

    # Create the final segmented image using the cluster colors

    # Create an image to store the colors for each pixel
    final_segmented_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    final_segmented_image = final_segmented_image[:, :, :3]

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            final_segmented_image[i][j] = cluster_color_dict[cluster_labels1[segments[i][j]]]

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
    plt.show()