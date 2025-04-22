import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn import metrics
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte
import warnings
import math
import matplotlib.colors as mcolors
import cv2
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, ctx, ClientsideFunction
from scipy.spatial.distance import cdist
from scipy.signal import find_peaks
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import time
import json
from numba import njit
import torch
import torch.nn as nn
import torch.optim as optim
import pickle
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from scipy.spatial import cKDTree
import urllib.parse
import os
import h5py
from scipy import ndimage
import numba

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------------

@numba.njit(cache=True, nogil=True)
def _remove_padding_uniform(data: np.ndarray) -> np.ndarray:
    num_channels = data.shape[-1]
    zero_data = np.isclose(data, 0).sum(axis=3) == num_channels

    # This is the number to crop
    n = 0
    indices = np.array([n, -n - 1])
    while (
        zero_data[indices].all()
        & zero_data[:, indices].all()
        & zero_data[:, :, indices].all()
    ):
        n += 1
        indices = np.array([n, -n - 1])

    if n != 0:
        data = data[n : -n - 1, n : -n - 1, n : -n - 1]

    return data

@numba.njit(cache=True, nogil=True)
def _normalize_data(data: np.ndarray, new_min: float = 0, new_max: float = 1):
    max_val = data.max()
    min_val = data.min()

    return (new_max - new_min) * (data.astype(np.float64) - min_val) / (
        max_val - min_val
    ) + new_min

# -------------------------------------------------------------------------------

# Set seed for reproducibility
torch.manual_seed(0)

# Access the data folder and load the names of the volume datasets
directory = "../../data"
volume_names = []
try:
    for filename in os.listdir(directory):
        # Check if the filename starts with "results"
        if filename.startswith('volume_labels'):
            # Load volume data
            volume_name = filename.split('.')[0].split('volume_labels_')[1]
            volume_names.append(volume_name)
    # Create options for the dropdown
    volume_options = [{'label': name, 'value': name} for name in volume_names]
    # Set the default value to the first volume name        
    default_value = volume_options[0]['value'] if volume_options else None

except FileNotFoundError:
    print(f"Directory {directory} not found. Please check the path.")
    quit()
    
# -------------------------------------------------------------------------------

# Initialize Dash app
# app = dash.Dash(__name__)
app = DashProxy(__name__, transforms=[MultiplexerTransform()])  # Helps to generate the same output from multiple callbacks

