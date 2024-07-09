# Creating a 3D volume from the multivariate data

# import h5py
# import numpy as np

# file_path = '../Gd_Ce_Fe_Co.h5'  # Update this path to your local file

# with h5py.File(file_path, 'r') as hdf:
#     # Access the datasets
#     ce_data = hdf['Ce'][:]
#     co_data = hdf['Co'][:]
#     fe_data = hdf['Fe'][:]
#     gd_data = hdf['Gd'][:]

# # Create a new array to hold the multivariate data
# combined_data = np.zeros((200, 200, 200, 4), dtype=np.float64)

# # Populate the new array with the values from each dataset
# combined_data[..., 0] = ce_data
# combined_data[..., 1] = co_data
# combined_data[..., 2] = fe_data
# combined_data[..., 3] = gd_data

# # Check the shape of the combined array and a sample point
# print(combined_data.shape)  # Should print (200, 200, 200, 4)
# print(combined_data[0, 0, 0])  # Sample point: should print a 4-element array

# np.save('../xray_volume.npy', combined_data)

# --------------------------------------------------------------------------------------------

# Visualizing the 3D volume

import numpy as np

# Assuming the 3D array is named 'volume'
volume = np.load("../xray_volume.npy")  # Example array

# Find coordinates where at least one element in the 4-element vector is not equal to 0
non_zero_coords = np.argwhere(np.any(volume != 0, axis=-1))

# Print the coordinates
print(non_zero_coords)
print(non_zero_coords.shape)  # Print the shape of the resulting array

# Print the value at any 5 coordinates
for i in range(5):
    print(volume[non_zero_coords[i][0], non_zero_coords[i][1], non_zero_coords[i][2]])

# Find coordinates where all elements in the 4-element vector is not equal to 0
non_zero_coords1 = np.argwhere(np.all(volume != 0, axis=-1))

# Print the coordinates
print(non_zero_coords1)
print(non_zero_coords1.shape)  # Print the shape of the resulting

# Print the value at any 5 coordinates
for i in range(5):
    print(volume[non_zero_coords1[i][0], non_zero_coords1[i][1], non_zero_coords1[i][2]])

# Find coordinates where 2 elements in the 4-element vector is not equal to 0
non_zero_coords2 = np.argwhere(np.sum(volume != 0, axis=-1) == 2)

# Print the coordinates
print(non_zero_coords2)
print(non_zero_coords2.shape)  # Print the shape of the resulting

# Print the value at any 5 coordinates
for i in range(5):
    print(volume[non_zero_coords2[i][0], non_zero_coords2[i][1], non_zero_coords2[i][2]])