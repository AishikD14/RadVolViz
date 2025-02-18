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

# Global variables
# selected_clusters = []

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
    segments = segmentation.slic(input_image, n_segments=num_superpixels, compactness=30, start_label=0)

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
    df_pca = pd.DataFrame(reduced_data, columns=['PCA Dimension 1', 'PCA Dimension 2'])
    df_pca['Segment ID'] = segment_labels

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
        df_pca,
        x='PCA Dimension 1',
        y='PCA Dimension 2',
        hover_data=['Segment ID'],
    )

    fig.update_traces(marker=dict(color=segment_labels, colorscale=color_scale))

    fig.update_layout(
        xaxis_title={
            'font': {
                'color': 'white'
            }
        },
        yaxis_title={
            'font': {
                'color': 'white'
            }
        },
        xaxis={
            'tickfont': {
                'color': 'white'
            }
        },
        yaxis={
            'tickfont': {
                'color': 'white'
            }
        }
    )

    return fig, reduced_data

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

    # -------------------------------------------------------------------------------

    # Create Radviz color scale

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

    # -------------------------------------------------------------------------------

    fig = px.scatter(
        df_tsne,
        x='t-SNE Dimension 1',
        y='t-SNE Dimension 2',
        hover_data=['Segment ID']
    )

    fig.update_traces(marker=dict(color=segment_labels, colorscale=color_scale))

    fig.update_layout(
        xaxis_title={
            'font': {
                'color': 'white'
            }
        },
        yaxis_title={
            'font': {
                'color': 'white'
            }
        },
        xaxis={
            'tickfont': {
                'color': 'white'
            }
        },
        yaxis={
            'tickfont': {
                'color': 'white'
            }
        }
    )

    return fig, reduced_data

# Function to create elbow plot for KMeans clustering
def create_elbow_plot(segment_vectors, clustering):
    distortions = []
    K = range(1, 11)

    if clustering == 'gmm':
        for k in K:
            gmm = GaussianMixture(n_components=k, random_state=42)
            gmm.fit(segment_vectors)
            distortions.append(gmm.bic(segment_vectors))

        fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'BIC'})

        fig.update_layout(
            xaxis_title={
                'font': {
                    'color': 'white'
                }
            },
            yaxis_title={
                'font': {
                    'color': 'white'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                }
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                }
            }
        )

        return fig
    
    elif clustering == 'kmeans':
        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(segment_vectors)
            distortions.append(kmeans.inertia_)

        fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Distortion'})

        fig.update_layout(
            xaxis_title={
                'font': {
                    'color': 'white'
                }
            },
            yaxis_title={
                'font': {
                    'color': 'white'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                }
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                }
            }
        )

    return fig

# Function to create clusters
def create_clusters(segment_vectors, clustering):
    num_clusters = 5

    if clustering == 'gmm':
        gmm = GaussianMixture(n_components=num_clusters, random_state=42)
        cluster_labels = gmm.fit_predict(segment_vectors)

    elif clustering == 'kmeans':
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(segment_vectors)

    # Initialize selected clusters for swapping
    selected_clusters = []
    cluster_color_dict = {}

    colormap = plt.cm.get_cmap("tab10")

    cluster_colors = {}
    for i in range(num_clusters):  # 5 clusters
        color = colormap(i)
        cluster_colors[i] = color

    cluster_color_dict = cluster_colors

    for cluster_id in np.unique(cluster_labels):
        cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), cluster_color_dict[cluster_id][:3]))

    print("Cluster Color Dictionary for clusters: ", cluster_color_dict)

    return cluster_labels, cluster_color_dict

