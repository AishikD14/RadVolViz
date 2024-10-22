import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries

# Define the custom weight function based on both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)
    
    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    
    return {'weight': total_weight}

# Define the merging function to handle both mean color and variance updates
def merge_mean_color_and_variance(graph, src, dst):
    """Merging two regions, updating both mean color and variance."""
    graph.nodes[dst]['total color'] += graph.nodes[src]['total color']
    graph.nodes[dst]['pixel count'] += graph.nodes[src]['pixel count']
    graph.nodes[dst]['mean color'] = (graph.nodes[dst]['total color'] /
                                      graph.nodes[dst]['pixel count'])

    # Merge variance using weighted average based on pixel counts
    total_pixels_dst = graph.nodes[dst]['pixel count']
    total_pixels_src = graph.nodes[src]['pixel count']
    
    graph.nodes[dst]['variance'] = ((total_pixels_dst * graph.nodes[dst]['variance'] +
                                     total_pixels_src * graph.nodes[src]['variance']) /
                                    (total_pixels_dst + total_pixels_src))

# Step 4: Iterative Merging Process
def iterative_merge(image, labels, rag, iterations):
    """Perform iterative merging of regions for a specified number of iterations."""
    for i in range(iterations):
        # Perform one iteration of merging based on mean color and variance similarity
        labels = graph.merge_hierarchical(
            labels, rag, thresh=35, rag_copy=False, in_place_merge=True,
            merge_func=merge_mean_color_and_variance, weight_func=weight_mean_color_and_variance
        )

        # Rebuild the RAG based on the newly merged labels
        rag = graph.rag_mean_color(image, labels)
        
        # Reinitialize variance for the updated regions
        for region in rag.nodes:
            mask = (labels == region)
            pixels = image[mask]
            variance = np.var(pixels, axis=0)
            rag.nodes[region]['variance'] = variance

    return labels

# -------------------------------------------------------------------------------

# Step 1: Load the image
image = imread('data1.jpg')

# Step 2: SLIC superpixels for initial segmentation
labels1 = segmentation.slic(image, compactness=30, n_segments=400, start_label=1)

# Step 3: Create a Region Adjacency Graph (RAG)
rag = graph.rag_mean_color(image, labels1)

# Initialize variance for each region (superpixel)
for region in rag.nodes:
    # Extract the pixels of the current superpixel
    mask = (labels1 == region)
    pixels = image[mask]

    # Calculate variance for each color channel (R, G, B)
    variance = np.var(pixels, axis=0)

    # Store the variance in the RAG
    rag.nodes[region]['variance'] = variance

# Specify the number of iterations
num_iterations = 10  # You can change this value as needed

# Step 5: Perform the iterative merging
final_labels = iterative_merge(image, labels1, rag, num_iterations)

# Step 6: Map the final segmented image to RGB color for visualization
out = color.label2rgb(final_labels, image, kind='avg', bg_label=0)

# Display the original image, SLIC superpixels, and final segmentation
fig, ax = plt.subplots(1, 3, figsize=(16, 5), sharex=True, sharey=True)

ax[0].imshow(image)
ax[0].set_title("Original Image")
ax[0].axis('off')

ax[1].imshow(mark_boundaries(image, labels1))
ax[1].set_title("SLIC Superpixels")
ax[1].axis('off')

ax[2].imshow(mark_boundaries(out, final_labels))
ax[2].set_title(f"After {num_iterations} Iterations of Merging")
ax[2].axis('off')

plt.tight_layout()
plt.show()
