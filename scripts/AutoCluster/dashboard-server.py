import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte
import warnings
import math
import matplotlib.colors as mcolors
import cv2
from sklearn.manifold import TSNE
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
from scipy.spatial.distance import cdist
from scipy.signal import find_peaks
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import time
import json

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

# -------------------------------------------------------------------------------

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

# Load volume data
volume = np.load('../../xray_volume.npy')

# -------------------------------------------------------------------------------

# Function to create original slice
def create_original_slice(axis, slice_num):
    # Extract slice from volume
    if axis == "x":
        image = volume[slice_num, :, :]
    elif axis == "y":
        image = volume[:, slice_num, :]
    else:
        image = volume[:, :, slice_num]

    print(image.shape)

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

    # Create a plotly figure
    fig = px.imshow(input_image)

    # Update the layout of the figure
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    # Return the figure
    return fig, resized_image, input_image

# Function to create superpixels
def create_superpixels(resized_image, input_image, num_superpixels):
    
    # segments, cluster_centers = custom_slic(resized_image, num_superpixels)
    segments = segmentation.slic(input_image, n_segments=450, compactness=30, start_label=0)

    # Create a plotly figure
    fig = px.imshow(mark_boundaries(input_image, segments))

    # Update the layout of the figure
    fig.update_layout(
        margin=dict(l=2, r=2, b=2, t=2),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    # Return the figure
    return fig, segments

# Function to create PCA plot
def create_pca_plot(segment_vectors, segmentColorDict):
    # Perform PCA for dimensionality reduction
        pca = PCA(n_components=2, random_state=42)
        reduced_data = pca.fit_transform(segment_vectors)

        # Create dummy labels for visualization (use actual labels if available)
        segment_labels = np.arange(len(reduced_data))

        # Create a DataFrame for easier plotting
        df_tsne = pd.DataFrame(reduced_data, columns=['PCA Dimension 1', 'PCA Dimension 2'])
        df_tsne['Segment ID'] = segment_labels

        # Extract colors for each segment in the same order as `segment_ids`
        color_array = [tuple(segmentColorDict[seg_id].tolist()) for seg_id in segment_labels]

        # Convert to 0-255 range
        color_array = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in color_array]

        # Format as "rgb(R, G, B)"
        color_array = [f'rgb{color}' for color in color_array]

        # Normalized levels
        normalized_levels = np.linspace(0, 1, len(reduced_data))

        # Create color scale of format [[level, color], ...]
        color_scale = [[level, color] for level, color in zip(normalized_levels, color_array)]

        fig = px.scatter(
            df_tsne,
            x='PCA Dimension 1',
            y='PCA Dimension 2',
            title='Interactive PCA Visualization of Segments',
            hover_data=['Segment ID'],
        )

        fig.update_traces(marker=dict(color=segment_labels, colorscale=color_scale))

        return fig

# Function to create t-SNE plot
def create_tsne_plot(segment_vectors, segmentColorDict):
    # Perform t-SNE for dimensionality reduction
    tsne = TSNE(n_components=2, random_state=42)
    reduced_data = tsne.fit_transform(segment_vectors)

    # Create dummy labels for visualization (use actual labels if available)
    segment_labels = np.arange(len(reduced_data))

    # Create a DataFrame for easier plotting
    df_tsne = pd.DataFrame(reduced_data, columns=['t-SNE Dimension 1', 't-SNE Dimension 2'])
    df_tsne['Segment ID'] = segment_labels

    # Extract colors for each segment in the same order as `segment_ids`
    color_array = [tuple(segmentColorDict[seg_id].tolist()) for seg_id in segment_labels]

    # Convert to 0-255 range
    color_array = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b in color_array]

    # Format as "rgb(R, G, B)"
    color_array = [f'rgb{color}' for color in color_array]

    # Normalized levels
    normalized_levels = np.linspace(0, 1, len(reduced_data))

    # Create color scale of format [[level, color], ...]
    color_scale = [[level, color] for level, color in zip(normalized_levels, color_array)]

    fig = px.scatter(
        df_tsne,
        x='t-SNE Dimension 1',
        y='t-SNE Dimension 2',
        title='Interactive t-SNE Visualization of Segments',
        hover_data=['Segment ID'],
    )

    fig.update_traces(marker=dict(color=segment_labels, colorscale=color_scale))

    return fig

