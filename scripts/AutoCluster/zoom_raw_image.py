import numpy as np
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from skimage.util import img_as_float

# Load volume data
volume = np.load('../volume.npy')

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [90]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue
    image = volume[x, :, :]

    # -------------------------------------------------------------------------------
    
    # Flatten the 4D data into a 2D array for PCA (pixels x channels)
    flat_image = image.reshape(-1, 4)  # assuming image has 4 channels

    # Apply PCA to reduce to 3 channels
    pca = PCA(n_components=3)
    pca_image = pca.fit_transform(flat_image)

    # Reshape back to the original image shape with 3 channels
    pca_image_reshaped = pca_image.reshape(image.shape[0], image.shape[1], 3)

    # Normalize the PCA-reduced image to the range [0, 1] for floats
    pca_image_normalized = img_as_float(pca_image_reshaped)

    img_arr = pca_image_normalized

    # Determine the center of the image
    height, width = img_arr.shape[:2]
    center_x, center_y = width // 2, height // 2

    # Define a zoom factor (increase this value to zoom in more)
    zoom_factor = 1.85

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
    cropped_img_arr = img_arr[top:bottom, left:right]

    # plt.figure(figsize=(12, 5))
    # plt.subplot(1, 2, 1)
    # plt.imshow(pca_image_normalized)

    # plt.subplot(1, 2, 2)
    plt.imshow(cropped_img_arr)
    # plt.show()

    # Save the cropped image
    plt.gca().set_xticks([])  # Remove x-ticks
    plt.gca().set_yticks([])  # Remove y-ticks

    plt.savefig('cropped.jpg', bbox_inches='tight', pad_inches=0)

    # -------------------------------------------------------------------------------