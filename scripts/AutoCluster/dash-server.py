import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage import graph
from skimage.segmentation import mark_boundaries
import warnings
import math
import matplotlib.colors as mcolors
import cv2
from sklearn.manifold import TSNE
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import pandas as pd

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------------

# Function to constrain CX and CY values to the unit circle
def ConstrainInUnit(CX, CY):
    r = math.sqrt(CX**2 + CY**2)
    if r > 1:
        CX /= r
        CY /= r
    return CX, CY

# Convert to color based on CX, CY (using HCL color space approximation)
def GBCtoHCL2(CX, CY):
    # Check if the point lies on the edge (similar to CX * CX + CY * CY > 0.999999)
    if CX * CX + CY * CY > 0.999999:
        return (0, 0, 0)  # Return RGB black as a tuple
    
    # Calculate hue
    h = math.atan2(CY, CX) + math.pi / 2
    if h < 0:
        h += math.pi * 2
    if h > math.pi * 2:
        h -= math.pi * 2

    # Convert radians to degrees
    h = h / math.pi * 180
    
    # Saturation
    s = math.sqrt(CX**2 + CY**2)
    
    # Lightness (fixed at 0.55)
    l = 0.55

    # Convert hue back to [0, 360] for matplotlib
    h = h / 360.0  # Normalize to [0, 1] range for matplotlib
    return mcolors.hsv_to_rgb((h, s, l))

# Function to perform geometric transformation on the supplied data
def GBC(datam, rotate_var):
    m = len(datam)
    n = len(datam[0])
    
    # Initialize the angle array
    angle = np.zeros(n)
    angle[0] = math.pi / 2 + rotate_var
    
    # Initialize the GBCL array with m + n rows and 2 + n columns
    GBCL = [[0 for _ in range(2 + n)] for _ in range(m + n)]
    
    # Populate the GBCL array
    for i in range(m + n):
        for k in range(2, 2 + n):
            if i < m:
                GBCL[i][k] = float(datam[i][k - 2])
    
    # Populate the first 2 dimensions of the first of the last n rows
    GBCL[m][0] = math.cos(angle[0])
    GBCL[m][1] = math.sin(angle[0])
    
    # Populate the first 2 dimensions of the remaining n-1 rows
    for i in range(1, n):
        angle[i] = angle[i - 1] - 2 * math.pi / n
        GBCL[m + i][0] = math.cos(angle[i]) * 0.997
        GBCL[m + i][1] = math.sin(angle[i]) * 0.997
    
    # Adjust the angles if needed
    for i in range(n):
        if angle[i] < 0:
            angle[i] += 2 * math.pi
        if angle[i] > 2 * math.pi:
            angle[i] -= 2 * math.pi
    
    # Sort the angles
    angle.sort()
    
    # Loop through the original data
    for i in range(m):
        tempsum = sum(float(datam[i][j]) for j in range(n))
        
        if tempsum == 0:
            GBCL[i][0] = 0
            GBCL[i][1] = 0
        else:
            for k in range(n):
                GBCL[i][0] += (float(datam[i][k]) / tempsum) * GBCL[m + k][0]
                GBCL[i][1] += (float(datam[i][k]) / tempsum) * GBCL[m + k][1]
            
            tempangle = math.atan2(GBCL[i][1], GBCL[i][0])
            if tempangle < 0:
                tempangle += 2 * math.pi
            
            flag = False
            tempA = 0
            tempB = 0
            
            for j in range(n - 1):
                if (tempangle > angle[j] or tempangle == angle[j]) and (tempangle < angle[j + 1]):
                    tempA = angle[j + 1]
                    tempB = angle[j]
                    flag = True
                    break
            
            if not flag:
                tempA = angle[0] + 2 * math.pi
                tempB = angle[n - 1]
            
            lth = (math.sqrt(GBCL[i][0] ** 2 + GBCL[i][1] ** 2) / 
                   math.cos((tempA - tempB) / 2) * 
                   math.cos(-(tempA + tempB) / 2 + tempangle))
            
            GBCL[i][0] = lth * math.cos(tempangle)
            GBCL[i][1] = lth * math.sin(tempangle)
 
    return GBCL

# Convert to color based on CX, CY (using HCL color space approximation)
def CoordToColor(CX, CY):
    CX, CY = ConstrainInUnit(CX, CY)
    return GBCtoHCL2(CX, CY)

# Function to get color from ratio
def getColorfromRatio(ratio):
    ss = GBC(np.array([ratio]), 0.0)[0][:2]

    color = CoordToColor(ss[0], ss[1])

    return (np.array(color)[:3] * 255).astype(int)

# Function to apply additive log-ratio (ALR) transformation
def alr_transform(image):
    # Avoid division by zero by adding a small constant (epsilon)
    epsilon = 1e-10
    # Use the last channel as the reference channel for ALR
    reference_channel = image[..., -1]
    # Perform ALR transformation on all other channels relative to the reference channel
    alr_image = np.log((image[..., :-1] + epsilon) / (reference_channel[..., np.newaxis] + epsilon))
    return alr_image

