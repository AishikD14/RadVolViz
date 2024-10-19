import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.metrics.pairwise import euclidean_distances

# -------------------------------------------------------------------------------

# Step 3: Define a custom weight function based on mean color similarity
def weight_mean_color(graph, src, dst, n):
    """Callback to handle edge weight between two regions (src, dst) based on color similarity."""
    diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    return {'weight': np.linalg.norm(diff)}

# Step 4: Define the merging function (e.g., merge regions based on color similarity)
def merge_mean_color(graph, src, dst):
    """Callback to handle merging of regions."""
    graph.nodes[dst]['total color'] += graph.nodes[src]['total color']
    graph.nodes[dst]['pixel count'] += graph.nodes[src]['pixel count']
    graph.nodes[dst]['mean color'] = (graph.nodes[dst]['total color'] /
                                      graph.nodes[dst]['pixel count'])

# Updated weight function to include both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""
    # Mean color difference
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    # Variance difference
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)

    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    
    return {'weight': total_weight}

# Update the merge function to store variance during merging
def merge_mean_color_and_variance(graph, src, dst):
    """Merging two regions, updating both mean color and variance."""
    # Merge color statistics
    graph.nodes[dst]['total color'] += graph.nodes[src]['total color']
    graph.nodes[dst]['pixel count'] += graph.nodes[src]['pixel count']
    graph.nodes[dst]['mean color'] = (graph.nodes[dst]['total color'] /
                                      graph.nodes[dst]['pixel count'])

    # Merge variance statistics
    total_pixels_dst = graph.nodes[dst]['pixel count']
    total_pixels_src = graph.nodes[src]['pixel count']
    
    # Weighted update for variance
    graph.nodes[dst]['variance'] = ((total_pixels_dst * graph.nodes[dst]['variance'] +
                                     total_pixels_src * graph.nodes[src]['variance']) /
                                    (total_pixels_dst + total_pixels_src))
    
# -------------------------------------------------------------------------------

# Load the image
image = imread('data3.jpg')

# -------------------------------------------------------------------------------

# Step 1: SLIC superpixels for initial segmentation
labels1 = segmentation.slic(image, compactness=30, n_segments=400, start_label=1)

# Assuming that black has RGB value (0, 0, 0), we create a mask
# mask = np.all(image == [0, 0, 0], axis=-1)

# # Step 2: SLIC superpixels for initial segmentation, with mask support
# labels1 = segmentation.slic(image, compactness=30, n_segments=400, start_label=1, mask=~mask)

# -------------------------------------------------------------------------------

# Step 2: Create a Region Adjacency Graph (RAG) based on the superpixels
rag = graph.rag_mean_color(image, labels1)

# Initialize variance for each node in the RAG
for region in rag.nodes:
    # Extract the pixels of the current superpixel
    mask = (labels1 == region)
    pixels = image[mask]

    # Calculate variance for each color channel (R, G, B)
    variance = np.var(pixels, axis=0)
    
    # Store variance in the RAG
    rag.nodes[region]['variance'] = variance

# -------------------------------------------------------------------------------

# Step 5: Apply hierarchical merging using the mean color similarity
labels2 = graph.merge_hierarchical(labels1, rag, thresh=35, rag_copy=False,
                                   in_place_merge=True,
                                   merge_func=merge_mean_color_and_variance,
                                   weight_func=weight_mean_color_and_variance)

# Step 6: Map the segmented image to RGB color for visualization
out = color.label2rgb(labels2, image, kind='avg', bg_label=0)

# Step 6: Apply hierarchical merging using the mean color similarity, excluding black regions
# Hierarchical clustering will only process regions inside the mask (non-black regions)
# labels2 = graph.merge_hierarchical(labels1, rag, thresh=35, rag_copy=False,
#                                    in_place_merge=True,
#                                    merge_func=merge_mean_color,
#                                    weight_func=weight_mean_color)

# # Step 7: Map the segmented image to RGB color for visualization, excluding black regions
# out = color.label2rgb(labels2, image, kind='avg', bg_label=0)

# -------------------------------------------------------------------------------

# Display the original image, SLIC superpixels, and final segmentation
fig, ax = plt.subplots(1, 3, figsize=(16, 5), sharex=True, sharey=True)

ax[0].imshow(image)
ax[0].set_title("Original Image")
ax[0].axis('off')

ax[1].imshow(mark_boundaries(image, labels1))
ax[1].set_title("SLIC Superpixels")
ax[1].axis('off')

ax[2].imshow(mark_boundaries(out, labels2))
ax[2].set_title("Hierarchical Clustering Segmentation")
ax[2].axis('off')

plt.tight_layout()
plt.show()
