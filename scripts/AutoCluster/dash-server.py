import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage import graph
from skimage.segmentation import mark_boundaries
import warnings
import math
import matplotlib.colors as mcolors
import cv2
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
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

# Zoom in on the center of the image
def cropImage(image, zoom_factor):
    # Calculate new dimensions for cropping
    width, height = image.shape[:2]
    center_x, center_y = width // 2, height // 2

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

    return resized_image

def initialize_cluster_centers(data, num_superpixels, grid_spacing):
    """
    Initialize cluster centers based on a uniform grid.
    """
    rows, cols, _ = data.shape
    centers = []
    for r in range(grid_spacing // 2, rows, grid_spacing):
        for c in range(grid_spacing // 2, cols, grid_spacing):
            centers.append([r, c] + list(data[r, c]))
            # if len(centers) >= num_superpixels:  # Stop when enough centers are created
            #     return np.array(centers)
    return np.array(centers)

def calculate_distance(pixel, center, spatial_weight, feature_weight):
    """
    Compute the combined distance between a pixel and a cluster center.
    """
    spatial_dist = np.linalg.norm(pixel[:2] - center[:2])
    feature_dist = np.linalg.norm(pixel[2:] - center[2:])
    return np.sqrt((spatial_dist / spatial_weight)**2 + (feature_dist / feature_weight)**2)

# Custom SLIC function with cosine distance metric
def custom_slic(data, num_superpixels, spatial_weight=5):
    """
    Perform SLIC segmentation on 4D input data (metal concentrations per pixel).
    """
    rows, cols, num_features = data.shape
    grid_spacing = int(np.sqrt((rows * cols) / num_superpixels))
    feature_weight = np.std(data.reshape(-1, num_features), axis=0).mean()

    # Initialize cluster centers
    cluster_centers = initialize_cluster_centers(data, num_superpixels, grid_spacing)
    labels = -1 * np.ones((rows, cols), dtype=int)
    distances = np.full((rows, cols), np.inf)

    # Iterate until convergence
    for _ in range(20):  # Number of iterations
        for idx, center in enumerate(cluster_centers):
            r, c = int(center[0]), int(center[1])
            for dr in range(-grid_spacing, grid_spacing + 1):
                for dc in range(-grid_spacing, grid_spacing + 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        pixel = [rr, cc] + list(data[rr, cc])
                        distance = calculate_distance(pixel, center, spatial_weight, feature_weight)
                        if distance < distances[rr, cc]:
                            distances[rr, cc] = distance
                            labels[rr, cc] = idx

        # Update cluster centers
        new_centers = np.zeros_like(cluster_centers)
        counts = np.zeros(cluster_centers.shape[0], dtype=int)
        for r in range(rows):
            for c in range(cols):
                label = labels[r, c]
                new_centers[label][:2] += [r, c]
                new_centers[label][2:] += data[r, c]
                counts[label] += 1

        for i in range(len(cluster_centers)):
            if counts[i] > 0:
                new_centers[i] /= counts[i]

        cluster_centers = new_centers

    return labels, cluster_centers

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
volume = np.load('../../xray_volume.npy')

# -------------------------------------------------------------------------------

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [130]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue

    image = volume[x, :, :]

    # -------------------------------------------------------------------------------
    # Zoom in on the center of the image
    # -------------------------------------------------------------------------------

    # Define a zoom factor (increase this value to zoom in more)
    zoom_factor = 1.4

    resized_image = cropImage(image, zoom_factor)

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

    # Apply SLIC segmentation on the RGB values from RadViz
    segments = segmentation.slic(input_image, n_segments=450, compactness=30, start_label=0)
    # print("Performing SLIC segmentation...")
    # segments, cluster_centers = custom_slic(resized_image, 450)
    # print("SLIC segmentation completed.")

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and metal values per pixel as the value
    segmentDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentDict:
                segmentDict[segments[i][j]] = []
            segmentDict[segments[i][j]].append(resized_image[i][j])

    # print(segmentDict.keys())

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and pixel coordinates as the value
    segmentCordDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentCordDict:
                segmentCordDict[segments[i][j]] = []
            segmentCordDict[segments[i][j]].append((i, j))

    # print(segmentCordDict.keys())

    # -------------------------------------------------------------------------------

    # Make segment ID as the key and pixel colors as the value
    segmentColorDict = dict()

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            if segments[i][j] not in segmentColorDict:
                segmentColorDict[segments[i][j]] = []
            segmentColorDict[segments[i][j]].append(input_image[i][j] / 255.0)

    # Replace the segment ID with the mean color of the segment
    for key in segmentColorDict.keys():
        segmentColorDict[key] = np.mean(segmentColorDict[key], axis=0)

    # print(segmentColorDict.keys())

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

    # print("Segment vector shape ", segment_vectors.shape)

    # -------------------------------------------------------------------------------

    # Number of clusters
    num_clusters = 5

    # Perform K-means clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(segment_vectors)

    print(len(cluster_labels))

    # Perform t-SNE for dimensionality reduction
    tsne_data = TSNE(n_components=2, random_state=42)
    reduced_data = tsne_data.fit_transform(segment_vectors)

    # Create dummy labels for visualization (use actual labels if available)
    segment_labels = np.arange(len(reduced_data))

    # Step 3: Visualize the results
    # Create a DataFrame for easier plotting
    df_tsne = pd.DataFrame(reduced_data, columns=['t-SNE Dim 1', 't-SNE Dim 2'])
    df_tsne['Cluster ID'] = cluster_labels
    df_tsne['Cluster ID'] = df_tsne['Cluster ID'].astype(str)
    df_tsne['Segment ID'] = segment_labels

    # Create a marked boundary image
    boundary_image = mark_boundaries(input_image, segments)

    # Get the shape of the image
    height, width = boundary_image.shape[:2]

    # Create a scatter trace for displaying segment IDs on hover
    segment_coords = []
    segment_ids = []
    
    for i in range(height):
        for j in range(width):
            segment_coords.append((i, j))
            segment_ids.append(segments[i, j])
    
    # Create a Plotly scatter plot for segment IDs at each pixel location
    scatter_trace1 = {
        'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
        'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
        'mode': 'markers',
        'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
        'text': [seg_id for seg_id in segment_ids],  # Text for hover
        'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
    }

    # -------------------------------------------------------------------------------
    cluster_color_dict = {}
    colormap = plt.cm.get_cmap("tab10")

    cluster_colors = {}
    for i in range(num_clusters):  # 5 clusters
        color = colormap(i)
        cluster_colors[i] = color

    cluster_color_dict = cluster_colors

    for cluster_id in np.unique(cluster_labels):
        cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), cluster_color_dict[cluster_id][:3]))

    print(cluster_color_dict)

    # Create the final segmented image using the cluster colors

    # Create an image to store the colors for each pixel
    final_segmented_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    final_segmented_image = final_segmented_image[:, :, :3]

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            final_segmented_image[i][j] = cluster_color_dict[cluster_labels[segments[i][j]]]

    final_image = mark_boundaries(final_segmented_image, segments)

    # Get the shape of the image
    height, width = final_image.shape[:2]

    # Create a scatter trace for displaying segment IDs on hover
    segment_coords = []
    segment_ids = []
    
    for i in range(height):
        for j in range(width):
            segment_coords.append((i, j))
            segment_ids.append(segments[i, j])
    
    # Create a Plotly scatter plot for segment IDs at each pixel location
    scatter_trace2 = {
        'x': [coord[1] for coord in segment_coords],  # x-coordinates (columns)
        'y': [coord[0] for coord in segment_coords],  # y-coordinates (rows)
        'mode': 'markers',
        'marker': {'color': 'rgba(0, 0, 0, 0)', 'size': 1},  # Invisible markers
        'text': [seg_id for seg_id in segment_ids],  # Text for hover
        'hovertemplate': '<b>%{text}</b><extra></extra>',  # Custom hover template to show the segment ID
    }


# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='original-image',
            # config={'displayModeBar': False},
        )
    ], style={'width': '25%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(
            id='segment-image',
            # config={'displayModeBar': False},
            clear_on_unhover=True
        )
    ], style={'width': '25%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(
            id='final-image',
            # config={'displayModeBar': False},
        )
    ], style={'width': '25%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(
            id='final-segment-image',
            # config={'displayModeBar': False},
            clear_on_unhover=True
        )
    ], style={'width': '25%', 'display': 'inline-block'}),

    # ---------------------------------------------------------------------------

    html.Div([
        dcc.Graph(
            id='tsne-plot',
            # config={'displayModeBar': False},
            clear_on_unhover=True
        )
    ], style={'width': '100%', 'display': 'block'}),

    dcc.Store(id='test')
])

# -------------------------------------------------------------------------------

# Callback to create original image
@app.callback(
    Output('original-image', 'figure'),
    Input('original-image', 'id')  # Dummy input to trigger initialization
)
def create_original_image(_):
    fig = px.imshow(input_image)
    fig.update_layout(
        margin=dict(l=27, r=27, b=27, t=27),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        coloraxis_showscale=False
    )
    return fig

# -------------------------------------------------------------------------------

# Callback to update plots interactively
@app.callback(
    [Output('segment-image', 'figure'), Output('final-segment-image', 'figure')],
    Input('tsne-plot', 'hoverData')
)
def highlight_segment(hover_data):
    if hover_data is None:
        # Default: Show the original boundary image without highlighting
        fig1 = px.imshow(boundary_image)
        fig1.update_layout(coloraxis_showscale=False)

        # Add the scatter trace to the figure
        fig1.add_traces([scatter_trace1])

        fig1.update_layout(
            margin=dict(l=2, r=2, b=2, t=2),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )

        fig2 = px.imshow(final_image)
        fig2.update_layout(coloraxis_showscale=False)

        # Add the scatter trace to the figure
        fig2.add_traces([scatter_trace2])

        fig2.update_layout(
            margin=dict(l=2, r=2, b=2, t=2),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
    
        return fig1, fig2

    # Get the hovered segment ID from t-SNE plot
    hovered_segment_id = hover_data['points'][0]['customdata'][1]

    # Highlight the corresponding segment in the image
    highlighted_image1 = np.copy(boundary_image)
    highlighted_image1[segments != hovered_segment_id] *= 0.3  # Dim non-selected segments

    # Create a new figure with highlighted segment
    fig1 = px.imshow(highlighted_image1)
    fig1.update_layout(
        margin=dict(l=27, r=27, b=27, t=27),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        coloraxis_showscale=False
    )

    # Highlight the corresponding segment in the image
    highlighted_image2 = np.copy(final_image)
    highlighted_image2[segments != hovered_segment_id] *= 0.3  # Dim non-selected segments

    fig2 = px.imshow(highlighted_image2)
    fig2.update_layout(
        margin=dict(l=27, r=27, b=27, t=27),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        coloraxis_showscale=False
    )

    return fig1, fig2

# -------------------------------------------------------------------------------

# Callback to create t-SNE plot
@app.callback(
    Output('tsne-plot', 'figure'),
    [Input('segment-image', 'hoverData'), Input('final-segment-image', 'hoverData')]
)
def create_tsne_plot(hover_data1, hover_data2):
    # Create a new figure with highlighted segment
    fig = px.scatter(
        df_tsne,
        x='t-SNE Dim 1',
        y='t-SNE Dim 2',
        color='Cluster ID',
        category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
        hover_data=['Cluster ID', 'Segment ID'],
        labels={"Cluster ID": "Cluster ID"}
    )

    if hover_data1 is None and hover_data2 is None:
        return fig
    
    if hover_data1 is not None:
        hover_data = hover_data1
    else:
        hover_data = hover_data2

    print(hover_data)

    # Get the hovered segment ID from the segment image
    hovered_segment_id = int(hover_data['points'][0]['text'])

    # Highlight the corresponding segment in the t-SNE plot
    highlighted_segment = df_tsne[df_tsne['Segment ID'] == hovered_segment_id]

    # Dim non-selected segments
    fig.update_traces(marker=dict(opacity=0.3), selector=dict(mode='markers'))

    # Add a trace for the highlighted segment
    fig.add_trace(
        go.Scatter(
            x=highlighted_segment['t-SNE Dim 1'],
            y=highlighted_segment['t-SNE Dim 2'],
            mode='markers',
            marker=dict(size=15, color='black', opacity=1),
            hoverinfo='skip',  # Hide hover info for the highlighted segment,
            showlegend=False  # Hide legend for the highlighted segment
        )
    )

    return fig

# -------------------------------------------------------------------------------

# Callback to create final segmented image
@app.callback(
    Output('final-image', 'figure'),
    Input('final-image', 'id')  # Dummy input to trigger initialization
)
def create_final_image(_):
    fig = px.imshow(final_segmented_image)
    fig.update_layout(
        margin=dict(l=25, r=25, b=25, t=25),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        coloraxis_showscale=False
    )
    return fig

# -------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)