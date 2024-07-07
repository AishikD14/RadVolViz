import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

data = np.load("../label_volume.npy")

data = data[100:130, 100:130, 100:130]

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
