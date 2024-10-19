import cv2
import numpy as np
from skimage import io, color
import matplotlib.pyplot as plt
from skimage.segmentation import mark_boundaries

# Load the image
image = cv2.imread('data3.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

# Step 1: Convert image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

# Step 2: Apply a Gaussian blur to reduce noise and improve thresholding
blur = cv2.GaussianBlur(gray, (5, 5), 0)

# Step 3: Apply Otsu's thresholding for binary segmentation
_, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# Step 4: Noise removal through morphological operations (opening)
kernel = np.ones((3, 3), np.uint8)
opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

# Step 5: Sure background area (dilate the opened image to get a solid background)
sure_bg = cv2.dilate(opening, kernel, iterations=3)

# Step 6: Sure foreground area (using distance transform)
dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
# Adjust threshold to capture sure foreground (you can tweak the multiplier)
_, sure_fg = cv2.threshold(dist_transform, 0.5 * dist_transform.max(), 255, 0)

# Step 7: Unknown region (subtract foreground from background)
sure_fg = np.uint8(sure_fg)
unknown = cv2.subtract(sure_bg, sure_fg)

# Step 8: Marker labeling
_, markers = cv2.connectedComponents(sure_fg)

# Add 1 to all labels so that the background is labeled as 1
markers = markers + 1

# Mark the unknown region as 0
markers[unknown == 255] = 0

# Step 9: Apply the Watershed algorithm
markers = cv2.watershed(image, markers)
print(markers)
print(np.unique(markers))

# Mark the boundaries in the original image (regions marked with -1)
image[markers == -1] = [255, 0, 0]  # Boundary in red

# Display the results
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title('Watershed Segmentation')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(mark_boundaries(cv2.cvtColor(image, cv2.COLOR_RGB2BGR), markers))
plt.title('Markers (Regions)')
plt.axis('off')

plt.tight_layout()
plt.show()
