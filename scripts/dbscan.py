import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score
import os

# Load data from CSV file
# Replace 'your_data.csv' with the path to your CSV file
data = pd.read_csv('/home/aideb/RadVolViz/data10.csv')

# Assuming the CSV has a header and the data starts from the first row
# and all columns are numeric features
# If there are non-numeric features, they need to be handled (e.g., encoding)
# and if there are irrelevant columns, they should be dropped

# Preview the data
print(data.head())

# Standardize the data
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data)

# Step 1: K-Distance Plot
def plot_k_distance(data, k):
    neighbors = NearestNeighbors(n_neighbors=k)
    neighbors_fit = neighbors.fit(data)
    distances, indices = neighbors_fit.kneighbors(data)
    distances = np.sort(distances[:, k-1], axis=0)
    plt.figure(figsize=(10, 6))
    plt.plot(distances)
    plt.title(f'K-Distance Plot for k={k}')
    plt.xlabel('Points sorted by distance')
    plt.ylabel(f'{k}-th Nearest Neighbor Distance')
    # plt.show()
    # Check if images directory exists
    if not os.path.exists('../images'):
        os.makedirs('../images')
    plt.savefig('../images/k-distance.png')

# Plot for min_samples = 5
# plot_k_distance(data_scaled, 5)

# Step 2: Grid Search for Optimal Parameters
# eps_values = np.linspace(0.1, 2.0, 20)
# min_samples_values = range(3, 10)

# best_eps = None
# best_min_samples = None
# best_score = -1

# for eps in eps_values:
#     for min_samples in min_samples_values:
#         print(f'EPS: {eps}, Min Samples: {min_samples}\n')
#         dbscan = DBSCAN(eps=eps, min_samples=min_samples)
#         labels = dbscan.fit_predict(data_scaled)
        
#         # Silhouette score only makes sense if more than 1 cluster
#         if len(set(labels)) > 1:
#             score = silhouette_score(data_scaled, labels)
#             print(f'Silhouette Score: {score}\n')
#             if score > best_score:
#                 best_eps = eps
#                 best_min_samples = min_samples
#                 best_score = score

# print(f'Best EPS: {best_eps}')
# print(f'Best Min Samples: {best_min_samples}')
# print(f'Best Silhouette Score: {best_score}')

# Apply DBSCAN
# Adjust the parameters `eps` and `min_samples` as needed
dbscan = DBSCAN(eps=0.8, min_samples=8)
# dbscan = DBSCAN(eps=best_eps, min_samples=best_min_samples)
clusters = dbscan.fit_predict(data_scaled)

# Add the cluster labels to the original data
data['Cluster'] = clusters

# Save the resulting data with clusters to a new CSV file
data.to_csv('clustered_data.csv', index=False)

# Print the first few rows of the clustered data
print(data.head())
print(data.shape)

# Optional: Visualize the clusters if the data is 2D or 3D
# For simplicity, we'll assume the data has at least two dimensions

if data.shape[1] >= 2:
    plt.scatter(data.iloc[:, 0], data.iloc[:, 1], c=clusters, cmap='plasma')
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.title('DBSCAN Clustering')
    # plt.show()
    # Check if images directory exists
    if not os.path.exists('../images'):
        os.makedirs('../images')
    plt.savefig('../images/dbscan.png')