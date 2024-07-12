import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ListedColormap, BoundaryNorm

# data = np.load("../label_volume.npy")

# data = data[100:120, 100:120, 100:120]

# # Get the coordinates and values from the 3D array
# x, y, z = np.indices(data.shape)
# values = data.ravel()

# print("Unique Labels:", np.unique(values))
# print("Number of Unique Labels:", len(np.unique(values)))

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')

# # Plot the 3D scatter plot
# ax.scatter(x, y, z, c=values, cmap='viridis')

# # Labels
# ax.set_xlabel('X axis')
# ax.set_ylabel('Y axis')
# ax.set_zlabel('Z axis')

# plt.show()


# # --------------------------------------------------------------------------------------------

# Visualizing the 2D slice

nullPresent = False
outlierPresent = False

data = np.load("../label_slice.npy")

# Get the coordinates and values from the 2D array
x, y = np.indices(data.shape)
values = data.ravel()
print(values)

print("Unique Labels:", np.unique(values))
print("Number of Unique Labels:", len(np.unique(values)))

actual_values = np.copy(np.unique(values))

# Remove -2 and -1 from the actual values
if -2 in values:
    nullPresent = True
    actual_values = np.delete(actual_values, np.where(actual_values == -2))
if -1 in values:
    outlierPresent = True
    actual_values = np.delete(actual_values, np.where(actual_values == -1))

print("Actual Values:", actual_values)

# Create a custom color map based on viridis, but with black for the value -2 and gray for the value -1
viridis = plt.get_cmap('viridis', len(actual_values))
newcolors = viridis(np.linspace(0, 1, viridis.N))
black = np.array([0, 0, 0, 1])
gray = np.array([0.5, 0.5, 0.5, 1])

# Determine the number of unique values excluding -2 and -1
unique_values = actual_values
num_unique_values = len(actual_values)

# Create a custom colormap
newcolors = viridis(np.linspace(0, 1, num_unique_values))
if outlierPresent:
    newcolors = np.vstack((gray, newcolors))  # Ensure -1 maps to gray
if nullPresent:
    newcolors = np.vstack((black, newcolors))  # Ensure -2 maps to black
newcmap = ListedColormap(newcolors)

# Create a normalization object that maps the values to the colormap indices
bounds = actual_values.tolist()

bounds.insert(0, 0)
if outlierPresent:
    bounds.insert(0, -1)
if nullPresent:
    bounds.insert(0, -2)

norm = BoundaryNorm(bounds, newcmap.N)

# Plot the 2D scatter plot
# scatter = plt.scatter(x, y, c=values, cmap='viridis')
scatter = plt.scatter(x, y, c=values, cmap=newcmap, norm=norm)

# Add color bar
colorbar = plt.colorbar(scatter)

# Label color bar
colorbar.set_label('Region Label')

# Labels
plt.xlabel('X axis')
plt.ylabel('Y axis')

# plt.show()

# Save the 2D slice scatter plot
plt.savefig("../images/label_slice_199.png")