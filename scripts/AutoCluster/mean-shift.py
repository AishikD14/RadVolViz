import cv2
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth
import matplotlib.pyplot as plt

# Load the image
image = cv2.imread('data3.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV) to RGB (matplotlib friendly)

# Reshape the image to a 2D array of pixels
pixels = image.reshape(-1, 3)

# Estimate the bandwidth (this is the radius of the search window)
bandwidth = estimate_bandwidth(pixels, quantile=0.1, n_samples=500)

# Apply Mean Shift clustering
meanshift = MeanShift(bandwidth=bandwidth, bin_seeding=True)
meanshift.fit(pixels)

# Get the cluster centers and labels
labels = meanshift.labels_
cluster_centers = meanshift.cluster_centers_

# Replace each pixel with the color of its corresponding cluster center
clustered = cluster_centers[labels]
clustered = np.clip(clustered.astype('uint8'), 0, 255)

# Reshape the clustered pixels back to the original image shape
clustered_image = clustered.reshape(image.shape)

# Display the original and clustered image
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(clustered_image)
plt.title('Mean Shift Clustering')
plt.axis('off')

plt.show()