# Layout of the app
app.layout = html.Div(
    id="dashboard-server3d",
    children=[
        html.Div(
            children=[
                # Control Panel
                html.Div(
                    children=[
                        html.H2(children='Control Panel'),

                        # Dropdown for selecting volume dataset
                        html.Label('Select Volume Dataset:'),
                        dcc.Dropdown(
                            id='volume-dropdown',
                            options=volume_options,
                            value=default_value
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Slider for selecting superpixel count
                        html.Label('Select number of supervoxels:'),
                        dcc.Slider(
                            id='superpixel-input',
                            min=300,
                            max=700,
                            step=1,
                            value=600,
                            marks={
                                300: {'label': str(300)},
                                700: {'label': str(700)}
                            },
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable filtering supervoxels
                        dcc.Checklist(
                            id='filter-sv-checkbox',
                            options=[
                                {'label': 'Filter Supervoxels', 'value': 'enable'}
                            ],
                            value=[]
                        ),

                        # -------------------------------------------------------------------------------

                        # Slider for selecting slice
                        html.Div(
                            id="slider-container",
                            children=[
                                html.Br(),
                                html.Label('Select supervoxel to visualize:'),
                                html.Br(),
                                dcc.Slider(
                                    id='supervoxel-slider',
                                    min=0,
                                    max=339,
                                    step=1,
                                    value=130,
                                    marks={
                                        0: {'label': str(0)},
                                        339: {'label': str(339)}
                                    },
                                    tooltip={"placement": "bottom"}
                                ),  
                            ],
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
                                {'label': 't-SNE', 'value': 'tsne'},
                                {'label': 'Parallel Coordinates', 'value': 'PC'}
                            ],
                            value='PC'
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
                            value=['enable']
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable Autoencoder feature extraction
                        dcc.Checklist(
                            id='autoencoder-checkbox',
                            options=[
                                {'label': 'Enable Autoencoder', 'value': 'enable'}
                            ],
                            value=[]
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable normalization of channels
                        dcc.Checklist(
                            id='normalize-channels-checkbox',
                            options=[
                                {'label': 'Normalize Channels', 'value': 'enable'}
                            ],
                            value=['enable']
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable supervoxel visualization
                        dcc.Checklist(
                            id='use-supervoxel-checkbox',
                            options=[
                                {'label': 'Use Supervoxel', 'value': 'enable'}
                            ],
                            value=['enable']
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Radio Button for viewing Cluster Statistics
                        html.Label('View Cluster Statistics:'),
                        dcc.RadioItems(
                            id='cluster-stats-radio',
                            options=[
                                {'label': 'Elbow Plot', 'value': 'Elbow'},
                                {'label': 'Silhouette Score', 'value': 'Silhouette'},
                                {'label': 'Davies-Bouldin Index', 'value': 'DBI'}
                            ],
                            value='Elbow'
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # Add break
                        html.Br(),

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Add reset button
                        html.Div(
                            children=[
                                html.Button('Reset Dashboard', id='reset-button', n_clicks=0),
                            ],
                            className='reset-button-container'
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
                                # Container for embedded 3D content
                                html.Div(id='content-div'), 
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
                                            id="loading-spinner3",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="vector-plot",
                                                    className="vector-plot-class",
                                                    clear_on_unhover=True
                                                ),  # Graph component wrapped in the loading spinner
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
                                            id="loading-spinner4",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="cluster-vector-plot",
                                                    className="cluster-vector-plot-class",
                                                    clear_on_unhover=True
                                                )  # Graph component wrapped in the loading spinner
                                            ]
                                        ),
                                    ],
                                    id="cluster-vector-space-visualization"
                                ),

                                # -------------------------------------------------------------------------------

                                # Cluster Stats Plot for Clustering
                                html.Div(
                                    children=[
                                        html.H3(id="cluster-stats-label", children='Elbow Plot for Clustering'),
                                        dcc.Loading(
                                            id="loading-spinner5",  # Wrapper to show loading spinner
                                            type="circle",  # Choose the spinner type (circle, dot, default)
                                            children=[
                                                dcc.Graph(
                                                    id="elbow-plot",
                                                    className="elbow-plot-class",
                                                )  # Graph component wrapped in the loading spinner
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

        # Dummy Div to store intermediate data
        html.Div(id='dummy', style={'display': 'none'}),

        # -------------------------------------------------------------------------------

        # Hidden store to hold intermediate data
        dcc.Store(id='volume-data'),
    ]
)

# -------------------------------------------------------------------------------

# Callback to populate the dropdown on page load
@app.callback(
    [Output('volume-data', 'data'), Output('supervoxel-slider', 'max'), Output('supervoxel-slider', 'marks')],
    Input('volume-dropdown', 'value'),
    State('normalize-channels-checkbox', 'value'),
)
def load_volume_data(volume_name, normalize_channels):
    print("---------------------------------------------------")
    print("Loading volume data")

    start_time = time.time()

    # Load the segment data based on the selected volume name
    segments = np.load(f'../../data/volume_labels_{volume_name}.npy')

    # Load the volume data
    volume_path = f'../../data/{volume_name}.h5'

    header = []
    data = []

    with h5py.File(volume_path, 'r') as f:
        for key in f:
            header.append(key)
            data.append(f[key][()])

    data = np.stack(data, axis=3)

    if volume_name == "thigh_sarcoma":
        header[0], header[1] = header[1], header[0]
        data[:, :, :, [0, 1]] = data[:, :, :, [1, 0]]

    print(header)
    print("Data shape on load ", data.shape)

    nan_replacement = 0

    data[np.isnan(data)] = float(nan_replacement)

    data = _remove_padding_uniform(data)

    num_channels = data.shape[-1]

    if normalize_channels:
        # Normalize each channel to be between 0 and 1
        for i in range(data.shape[-1]):
            data[:, :, :, i] = _normalize_data(data[:, :, :, i])
    else:
        data = _normalize_data(data)

    unique_segments = np.unique(segments)
    num_segments = unique_segments.size
    num_channels = data.shape[-1]

    # Preallocate result array
    segment_vectors = np.zeros((num_segments, num_channels), dtype=data.dtype)

    # Compute mean per channel per segment
    for c in range(num_channels):
        segment_vectors[:, c] = ndimage.mean(data[..., c], labels=segments, index=unique_segments)

    print("Segment vector shape ", segment_vectors.shape)

    min_val  = 0
    max_val  = segment_vectors.shape[0]-1

    marks = {
        min_val: {'label': str(min_val)},
        max_val: {'label': str(max_val)}
    }

    segments = segments.tolist()
    data = data.tolist()

    print('Load volume data completed in:', time.time() - start_time)

    return json.dumps({'segments': segments, 'volume': data}), max_val, marks

# -------------------------------------------------------------------------------

# Update the volume-data when normalize-channels-checkbox is changed
# @app.callback(
#     [Output('volume-data', 'data')],
#     [Input('normalize-channels-checkbox', 'value')],
#     [State('volume-data', 'data')],
#     prevent_initial_call=True
# )
# def update_volume_data(normalize_channels, jsonified_volume_data):
#     print("---------------------------------------------------")
#     print("Updating volume data")

#     start_time = time.time()

#     if jsonified_volume_data is None:
#         print("No volume data found")
#         return dash.no_update

#     if 'enable' in normalize_channels:
#         normalize_channels = True
#     else:
#         normalize_channels = False

#     volume_data = json.loads(jsonified_volume_data)

#     # Convert stored lists back to numpy arrays
#     segments = np.array(volume_data['segments'])
#     data = np.array(volume_data['volume'])

#     print("In between")

#     if normalize_channels:
#         # Normalize each channel to be between 0 and 1
#         for i in range(data.shape[-1]):
#             data[:, :, :, i] = _normalize_data(data[:, :, :, i])
#     else:
#         data = _normalize_data(data)

#     unique_segments = np.unique(segments)
#     num_segments = unique_segments.size
#     num_channels = data.shape[-1]

#     # Preallocate result array
#     segment_vectors = np.zeros((num_segments, num_channels), dtype=data.dtype)

#     # Compute mean per channel per segment
#     for c in range(num_channels):
#         segment_vectors[:, c] = ndimage.mean(data[..., c], labels=segments, index=unique_segments)

#     print('Update volume data completed in:', time.time() - start_time)

#     return json.dumps({'segments': segments.tolist(), 'volume': data.tolist()})

# -------------------------------------------------------------------------------

# Visualize 3D volume inside Dash app
@app.callback(
    Output('content-div', 'children'),
    [Input('volume-dropdown', 'value'), Input('supervoxel-slider', 'value'), Input('filter-sv-checkbox', 'value'), Input('normalize-channels-checkbox', 'value')]
)
def embed_page(volume_name, supervoxel, filter_sv, normalize_channels):
    print("----------------------------------------------------")
    print("Generating 3D visualization")

    print("Volume name: ", volume_name)
    print("Supervoxel: ", supervoxel)
    print("Filter supervoxel: ", filter_sv)
    print("Normalize channels: ", normalize_channels)

    print("----------------------------------------------------")

    # url = 'http://localhost:8080/index.html?dataset='+volume_name+'&timestamp={'+str(time.time())+'}'
    url = 'http://localhost:8080/index.html?dataset='+volume_name

    if 'enable' in normalize_channels:
        url = url + '&normalize_channels=True'

    if 'enable' in filter_sv:
        url = url + '&selected_supervoxel='+str(supervoxel)

    # url = 'https://google.com/'

    return html.Iframe(
        src= url,
        style={
            'width': '100%',
            'height': '520px',
            'border': 'none'
        }
    )

# -------------------------------------------------------------------------------

# Callback to show the supervoxel slider based on the filter checkbox
@app.callback(
    Output('slider-container', 'style'),
    Input('filter-sv-checkbox', 'value'),
    prevent_initial_call=True
)
def show_supervoxel_slider(filter_sv):
    print("----------------------------------------------------")
    print("Inside show_supervoxel_slider")

    if filter_sv:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# -------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True, use_reloader=True)
    app.run(dev_tools_hot_reload=False, debug=True)