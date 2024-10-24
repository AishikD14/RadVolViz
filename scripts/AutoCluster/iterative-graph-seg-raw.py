import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte

# Define the custom weight function based on both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""

    # Check if any region is below the intensity threshold (black background)
    if graph.nodes[src]['mean intensity'] < intensity_threshold or graph.nodes[dst]['mean intensity'] < intensity_threshold:
        # print("source: ", src, "dest: ", dst)
        # print(f"src intensity: {graph.nodes[src]['mean intensity']}, dst intensity: {graph.nodes[dst]['mean intensity']}")
        return {'weight': 1e6}  # Prevent merging by assigning a very high weight
    
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)
    
    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    # print(total_weight)
    
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
    init_label = None
    iter = 0

    # The edges are stored in the RAG, and you can access them using rag.edges.data()
    edge_weights = np.array([rag[u][v]['weight'] for u, v in rag.edges])

    # Step 2: Calculate mean and standard deviation of edge weights
    mean_weight = np.mean(edge_weights)
    std_weight = np.std(edge_weights)

    # Example of setting a threshold based on mean and standard deviation
    threshold = mean_weight + std_weight  # Adjust this formula as needed
    print(f"Dynamic Threshold for Merging: {threshold}")

    # quit()

    while 1:
        # Perform one iteration of merging based on mean color and variance similarity
        labels = graph.merge_hierarchical(
            labels, rag, thresh=20, rag_copy=False, in_place_merge=True,
            merge_func=merge_mean_color_and_variance, weight_func=weight_mean_color_and_variance
        )

        # Check if the labels have converged (no change in labels)
        if np.array_equal(labels, init_label):
            break
        else:
            init_label = labels.copy()

        # Rebuild the RAG based on the newly merged labels
        rag = graph.rag_mean_color(image, labels)
        
        # Reinitialize variance for the updated regions
        for region in rag.nodes:
            mask = (labels == region)
            pixels = image[mask]
            variance = np.var(pixels, axis=0)
            rag.nodes[region]['variance'] = variance
            rag.nodes[region]['mean intensity'] = np.mean(color.rgb2gray(pixels))

        iter += 1

    return labels, iter

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../volume.npy')

# Initialize variance and filter based on mean intensity
intensity_threshold = 0.15  # Threshold to ignore black regions (adjust as needed)

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [90]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue
    image = volume[x, :, :]

    # -------------------------------------------------------------------------------
    
    # Flatten the 4D data into a 2D array for PCA (pixels x channels)
    flat_image = image.reshape(-1, 4)  # assuming image has 4 channels

    # Apply PCA to reduce to 3 channels
    pca = PCA(n_components=3)
    pca_image = pca.fit_transform(flat_image)

    # Reshape back to the original image shape with 3 channels
    pca_image_reshaped = pca_image.reshape(image.shape[0], image.shape[1], 3)

    # Apply SLIC to the PCA-reduced image
    labels1 = segmentation.slic(pca_image_reshaped, compactness=30, n_segments=400, start_label=1)

    # Normalize the PCA-reduced image to the range [0, 1] for floats
    pca_image_normalized = img_as_float(pca_image_reshaped)

    # -------------------------------------------------------------------------------

    # Highlight specific regions for visualization
    # highlight_regions = [132]

    # # Check if the highlighted regions are present in the SLIC segmentation
    # if all(region in np.unique(labels1) for region in highlight_regions):
    #     # Create a mask for the highlighted regions
    #     mask = np.isin(labels1, highlight_regions)

    #     # Highlight the regions in the original image
    #     pca_image_normalized[mask] = [255, 0, 0]  # Set the color to red (RGB)

    #     # Display the highlighted regions
    #     plt.imshow(pca_image_normalized)
    #     plt.axis('off')
    #     plt.show()

    # -------------------------------------------------------------------------------


    # Step 3: Create a Region Adjacency Graph (RAG)
    rag = graph.rag_mean_color(pca_image_normalized, labels1)

    # Initialize variance for each region (superpixel)
    for region in rag.nodes:
        # Extract the pixels of the current superpixel
        mask = (labels1 == region)
        pixels = pca_image_normalized[mask]

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
    # Right now it goes until convergence
    num_iterations = 15  # You can change this value as needed

    # Step 5: Perform the iterative merging
    final_labels, iter = iterative_merge(pca_image_normalized, labels1, rag, num_iterations)

    # 1. Visualize the original 4-channel image (displaying only the first 3 channels for visualization)
    plt.figure(figsize=(16, 5))

    # 2. Visualize the PCA-reduced image (normalized to [0, 1] range)
    plt.subplot(1, 3, 1)
    plt.imshow(pca_image_normalized)  # PCA-reduced and normalized image
    plt.title('PCA Reduced Image (Normalized)')
    plt.axis('off')

    # 3. Visualize the superpixel-boundary marked image
    plt.subplot(1, 3, 2)
    plt.imshow(segmentation.mark_boundaries(pca_image_normalized, labels1, color=(0.38, 0.21, 0.06)))
    plt.title('Superpixel Boundaries on PCA Image')
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(segmentation.mark_boundaries(pca_image_normalized, final_labels, color=(0.38, 0.21, 0.06)))
    plt.title(f"After {iter} Iterations of Merging")
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    plt.show()
