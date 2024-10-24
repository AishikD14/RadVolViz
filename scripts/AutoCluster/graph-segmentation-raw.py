import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte

# -------------------------------------------------------------------------------

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

# Load volume data
volume = np.load('../volume.npy')

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [130]
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

    # Step 2: Create a Region Adjacency Graph (RAG) based on the superpixels
    rag = graph.rag_mean_color(pca_image_normalized, labels1)

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

    # -------------------------------------------------------------------------------

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
    plt.imshow(segmentation.mark_boundaries(pca_image_normalized, labels2, color=(0.38, 0.21, 0.06)))
    plt.title('Hierarchical Clustering Segmentation')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    plt.show()