# -------------------------------------------------------------------------------

# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    # html.H1(children='Dashboard'),

    html.Div(children=[
        # Control Panel
        html.Div(children=[
            html.H2(children='Control Panel'),

            # Radio Button for selection of axis for slicing
            html.Label('Select axis for slicing volume:'),
            dcc.RadioItems(
                id='axis-radio',
                options=[
                    {'label': 'X Axis', 'value': 'x'},
                    {'label': 'Y Axis', 'value': 'y'},
                    {'label': 'Z Axis', 'value': 'z'}
                ],
                value = 'x'
            ),

            # -------------------------------------------------------------------------------

            # Add break
            html.Br(),

            # -------------------------------------------------------------------------------

            # Slider for selecting slice
            html.Label('Select slice:'),
            dcc.Slider(
                id='slice-slider',
                min=1,
                max=volume.shape[0],
                step=1,
                value=130,
                marks={1: str(1), volume.shape[0]: str(volume.shape[0])}
            ),

            # -------------------------------------------------------------------------------

            # Add break
            html.Br(),

            # -------------------------------------------------------------------------------

            # Checkbox to enable/disable segmentation
            dcc.Checklist(
                id='segmentation-checkbox',
                options=[
                    {'label': 'Superpixel segmentation', 'value': 'enable'}
                ],
                value=['enable']
            ),

            # -------------------------------------------------------------------------------

            # Add break
            html.Br(),

            # -------------------------------------------------------------------------------

            # Radio Button for selection Visualization Technique
            html.Label('Select Visualization Technique:'),
            dcc.RadioItems(
                id='visualization-radio',
                options=[
                    {'label': 'PCA', 'value': 'pca'},
                    {'label': 't-SNE', 'value': 'tsne'}
                ],
                value='tsne'
            ),

            # -------------------------------------------------------------------------------

            # Add break
            html.Br(),
            
            # -------------------------------------------------------------------------------

            # Radio Button for selection Clustering Technique
            html.Label('Select Clustering Technique:'),
            dcc.RadioItems(
                id='clustering-radio',
                options=[
                    {'label': 'KMeans', 'value': 'kmeans'},
                    {'label': 'GMM', 'value': 'gmm'}
                ],
                value='kmeans'
            ),
        
        ], style={'width': '20%', 'display': 'inline-block'}),

        # -------------------------------------------------------------------------------

        # Display Panel
        html.Div(children=[

            # Top Half Display
            html.Div(children=[

                # Original Slice
                html.Div(children=[
                    html.H3(children='Original Slice'),
                    dcc.Graph(
                        id='slice-plot'
                    ),
                ], style={'width': '33%', 'display': 'inline-block', 'text-align': 'center'}),

                # -------------------------------------------------------------------------------

                # Superpixel Segmentation
                html.Div(children=[
                    html.H3(children='Superpixel Segmentation'),
                    dcc.Graph(
                        id='superpixel-plot'
                    ),
                ], style={'width': '33%', 'display': 'inline-block', 'text-align': 'center'}),

                # -------------------------------------------------------------------------------

                # Final Segmented Slice
                html.Div(children=[
                    html.H3(children='Final Segmented Slice'),
                    dcc.Graph(
                        id='final-plot'
                    ),
                ], style={'width': '33%', 'display': 'inline-block', 'text-align': 'center'}),

            ]),

            # -------------------------------------------------------------------------------

            # Bottom Half Display
            html.Div(children=[

                # Elbow Plot for Clustering
                html.Div(children=[
                    html.H3(children='Elbow Plot for Clustering'),
                    dcc.Graph(
                        id='elbow-plot'
                    ),
                ], style={'width': '50%', 'display': 'inline-block', 'text-align': 'center'}),

                # -------------------------------------------------------------------------------

                # Vector Space Visualization
                html.Div(children=[
                    html.H3(children='Vector Space Visualization'),
                    dcc.Graph(
                        id='vector-plot'
                    ),
                ], style={'width': '50%', 'display': 'inline-block', 'text-align': 'center'}),

            ]),

        ], style={'width': '80%'}),

    ], style={'display': 'flex'}),

    # Hidden store to hold intermediate data
    dcc.Store(id='slice-data'),
    dcc.Store(id='superpixel-data'),
    dcc.Store(id='vector-data'),
])