# -------------------------------------------------------------------------------

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

    while 1:
        # Perform one iteration of merging based on mean color and variance similarity
        labels = graph.merge_hierarchical(
            labels, rag, thresh=28, rag_copy=False, in_place_merge=True,
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

# Normalize the value of each voxel so that the sum of all channels is 1
volume = volume / 255

# -------------------------------------------------------------------------------

# Initialize variance and filter based on mean intensity
intensity_threshold = 0.15  # Threshold to ignore black regions (adjust as needed)

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [130]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue

    image = volume[slice_allowed[0], :, :]

    # -------------------------------------------------------------------------------
    # Zoom in on the center of the image
    # -------------------------------------------------------------------------------

    # Determine the center of the image
    height, width = image.shape[:2]
    center_x, center_y = width // 2, height // 2

    # Define a zoom factor (increase this value to zoom in more)
    zoom_factor = 1.85

    # Calculate new dimensions for cropping
    crop_width = int(width / zoom_factor)
    crop_height = int(height / zoom_factor)

    # Define crop box around the center
    left = center_x - crop_width // 2
    right = center_x + crop_width // 2
    top = center_y - crop_height // 2
    bottom = center_y + crop_height // 2

    # Ensure that the crop box is within bounds of the original image
    left = max(left, 0)
    right = min(right, width)
    top = max(top, 0)
    bottom = min(bottom, height)

    # Crop the image using numpy slicing
    cropped_image = image[top:bottom, left:right]

    # Resize the cropped image back to the original size
    resized_image = cv2.resize(cropped_image, (width, height), interpolation=cv2.INTER_LINEAR)

    # -------------------------------------------------------------------------------

    # Create an input image to store the colors for each pixel
    input_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    input_image = input_image[:, :, :3]

    # Loop though each pixel in the image and assign custom colors
    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            # If all channels are 0, assign black color
            if np.all(resized_image[i][j] == 0):
                input_image[i][j] = [0, 0, 0]
            else:
                input_image[i][j] = getColorfromRatio(resized_image[i][j])

    # -------------------------------------------------------------------------------

    # Apply SLIC segmentation on the RGB values fro RadViz
    # segments = segmentation.slic(input_image, n_segments=200, compactness=30, start_label=1)

    # Apply ALR transformation to the 4-channel ratio data
    alr_image = alr_transform(resized_image)

    # Apply SLIC segmentation on the transformed image (now shape is (256, 256, 3))
    segments = segmentation.slic(alr_image, n_segments=400, compactness=10, sigma=1)

    # -------------------------------------------------------------------------------

    unique_segments = np.unique(segments)  # Get unique segment IDs
    segment_vectors = []
    
    # Loop through each segment ID and compute mean feature vector
    for segment_id in unique_segments:
        mask = (segments == segment_id)  # Mask for current segment
        mean_color = np.mean(resized_image[mask], axis=0)  # Mean of pixel values in this segment
        segment_vectors.append(mean_color)

    # Convert the list of vectors to a NumPy array
    segment_vectors = np.array(segment_vectors)

    print(segment_vectors.shape)

    # -------------------------------------------------------------------------------

    # Perform t-SNE for dimensionality reduction
    tsne_data = TSNE(n_components=2)
    reduced_data = tsne_data.fit_transform(segment_vectors)

    # Create dummy labels for visualization (use actual labels if available)
    segment_ids = np.arange(len(reduced_data))

    # Step 3: Visualize the results
    # Create a DataFrame for easier plotting
    df_tsne = pd.DataFrame(reduced_data, columns=['t-SNE Dim 1', 't-SNE Dim 2'])
    df_tsne['Cluster ID'] = segment_ids

    # Create a marked boundary image
    boundary_image = mark_boundaries(input_image, segments)

# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='tsne-plot',
            config={'displayModeBar': False},
        )
    ], style={'width': '48%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(
            id='segment-image',
            config={'displayModeBar': False},
        )
    ], style={'width': '48%', 'display': 'inline-block'})
])

# Callback to update plots interactively
@app.callback(
    Output('segment-image', 'figure'),
    Input('tsne-plot', 'hoverData')
)
def highlight_segment(hover_data):
    if hover_data is None:
        # Default: Show the original boundary image without highlighting
        fig = px.imshow(boundary_image)
        fig.update_layout(coloraxis_showscale=False)
        return fig

    # Get the hovered segment ID from t-SNE plot
    hovered_segment_id = hover_data['points'][0]['pointIndex']

    # Highlight the corresponding segment in the image
    highlighted_image = np.copy(boundary_image)
    highlighted_image[segments != hovered_segment_id] *= 0.3  # Dim non-selected segments

    # Create a new figure with highlighted segment
    fig = px.imshow(highlighted_image)
    fig.update_layout(coloraxis_showscale=False)
    return fig

# Callback to create t-SNE plot
@app.callback(
    Output('tsne-plot', 'figure'),
    Input('tsne-plot', 'id')  # Dummy input to trigger initialization
)

def create_tsne_plot(_):
    # Create scatter plot for t-SNE with segment IDs as custom data
    # fig = px.scatter(df_tsne, x='t-SNE Dim 1', y='t-SNE Dim 2', title='Interactive t-SNE Visualization')
    fig = px.scatter(
        df_tsne,
        x='t-SNE Dim 1',
        y='t-SNE Dim 2',
        color='Cluster ID',  # Use the 'Cluster ID' column for coloring
        color_continuous_scale='Viridis',  # Choose a color scale (e.g., 'Viridis', 'Plasma', etc.)
        title='Interactive t-SNE Visualization with Colorbar',
        labels={'Cluster ID': 'Cluster ID'},  # Label for the colorbar
    )
    fig.update_traces(marker=dict(size=10, color=segment_ids, colorscale='Viridis'))
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)