# Function to create cluster vector plot
def create_cluster_vector_plot(reduced_data, cluster_labels, cluster_color_dict, visualization):
    # Create a DataFrame for easier plotting
    if visualization == 'pca':
        df = pd.DataFrame(reduced_data, columns=['PCA Dimension 1', 'PCA Dimension 2'])
    elif visualization == 'tsne':
        df = pd.DataFrame(reduced_data, columns=['t-SNE Dimension 1', 't-SNE Dimension 2'])

    df['Cluster ID'] = cluster_labels
    # Convert Cluster ID to a string to ensure it's treated as categorical
    df['Cluster ID'] = df['Cluster ID'].astype(str)

    segment_labels = np.arange(len(reduced_data))
    df['Segment ID'] = segment_labels

    # Extract colors for each segment in the same order as `segment_ids`
    # color_array = [cluster_color_dict[cluster_id] for cluster_id in cluster_labels]

    # # Format as "rgb(R, G, B)"
    # color_array = [f'rgb{color}' for color in color_array]

    # # Normalized levels
    # normalized_levels = np.linspace(0, 1, len(reduced_data))

    # # Create color scale of format [[level, color], ...]
    # color_scale = [[level, color] for level, color in zip(normalized_levels, color_array)]

    if visualization == 'pca':
        fig = px.scatter(
            df,
            x='PCA Dimension 1',
            y='PCA Dimension 2',
            color='Cluster ID',
            category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
            hover_data=['Cluster ID', 'Segment ID'],
            labels={"Cluster ID": "Cluster ID"}
        )

    elif visualization == 'tsne':
        fig = px.scatter(
            df,
            x='t-SNE Dimension 1',
            y='t-SNE Dimension 2',
            color='Cluster ID',
            category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
            hover_data=['Cluster ID', 'Segment ID'],
            labels={"Cluster ID": "Cluster ID"}
        )

    # fig.update_traces(marker=dict(color=cluster_labels, colorscale=color_scale))

    fig.update_layout(
        xaxis_title={
            'font': {
                'color': 'white'
            }
        },
        yaxis_title={
            'font': {
                'color': 'white'
            }
        },
        xaxis={
            'tickfont': {
                'color': 'white'
            }
        },
        yaxis={
            'tickfont': {
                'color': 'white'
            }
        }
    )

    fig.update_layout(clickmode='event+select')

    return fig

# Function to create final segmented slice
def create_final_image(cluster_labels, cluster_color_dict, input_image, resized_image, segments):
    # Create an image to store the colors for each pixel
    final_segmented_image = np.zeros_like(resized_image, dtype=np.uint8)
    # Drop the alpha channel
    final_segmented_image = final_segmented_image[:, :, :3]

    for i in range(resized_image.shape[0]):
        for j in range(resized_image.shape[1]):
            final_segmented_image[i][j] = cluster_color_dict[cluster_labels[segments[i][j]]]

    # Create a plotly figure
    fig = px.imshow(final_segmented_image)

    # Update the layout of the figure
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig

# -------------------------------------------------------------------------------

# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    # html.H1(children='Dashboard'),

    html.Div(
        children=[
            # Control Panel
            html.Div(
                children=[
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

                    # -------------------------------------------------------------------------------

                    # Add break
                    html.Br(),

                    # -------------------------------------------------------------------------------

                    # Checkbox to enable/disable clustering
                    dcc.Checklist(
                        id='clustering-checkbox',
                        options=[
                            {'label': 'Enable Clustering', 'value': 'enable'}
                        ],
                        value=[]
                    ),
                
                ],
                className="control-panel"
            ),

            # -------------------------------------------------------------------------------

            # Display Panel
            html.Div(
                children=[

                    # Top Half Display
                    html.Div(
                        children=[

                            # Original Slice
                            html.Div(
                                children=[
                                    html.H3(children='Original Slice'),
                                    dcc.Loading(
                                        id="loading-spinner",  # Wrapper to show loading spinner
                                        type="circle",  # Choose the spinner type (circle, dot, default)
                                        children=[
                                            dcc.Graph(id="slice-plot")  # Graph component wrapped in the loading spinner
                                        ]
                                    ),
                                ],
                                className="original-slice"
                            ),

                            # -------------------------------------------------------------------------------

                            # Superpixel Segmentation
                            html.Div(
                                children=[
                                    html.H3(children='Superpixel Segmentation'),
                                    dcc.Loading(
                                        id="loading-spinner",  # Wrapper to show loading spinner
                                        type="circle",  # Choose the spinner type (circle, dot, default)
                                        children=[
                                            dcc.Graph(id="superpixel-plot")  # Graph component wrapped in the loading spinner
                                        ]
                                    ),
                                ],
                                className="superpixel-segmentation"
                            ),

                            # -------------------------------------------------------------------------------

                            # Final Segmented Slice
                            html.Div(
                                children=[
                                    html.H3(children='Final Segmented Slice'),
                                    html.Div(
                                        "Enable clustering to view final segmented slice",
                                        id="final-segmented-slice-text"
                                    ),
                                    html.Div(
                                        children=[
                                            dcc.Graph(
                                                id='final-plot'
                                            ),
                                        ],
                                    ),
                                ],
                                className="final-segmented-slice"
                            ),

                        ],
                        className="top-half-display"
                    ),

                    # -------------------------------------------------------------------------------

                    # Bottom Half Display
                    html.Div(
                        children=[

                            # Vector Space Visualization
                            html.Div(
                                children=[
                                    html.H3(children='Vector Space Visualization'),
                                    dcc.Loading(
                                        id="loading-spinner",  # Wrapper to show loading spinner
                                        type="circle",  # Choose the spinner type (circle, dot, default)
                                        children=[
                                            dcc.Graph(id="vector-plot")  # Graph component wrapped in the loading spinner
                                        ]
                                    ),
                                ],
                                id="vector-space-visualization"
                            ),

                            # -------------------------------------------------------------------------------

                            # Vector Space Visualization with Clustering
                            html.Div(
                                children=[
                                    html.H3(children='Clustered Vector Space Visualization'),
                                    dcc.Loading(
                                        id="loading-spinner",  # Wrapper to show loading spinner
                                        type="circle",  # Choose the spinner type (circle, dot, default)
                                        children=[
                                            dcc.Graph(id="cluster-vector-plot")  # Graph component wrapped in the loading spinner
                                        ]
                                    ),
                                ],
                                id="cluster-vector-space-visualization"
                            ),

                            # -------------------------------------------------------------------------------

                            # Elbow Plot for Clustering
                            html.Div(
                                children=[
                                    html.H3(children='Elbow Plot for Clustering'),
                                    dcc.Loading(
                                        id="loading-spinner",  # Wrapper to show loading spinner
                                        type="circle",  # Choose the spinner type (circle, dot, default)
                                        children=[
                                            dcc.Graph(id="elbow-plot")  # Graph component wrapped in the loading spinner
                                        ]
                                    ),
                                ],
                                className="elbow-plot"
                            ),
                        ],
                        className="bottom-half-display"
                    ),

                ],
                className="display-panel"
            ),

        ], 
        style={'display': 'flex'}
    ),

    # -------------------------------------------------------------------------------

    # Hidden store to hold intermediate data
    dcc.Store(id='slice-data'),
    dcc.Store(id='superpixel-data'),
    dcc.Store(id='vector-data'),
    dcc.Store(id='cluster-data')
])

