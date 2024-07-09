import numpy as np

volume = np.load("../xray_volume.npy")

print(volume.shape)  # Should print (200, 200, 200, 4)

# Create a 2D slice from the 3D volume
slice_index = 100
slice_data = volume[slice_index]

print(slice_data.shape)  # Should print (200, 4)