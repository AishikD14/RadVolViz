import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Load the image
image = cv2.imread('data1.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV) to RGB (matplotlib friendly)

# Reshape the image to a 2D array of pixels
pixels = image.reshape(-1, 3)

# --------------------------------------------------------------
# Preprocessing steps

# Normalize pixel values to the [0, 1] range
pixels_normalized = pixels / 255.0

# Apply Gaussian blur to the image
blurred_image = cv2.GaussianBlur(image, (5, 5), 0)
pixels_blurred = blurred_image.reshape(-1, 3)

# --------------------------------------------------------------

# Apply KMeans to cluster the pixel intensities
k = 7  # Number of clusters
kmeans = KMeans(n_clusters=k)
kmeans.fit(pixels_blurred)

# Replace each pixel value with its corresponding cluster centroid
clustered = kmeans.cluster_centers_[kmeans.labels_]
clustered = np.clip(clustered.astype('uint8'), 0, 255)

# Reshape the clustered pixels back into the original image shape
clustered_image = clustered.reshape(image.shape)

# Display the original and clustered image
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(clustered_image)
plt.title(f'K-Means Clustering with {k} Clusters')
plt.axis('off')

plt.show()
