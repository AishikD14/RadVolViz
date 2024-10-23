import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries

# Define the custom weight function based on both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""

    # Check if any region is below the intensity threshold (black background)
    if graph.nodes[src]['mean intensity'] < intensity_threshold or graph.nodes[dst]['mean intensity'] < intensity_threshold:
        # print("source: ", src, "dest: ", dst)
        # print(f"src intensity: {graph.nodes[src]['mean intensity']}, dst intensity: {graph.nodes[dst]['mean intensity']}")
        return {'weight': 1e6}  # Prevent merging by assigning a very high weight
    
    # print("hi")
    
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)
    
    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    
    return {'weight': total_weight}

    # """Calculate weight between two regions based on both mean color and variance similarity."""
    # src_intensity = graph.nodes[src]['mean intensity']
    # dst_intensity = graph.nodes[dst]['mean intensity']
    
    # # If both regions are below the intensity threshold (i.e., both black), allow merging
    # if src_intensity < intensity_threshold and dst_intensity < intensity_threshold:
    #     # Allow merging with a weight based on variance similarity
    #     var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    #     var_weight = np.linalg.norm(var_diff)
    #     return {'weight': var_weight}
    
    # # If one region is black and the other is not, prevent merging
    # if src_intensity < intensity_threshold or dst_intensity < intensity_threshold:
    #     return {'weight': np.inf}  # Prevent merging by assigning a very high weight
    
    # # For non-black regions, calculate weight based on mean color and variance
    # mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    # mean_color_weight = np.linalg.norm(mean_diff)
    
    # var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    # var_weight = np.linalg.norm(var_diff)
    
    # # Combine mean color and variance differences into the total weight
    # total_weight = mean_color_weight + var_weight
    
    # return {'weight': total_weight}

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
    
    # Update mean intensity
    graph.nodes[dst]['mean intensity'] = (graph.nodes[dst]['mean intensity'] * total_pixels_dst +
                                          graph.nodes[src]['mean intensity'] * total_pixels_src) / \
                                          (total_pixels_dst + total_pixels_src)

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
            rag.nodes[region]['mean intensity'] = np.mean(color.rgb2gray(pixels))

    return labels

# -------------------------------------------------------------------------------

# Step 1: Load the image
image = imread('data1.jpg')

# Initialize variance and filter based on mean intensity
intensity_threshold = 0.15  # Threshold to ignore black regions (adjust as needed)

# Step 2: SLIC superpixels for initial segmentation
labels1 = segmentation.slic(image, compactness=30, n_segments=400, start_label=1)

# -------------------------------------------------------------------------------

# Highlight specific regions for visualization
# highlight_regions = [132]

# # Check if the highlighted regions are present in the SLIC segmentation
# if all(region in np.unique(labels1) for region in highlight_regions):
#     # Create a mask for the highlighted regions
#     mask = np.isin(labels1, highlight_regions)

#     # Highlight the regions in the original image
#     image[mask] = [255, 0, 0]  # Set the color to red (RGB)

#     # Display the highlighted regions
#     plt.imshow(image)
#     plt.axis('off')
#     plt.show()

# -------------------------------------------------------------------------------


# Step 3: Create a Region Adjacency Graph (RAG)
rag = graph.rag_mean_color(image, labels1)

# Initialize variance for each region (superpixel)
for region in rag.nodes:
    # Extract the pixels of the current superpixel
    mask = (labels1 == region)
    pixels = image[mask]

    # Calculate variance for each color channel (R, G, B)
    variance = np.var(pixels, axis=0)

    # Calculate mean intensity (grayscale equivalent or sum of RGB)
    mean_intensity = np.mean(color.rgb2gray(pixels))  # Using grayscale for intensity

    # Store the variance in the RAG
    rag.nodes[region]['variance'] = variance
    rag.nodes[region]['mean intensity'] = mean_intensity

# -------------------------------------------------------------------------------

# Visualize heatmap of mean intensity
# mean_intensity_map = np.zeros_like(labels1, dtype=float)
# for region in rag.nodes:
#     mean_intensity_map[labels1 == region] = rag.nodes[region]['mean intensity']

# plt.imshow(mean_intensity_map, cmap='inferno')
# plt.colorbar(label='Mean Intensity')
# plt.title("Mean Intensity Map")
# plt.axis('off')
# plt.show()

# quit()

# -------------------------------------------------------------------------------

# Specify the number of iterations
num_iterations = 20  # You can change this value as needed

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
