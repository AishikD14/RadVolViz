import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import SpectralClustering
from skimage import color

# Step 1: Load the image
image = cv2.imread('data1.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Step 2: Reshape the image to a 2D array of pixels
height, width, channels = image.shape
pixels = image.reshape(-1, 3)  # Reshape to (num_pixels, 3) for RGB

# Step 3: Normalize the pixel values to the range [0, 1]
pixels = pixels / 255.0

# Step 4: Define the Spectral Clustering model
n_clusters = 5  # Adjust based on how many segments you want
spectral_model = SpectralClustering(n_clusters=n_clusters, affinity='nearest_neighbors', assign_labels='kmeans')

# Step 5: Fit the model to the pixels
labels = spectral_model.fit_predict(pixels)

# Step 6: Reshape the labels back to the original image shape
segmented_image = labels.reshape(height, width)

# Step 7: Display the original and segmented images
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(segmented_image, cmap='nipy_spectral')
plt.title(f'Spectral Clustering Segmentation ({n_clusters} clusters)')
plt.axis('off')

plt.tight_layout()
plt.show()