# -------------------------------------------------------------------------------

# Callback for Slice Plot
@app.callback(
    [Output('slice-plot', 'figure'), Output('slice-data', 'data'), Output('clustering-checkbox', 'value')],
    [Input('axis-radio', 'value'), Input('slice-slider', 'value')]
)
def update_slice_plot(axis, slice_num):
    print("--------------------------------")
    print("Updating slice plot...")
    start_time = time.time()
    
    original_slice_fig, resized_image, input_image = create_original_slice(axis, slice_num)
    
    print('Slice plot ready in:', time.time() - start_time)
    return original_slice_fig, json.dumps({'resized_image': resized_image.tolist(), 'input_image': input_image.tolist()}), []

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
        vector_space_fig, reduced_data = create_pca_plot(segment_vectors, segmentColorDict)

    elif visualization == 'tsne':
        vector_space_fig, reduced_data = create_tsne_plot(segment_vectors, segmentColorDict)
    
    print('Vector plot ready in:', time.time() - start_time)
    return vector_space_fig, json.dumps({'segment_vectors': segment_vectors.tolist(), 'reduced_data': reduced_data.tolist()})

# -------------------------------------------------------------------------------

# Callback for Elbow Plot
@app.callback(
    Output('elbow-plot', 'figure'),
    [Input('vector-data', 'data'), Input('clustering-radio', 'value')]
)
def update_elbow_plot(jsonified_vector_data, clustering):
    vector_data = json.loads(jsonified_vector_data)

    print("Updating elbow plot...")
    start_time = time.time()

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])

    # -------------------------------------------------------------------------------

    elbow_fig = create_elbow_plot(segment_vectors, clustering)

    print('Elbow plot ready in:', time.time() - start_time)
    return elbow_fig

# -------------------------------------------------------------------------------

# Callback for enabling/disabling clustering
@app.callback(
    [Output('final-plot', 'style'), Output('final-segmented-slice-text', 'style'), Output('vector-space-visualization', 'style'), Output('cluster-vector-space-visualization', 'style')],
    [Input('clustering-checkbox', 'value')]
)
def enable_clustering(checkbox_value):
    if 'enable' in checkbox_value:
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'inline-block'}
    else:
        return {'display': 'none'}, {'display': 'flex'}, {'display': 'inline-block'}, {'display': 'none'}

