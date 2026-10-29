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
from sklearn.discriminant_analysis import StandardScaler
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
import torch.nn.functional as F
import torch.optim as optim
from numba import njit
import pickle
from torch.utils.data import DataLoader, Dataset
from skimage.transform import resize
import torchvision.transforms as transforms

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
    return np.array(centers, dtype=np.float32)


@njit
def calculate_distance(pixel, center, spatial_weight, feature_weight):
    """
    Compute the combined distance between a pixel and a cluster center.
    Uses Numba to accelerate this function.
    """
    spatial_dist = np.sqrt((pixel[0] - center[0])**2 + (pixel[1] - center[1])**2)
    feature_dist = np.sqrt(np.sum((pixel[2:] - center[2:])**2))
    return np.sqrt((spatial_dist / spatial_weight)**2 + (feature_dist / feature_weight)**2)


@njit
def assign_pixels_to_clusters(data, cluster_centers, labels, distances, spatial_weight, feature_weight, grid_spacing):
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
                distance = calculate_distance(pixel, center, spatial_weight, feature_weight)
                if distance < distances[rr, cc]:
                    distances[rr, cc] = distance
                    labels[rr, cc] = idx


@njit
def update_cluster_centers(data, labels, cluster_centers):
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


def custom_slic(data, num_superpixels, spatial_weight=5, max_iter=20):
    """
    Perform optimized SLIC segmentation on 4D input data (metal concentrations per pixel).
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

    return labels, cluster_centers

# -------------------------------------------------------------------------------

# Define CNN Encoder (Feature Extractor)
# class CNNEncoder(nn.Module):
#     def __init__(self, latent_dim=128):
#         super(CNNEncoder, self).__init__()
#         self.encoder = nn.Sequential(
#             nn.Conv2d(4, 32, kernel_size=3, stride=1, padding=1),
#             nn.ReLU(),
#             nn.MaxPool2d(2, 2),  

#             nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
#             nn.ReLU(),
#             nn.MaxPool2d(2, 2),  

#             nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
#             nn.ReLU(),
#             nn.AdaptiveAvgPool2d((1, 1)),  
#         )

#         self.fc = nn.Linear(128, latent_dim)

#     def forward(self, x):
#         x = self.encoder(x)
#         x = torch.flatten(x, start_dim=1)
#         return self.fc(x)

class CNNEncoder(nn.Module):
    def __init__(self, latent_dim=128):
        super(CNNEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(4, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 32, kernel_size=3, stride=2, padding=1),  # Strided Conv Instead of MaxPool
            
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=2, padding=1),  # Strided Conv Instead of MaxPool
            
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1),  # Strided Conv Instead of MaxPool
            
            nn.AdaptiveAvgPool2d((1, 1))  # Adaptive pooling to maintain spatial info
        )

        self.fc = nn.Linear(128, latent_dim)

    def forward(self, x):
        x = self.encoder(x)
        x = torch.flatten(x, start_dim=1)
        return self.fc(x)

# Define Projection Head
class ProjectionHead(nn.Module):
    def __init__(self, latent_dim=128, projection_dim=64):
        super(ProjectionHead, self).__init__()
        self.projection = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, projection_dim)
        )

    def forward(self, x):
        return self.projection(x)

# Define NT-Xent Contrastive Loss
class NTXentLoss(nn.Module):
    def __init__(self, temperature=0.5):
        super(NTXentLoss, self).__init__()
        self.temperature = temperature
        self.cosine_similarity = nn.CosineSimilarity(dim=-1)

    def forward(self, z_i, z_j):
        batch_size = z_i.shape[0]

        # Compute cosine similarity
        sim_ij = self.cosine_similarity(z_i.unsqueeze(1), z_j.unsqueeze(0)) / self.temperature
        sim_ji = self.cosine_similarity(z_j.unsqueeze(1), z_i.unsqueeze(0)) / self.temperature
        similarity_matrix = torch.cat([sim_ij, sim_ji], dim=1)

        # Generate labels
        labels = torch.arange(batch_size).to(device)
        loss = F.cross_entropy(similarity_matrix, labels)
        return loss
    
# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../../xray_volume.npy')

skip_training = False

# -------------------------------------------------------------------------------

# Define the latent dimension
# latent_dim = 32
batch_size = 64
# loss = "MSE"
# loss = "ssim"
epochs = 20 

# Set seed for reproducibility
torch.manual_seed(0)

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

if not skip_training:
    
    # File path for superpixel CNN training data
    training_data_path = 'superpixels_features_cnn.npy'

    # Load training data
    data = np.load(training_data_path) #(num_superpixels, img_size, img_size, num_channels)

    print('Training data shape:', data.shape)

    # Normalize the data (per-channel normalization)
    data = (data - np.mean(data, axis=(1, 2), keepdims=True)) / (np.std(data, axis=(1, 2), keepdims=True) + 1e-8)

    # Convert to PyTorch tensors
    data_tensor = torch.tensor(data, dtype=torch.float32).permute(0, 3, 1, 2)  # (N, C, H, W)
    data_tensor = data_tensor.to(device)

    print('Data tensor shape:', data_tensor.shape)

    # Convert dataset into batches
    dataset = torch.utils.data.TensorDataset(data_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # SimCLR Augmentations for Superpixels
    simclr_transforms = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20),
        transforms.RandomResizedCrop(size=(data.shape[2], data.shape[3]), scale=(0.8, 1.0)),
    ])

    # Initialize Model, Loss, and Optimizer
    encoder = CNNEncoder(latent_dim=128).to(device)
    projector = ProjectionHead(latent_dim=128, projection_dim=64).to(device)
    contrastive_loss = NTXentLoss(temperature=0.5).to(device)
    optimizer = torch.optim.Adam(list(encoder.parameters()) + list(projector.parameters()), lr=0.001)

    encoder.train()
    projector.train()

    for epoch in range(epochs):
        epoch_loss = 0
        for (x,) in dataloader:  # Unpack tuple from TensorDataset
            x = x.to(device)

            # Generate Two Augmented Views
            x_i = torch.stack([simclr_transforms(img) for img in x])
            x_j = torch.stack([simclr_transforms(img) for img in x])

            # Compute Latent Representations
            z_i = projector(encoder(x_i))
            z_j = projector(encoder(x_j))

            # Compute Contrastive Loss
            loss = contrastive_loss(z_i, z_j)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        print(f"Epoch [{epoch+1}/{epochs}], Loss: {epoch_loss/len(dataloader):.4f}")

    print("Training complete!")

    # Save the trained model
    torch.save(encoder.state_dict(), 'autoencoder_simclr.pth')
    print("Model saved successfully!")

else:
    # Load the trained model
    autoencoder = Autoencoder(latent_dim)
    autoencoder.load_state_dict(torch.load('autoencoder_cnn.pth'))
    autoencoder.to(device)
    autoencoder.eval()

    print("Model loaded successfully!")

# -------------------------------------------------------------------------------

# Choose a slice from the volume
x = 130

image = volume[x, :, :]

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

segments, cluster_centers = custom_slic(resized_image, 450)

print("Superpixels Generated Successfully for test data!")

# -------------------------------------------------------------------------------

superpixel_size = 16   # Resize each superpixel to 16x16 pixels

superpixel_features = []

# Extract and resize each superpixel
for label in np.unique(segments):
    mask = (segments == label)
    superpixel = resized_image * mask[..., None]  # Apply mask to extract region
    resized_sp = resize(superpixel, (superpixel_size, superpixel_size, 4), anti_aliasing=True)
    superpixel_features.append(resized_sp)

print("Superpixels extracted for slice", x)

# -------------------------------------------------------------------------------

# Convert superpixel features to a numpy array
superpixel_features = np.array(superpixel_features)

# Normalize the data (per-channel normalization)
superpixel_features = (superpixel_features - np.mean(superpixel_features, axis=(1, 2), keepdims=True)) / (np.std(superpixel_features, axis=(1, 2), keepdims=True) + 1e-8)

# Convert to PyTorch tensor
superpixel_tensor = torch.tensor(superpixel_features, dtype=torch.float32).permute(0, 3, 1, 2)  # (N, C, H, W)
superpixel_tensor = superpixel_tensor.to(device)

# Get latent features for superpixels
with torch.no_grad():
    encoder.eval()
    encoded_features = encoder(superpixel_tensor).cpu().numpy()

print("Latent features extracted for superpixels!")

# -------------------------------------------------------------------------------

# Fit KMeans clustering on the latent features
kmeans = KMeans(n_clusters=5, random_state=42).fit(encoded_features)

# Get cluster labels
cluster_labels = kmeans.labels_

# Visualize t-SNE
tsne = TSNE(n_components=2, random_state=42)
reduced_data = tsne.fit_transform(encoded_features)

cluster_color_dict = {}

colormap = plt.cm.get_cmap("tab10")

plt.figure(figsize=(12, 5))

cluster_colors = {}
for i in range(5):  # 5 clusters
    color = colormap(i)
    cluster_colors[i] = color
    plt.scatter(reduced_data[cluster_labels == i, 0], reduced_data[cluster_labels == i, 1], label=f'Cluster {i+1}')

plt.legend()
plt.title('t-sne Visualization of Segments after K-means Clustering')
plt.xlabel('t-sne Component 1')
plt.ylabel('t-sne Component 2')
plt.grid(True)
# plt.show()

cluster_color_dict = cluster_colors

for cluster_id in np.unique(cluster_labels):
    cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), cluster_color_dict[cluster_id][:3]))

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
plt.show()