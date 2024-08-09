import numpy as np
from PIL import Image

# Sample volumetric data (replace with your actual data)
# Assuming the volumetric data is in the shape (X, Y, Z, 4) where the last dimension represents the four variables
data = np.load("../xray_volume.npy")

# Normalize data to range [0, 255] for image representation
data_normalized = (data * 255).astype(np.uint8)

# Flatten the 3D volume to 2D by stacking slices (this step may vary based on your specific data and visualization needs)
# Here we stack slices along the Z-axis to form a 2D image
slices = [data_normalized[:, :, i, :] for i in range(data.shape[2])]
image_2d = np.concatenate(slices, axis=0)

# Create the RGBA image
image = Image.fromarray(image_2d, mode='RGBA')

# Save or display the image
image.save('../images/volumetric_data_rgba.png')
# image.show()
