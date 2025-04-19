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

# Ignore warnings
warnings.filterwarnings("ignore")

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

                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Slider for selecting slice
                        html.Label('Select supervoxel to visualize:'),
                        html.Br(),
                        dcc.Slider(
                            id='supervoxel-slider',
                            # min=1,
                            # max=volume.shape[0],
                            min=0,
                            max=160,
                            step=1,
                            value=130,
                            # marks={1: str(1), volume.shape[0]: str(volume.shape[0])}
                            marks={
                                0: {'label': str(0)},
                                160: {'label': str(160)}
                            },
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Slider for selecting superpixel count
                        html.Label('Select number of superpixels:'),
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

                        # Checkbox to enable/disable zero-value pixels dropping
                        dcc.Checklist(
                            id='normalize-channels-checkbox',
                            options=[
                                {'label': 'Normalize Channels', 'value': 'enable'}
                            ],
                            value=[]
                        ),

                        # -------------------------------------------------------------------------------

                        # Add break
                        html.Br(),

                        # -------------------------------------------------------------------------------

                        # Checkbox to enable/disable zero-value pixels dropping
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
        dcc.Store(id='slice-data'),
        dcc.Store(id='superpixel-data'),
        dcc.Store(id='vector-data'),
        dcc.Store(id='cluster-data'),
        dcc.Store(id='cluster-number', data=5),
        dcc.Store(id='class-tracker'),
        dcc.Store(id='volume-data'),
    ]
)

# -------------------------------------------------------------------------------

# Callback to populate the dropdown on page load
@app.callback(
    Output('volume-data', 'data'),
    Input('volume-dropdown', 'value')
)
def load_volume_data(volume_name):
    # Load the volume data based on the selected volume name
    volume = np.load(f'../../data/volume_labels_{volume_name}.npy')

    print("--------------------------------")
    print(f"Volume data loaded for {volume_name}.")

    return volume.tolist()  # Convert to list for JSON serialization

# -------------------------------------------------------------------------------

# Visualize 3D volume inside Dash app
@app.callback(
    Output('content-div', 'children'),
    Input('volume-dropdown', 'value')
)
def embed_page(volume_name):

    return html.Iframe(
        # src='http://localhost:8080?timestamp={'+str(time.time())+'}',
        src='http://localhost:8080/index.html?dataset='+volume_name,
        style={
            'width': '100%',
            'height': '520px',
            'border': 'none'
        }
    )

# -------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True, use_reloader=True)
    app.run(dev_tools_hot_reload=True, debug=True)