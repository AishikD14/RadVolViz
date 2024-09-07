from PIL import Image
import numpy as np

def extract_slices(image_path, x_size, y_size, z_slices=256, grid_size=16):
    image = Image.open(image_path)
    slices = []

    for i in range(z_slices):
        # Determine the position in the grid
        row = i // grid_size
        col = i % grid_size

        # Calculate the bounding box of the slice
        left = col * x_size
        upper = row * y_size
        right = left + x_size
        lower = upper + y_size

        # Extract the slice
        slice_img = image.crop((left, upper, right, lower))
        slices.append(slice_img)

    return slices

# Example usage
slices = extract_slices('../img/12CeCoFeGd.png', 256, 256)

# Assuming slices are numpy arrays
volume_data = np.stack([np.array(slice) for slice in slices])

# Save to a .raw file
volume_data.tofile('volume_data.raw')

slices = extract_slices('../img/15GdCeCoFe.png', 256, 256)

volume_data1 = np.stack([np.array(slice) for slice in slices])

# Check if the volumes are same
print(np.array_equal(volume_data, volume_data1))  # Should print False