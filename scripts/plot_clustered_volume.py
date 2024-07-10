import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

data = np.load("../label_volume.npy")

data = data[100:120, 100:120, 100:120]

# Get the coordinates and values from the 3D array
x, y, z = np.indices(data.shape)
values = data.ravel()

print("Unique Labels:", np.unique(values))
print("Number of Unique Labels:", len(np.unique(values)))

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot the 3D scatter plot
ax.scatter(x, y, z, c=values, cmap='viridis')

# Labels
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.set_zlabel('Z axis')

plt.show()


# # --------------------------------------------------------------------------------------------

# # Visualizing the 2D slice

# data = np.load("../label_slice.npy")

# # Get the coordinates and values from the 2D array
# x, y = np.indices(data.shape)
# values = data.ravel()

# print("Unique Labels:", np.unique(values))
# print("Number of Unique Labels:", len(np.unique(values)))

# # Plot the 2D scatter plot
# plt.scatter(x, y, c=values, cmap='viridis')

# # Labels
# plt.xlabel('X axis')
# plt.ylabel('Y axis')

# # plt.show()

# # Save the 2D slice scatter plot
# plt.savefig("../images/label_slice_175.png")