# -------------------------------------------------------------------------------

# Callback for Slice Plot
@app.callback(
    [Output('slice-plot', 'figure'), Output('slice-data', 'data')],
    [Input('axis-radio', 'value'), Input('slice-slider', 'value')]
)
def update_slice_plot(axis, slice_num):
    print("--------------------------------")
    print("Updating slice plot...")
    start_time = time.time()
    
    original_slice_fig, resized_image, input_image = create_original_slice(axis, slice_num)
    
    print('Slice plot ready in:', time.time() - start_time)
    return original_slice_fig, json.dumps({'resized_image': resized_image.tolist(), 'input_image': input_image.tolist()})

# -------------------------------------------------------------------------------

# Callback for Superpixel Plot
@app.callback(
    [Output('superpixel-plot', 'figure'), Output('superpixel-data', 'data')],
    [Input('slice-data', 'data')]
)
def update_superpixel_plot(jsonified_slice_data):
    slice_data = json.loads(jsonified_slice_data)
    
    print("Updating superpixel plot...")
    start_time = time.time()

    # Convert stored lists back to numpy arrays
    resized_image = np.array(slice_data['resized_image'])
    input_image = np.array(slice_data['input_image'], dtype=np.uint8)
    
    superpixel_fig, segments = create_superpixels(resized_image, input_image, 450)
    
    print('Superpixel plot ready in:', time.time() - start_time)
    return superpixel_fig, json.dumps({'segments': segments.tolist()})  # Store segments for future use

# -------------------------------------------------------------------------------

# Callback for Vector Space Visualization Plot
@app.callback(
    [Output('vector-plot', 'figure'), Output('vector-data', 'data')],
    [Input('slice-data', 'data'), Input('superpixel-data', 'data'), Input('visualization-radio', 'value')]
)
def update_vector_plot(jsonified_slice_data, jsonified_superpixel_data, visualization):
    slice_data = json.loads(jsonified_slice_data)
    superpixel_data = json.loads(jsonified_superpixel_data)
    print(visualization)
    
    print("Updating vector plot...")
    start_time = time.time()

    # Convert stored lists back to numpy arrays
    resized_image = np.array(slice_data['resized_image'])
    input_image = np.array(slice_data['input_image'], dtype=np.uint8)
    segments = np.array(superpixel_data['segments'])

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

    vector_space_fig = {}

    if visualization == 'pca':
        vector_space_fig = create_pca_plot(segment_vectors, segmentColorDict)

    elif visualization == 'tsne':
        vector_space_fig = create_tsne_plot(segment_vectors, segmentColorDict)
    
    print('Vector plot ready in:', time.time() - start_time)
    return vector_space_fig, json.dumps({'pca_df': ""})

# -------------------------------------------------------------------------------

# Callback for updating plots
# @app.callback(
#     [
#         Output('slice-plot', 'figure'),
#         Output('superpixel-plot', 'figure'),
#         Output('final-plot', 'figure'),
#         Output('elbow-plot', 'figure'),
#         Output('vector-plot', 'figure')
#     ],
#     [
#         Input('axis-radio', 'value'),
#         Input('slice-slider', 'value'),
#         Input('segmentation-checkbox', 'value'),
#         Input('visualization-radio', 'value'),
#         Input('clustering-radio', 'value')
#     ]
# )
# def update_plots(axis, slice_num, segmentation, visualization, clustering):
#     print("--------------------------------")
#     print('Updating plots...')
#     start_time = time.time()

#     print(axis, slice_num, segmentation, visualization, clustering)

#     original_slice_fig, resized_image, input_image = create_original_slice(axis, slice_num)

#     superpixel_fig, segments = create_superpixels(resized_image, input_image, 450)

#     print('Time taken:', time.time() - start_time)

#     return original_slice_fig, superpixel_fig, {}, {}, {}

# -------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)