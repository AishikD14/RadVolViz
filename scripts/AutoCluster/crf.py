import cv2
import numpy as np
import matplotlib.pyplot as plt
import pydensecrf.densecrf as dcrf
from pydensecrf.utils import unary_from_labels, create_pairwise_gaussian, create_pairwise_bilateral

# Step 1: Load the image
image = cv2.imread('path_to_image.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Step 2: Generate an initial segmentation (e.g., using a simple method like K-Means or Random Forest)
# For this example, let's assume we have a labeled image (pre-segmentation) available.
# You can replace this with a segmentation result from a classifier or clustering method.
initial_segmentation = cv2.imread('path_to_presegmentation.png', 0)  # Assuming a grayscale image with labels

# Step 3: Convert the segmentation labels to a format suitable for CRF (discrete labels starting from 0)
n_labels = len(np.unique(initial_segmentation))  # Number of unique labels in the pre-segmentation
initial_labels = initial_segmentation.flatten()

# Step 4: Setup the CRF model
height, width, _ = image.shape
dcrf_model = dcrf.DenseCRF2D(width, height, n_labels)  # Define Dense CRF model with width, height, and number of labels

# Step 5: Create Unary Potentials from the initial segmentation
# Unary potentials represent the cost of assigning each pixel to a label
unary = unary_from_labels(initial_labels, n_labels, gt_prob=0.7, zero_unsure=False)
dcrf_model.setUnaryEnergy(unary)

# Step 6: Add Pairwise Potentials (spatial consistency)
# Create pairwise Gaussian potentials (small smoothness)
pairwise_gaussian = create_pairwise_gaussian(sdims=(3, 3), shape=(height, width))
dcrf_model.addPairwiseEnergy(pairwise_gaussian, compat=3)

# Step 7: Add Pairwise Potentials (appearance consistency based on pixel intensities)
pairwise_bilateral = create_pairwise_bilateral(sdims=(50, 50), schan=(20, 20, 20), img=image, chdim=2)
dcrf_model.addPairwiseEnergy(pairwise_bilateral, compat=10)

# Step 8: Inference (perform CRF optimization to refine the segmentation)
# Run inference for a certain number of iterations (can be tuned)
Q = dcrf_model.inference(10)

# Step 9: Get the refined segmentation
refined_labels = np.argmax(Q, axis=0).reshape((height, width))

# Step 10: Display the original image, initial segmentation, and refined segmentation
plt.figure(figsize=(12, 6))

plt.subplot(1, 3, 1)
plt.imshow(image)
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 3, 2)
plt.imshow(initial_segmentation, cmap='nipy_spectral')
plt.title('Initial Segmentation')
plt.axis('off')

plt.subplot(1, 3, 3)
plt.imshow(refined_labels, cmap='nipy_spectral')
plt.title('CRF Refined Segmentation')
plt.axis('off')

plt.tight_layout()
plt.show()