# -------------------------------------------------------------------------------

# Callback for performing clustering
@app.callback(
    Output('cluster-data', 'data'),
    [Input('vector-data', 'data'), Input('clustering-radio', 'value')]
)
def perform_clustering(jsonified_vector_data, clustering):
    vector_data = json.loads(jsonified_vector_data)

    print("Performing clustering...")
    start_time = time.time()

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])

    # -------------------------------------------------------------------------------

    cluster_labels, cluster_color_dict = create_clusters(segment_vectors, clustering)

    print('Clustering done in:', time.time() - start_time)

    return json.dumps({'cluster_labels': cluster_labels.tolist(), 'cluster_color_dict': cluster_color_dict})

# -------------------------------------------------------------------------------

# Callback for updating vector plot with clustering
@app.callback(
    Output('cluster-vector-plot', 'figure'),
    [Input('vector-data', 'data'), Input('cluster-data', 'data'), Input('visualization-radio', 'value')]
)
def update_cluster_vector_plot(jsonified_vector_data, jsonified_cluster_data, visualization):

    vector_data = json.loads(jsonified_vector_data)
    cluster_data = json.loads(jsonified_cluster_data)

    print("Updating cluster vector plot...")
    start_time = time.time()

    # Convert stored lists back to numpy arrays
    reduced_data = np.array(vector_data['reduced_data'])
    cluster_labels = np.array(cluster_data['cluster_labels'])
    cluster_color_dict = cluster_data['cluster_color_dict']

    # Convert the keys of the dictionary to integers
    cluster_color_dict = {int(k): v for k, v in cluster_color_dict.items()}

    # convert the values of the dictionary to tuples
    cluster_color_dict = {k: tuple(v) for k, v in cluster_color_dict.items()}

    # update_required = False

    # if clickData:
    #     print("--------------------------------")
    #     print(f"Selected clusters Initial: {selected_clusters}")
    #     clicked_cluster = int(clickData['points'][0]['customdata'][0])
    #     print(f"Clicked cluster: {clicked_cluster}")

    #     if clicked_cluster not in selected_clusters:
    #         selected_clusters.append(clicked_cluster)
        
    #     print(f"Selected clusters Final: {selected_clusters}")
    #     print(len(selected_clusters))

    #     # If two clicks, swap data and reset tracking
    #     # if len(selected_clusters) == 2:
    #     #     cluster_map = {selected_clusters[0]: selected_clusters[1], selected_clusters[1]: selected_clusters[0]}
    #     #     cluster_labels = np.array([cluster_map.get(label, label) for label in cluster_labels])
    #     #     selected_clusters.clear()
    #     #     update_required = True

    # -------------------------------------------------------------------------------

    cluster_vector_plot_fig = create_cluster_vector_plot(reduced_data, cluster_labels, cluster_color_dict, visualization)

    print('Cluster vector plot ready in:', time.time() - start_time)

    return cluster_vector_plot_fig

# -------------------------------------------------------------------------------

# Callback for Final Segmented Slice
@app.callback(
    Output('final-plot', 'figure'),
    [Input('cluster-data', 'data'), Input('slice-data', 'data'), Input('superpixel-data', 'data')]
)
def update_final_plot(jsonified_cluster_data, jsonified_slice_data, jsonified_superpixel_data):
    cluster_data = json.loads(jsonified_cluster_data)
    slice_data = json.loads(jsonified_slice_data)
    superpixel_data = json.loads(jsonified_superpixel_data)

    print("Updating final segmented slice...")
    start_time = time.time()

    # Convert stored lists back to numpy arrays
    cluster_labels = np.array(cluster_data['cluster_labels'])
    cluster_color_dict = cluster_data['cluster_color_dict']
    resized_image = np.array(slice_data['resized_image'])
    input_image = np.array(slice_data['input_image'], dtype=np.uint8)
    segments = np.array(superpixel_data['segments'])

    # Convert the keys of the dictionary to integers
    cluster_color_dict = {int(k): v for k, v in cluster_color_dict.items()}

    # convert the values of the dictionary to tuples
    cluster_color_dict = {k: tuple(v) for k, v in cluster_color_dict.items()}

    # -------------------------------------------------------------------------------

    final_fig = create_final_image(cluster_labels, cluster_color_dict, input_image, resized_image, segments)

    print('Final segmented slice ready in:', time.time() - start_time)

    return final_fig

# -------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)