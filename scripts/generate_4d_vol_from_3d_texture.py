import numpy as np
import matplotlib.pyplot as plt

# Define the parameters of your raw data
width = 256  # Width of the data
height = 256  # Height of the data
depth = 256  # Depth of the data
channel = 4  # Number of channels in the data
dtype = np.uint8  # Data type, change according to your file (e.g., np.float32, np.int16)

# Read the raw file
filename = 'volume_data.raw'
with open(filename, 'rb') as file:
    data = np.fromfile(file, dtype=dtype)

# Reshape the flat data array to 3D (depth, height, width)
volume = data.reshape((depth, height, width, channel))

# Now `volume` is a 3D NumPy array
print(volume.shape)  # This should print (depth, height, width)

# Find number of unique values in the volume
unique_values = np.unique(volume)
# print("Number of unique values:", len(unique_values))

# Find the minimum and maximum values in the volume
min_value = np.min(volume)
max_value = np.max(volume)
# print("Min value:", min_value)
# print("Max value:", max_value)

# Find index of first occurrence of a specific value
value_to_find = 128
index = np.unravel_index(np.argmax(volume == value_to_find), volume.shape)
# print("Index of first occurrence of value 128:", index)

# Save the original volume as a NumPy file
np.save('volume.npy', volume)

# Print value of all channels at a specific location
z, y, x = 100, 100, 101
print("Values at location (100, 100, 100):", volume[z, y, x])

# Optionally: visualize a slice using matplotlib
# plt.imshow(volume[depth // 2], cmap='gray')  # Show the middle slice
# plt.show()

# --------------------------------------------------------------------------------------------

# Normalize values in each voxel of the volume data such that all the values of the individual voxels add up to 1, there can be more than 1 value in each voxel
volume = np.load('volume.npy')
print("Original Volume Shape:", volume.shape)

# Normalize the volume
volume_sum = np.sum(volume, axis=-1, keepdims=True)
volume_normalized = volume / volume_sum

print("Normalized Volume Shape:", volume_normalized.shape)
print("Normalized Volume Min Value:", np.min(volume_normalized))
print("Normalized Volume Max Value:", np.max(volume_normalized))

# Print value of all channels at a specific location
z, y, x = 100, 100, 101
print("Values at location (100, 100, 100):", volume_normalized[z, y, x])

# Save the normalized volume
np.save('normalized_volume.npy', volume_normalized)

# --------------------------------------------------------------------------------------------
