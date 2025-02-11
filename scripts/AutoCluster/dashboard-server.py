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

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../../xray_volume.npy')

# -------------------------------------------------------------------------------



# -------------------------------------------------------------------------------

# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1(children='Dashboard'),

    html.Div(children=[
        # Control Panel
        html.Div(children=[
            html.H2(children='Control Panel'),

            # Radio Button for selection of axis for slicing
            html.Label('Select axis for slicing volume:'),
            dcc.RadioItems(
                id='axis-radio',
                options=[
                    {'label': 'X', 'value': 'x'},
                    {'label': 'Y', 'value': 'y'},
                    {'label': 'Z', 'value': 'z'}
                ],
                value = "x"
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
                    html.H2(children='Original Slice'),
                    dcc.Graph(
                        id='slice-plot'
                    ),
                ], style={'width': '33%', 'display': 'inline-block'}),

                # -------------------------------------------------------------------------------

                # Superpixel Segmentation
                html.Div(children=[
                    html.H2(children='Superpixel Segmentation'),
                    dcc.Graph(
                        id='superpixel-plot'
                    ),
                ], style={'width': '33%', 'display': 'inline-block'}),

                # -------------------------------------------------------------------------------

                # Final Segmented Slice
                html.Div(children=[
                    html.H2(children='Final Segmented Slice'),
                    dcc.Graph(
                        id='final-plot'
                    ),
                ], style={'width': '33%', 'display': 'inline-block'}),

            ]),

            # -------------------------------------------------------------------------------

            # Bottom Half Display
            html.Div(children=[

                # Elbow Plot for Clustering
                html.Div(children=[
                    html.H2(children='Elbow Plot for Clustering'),
                    dcc.Graph(
                        id='elbow-plot'
                    ),
                ], style={'width': '50%', 'display': 'inline-block'}),

                # -------------------------------------------------------------------------------

                # Vector Space Visualization
                html.Div(children=[
                    html.H2(children='Vector Space Visualization'),
                    dcc.Graph(
                        id='vector-plot'
                    ),
                ], style={'width': '50%', 'display': 'inline-block'}),

            ]),

        ], style={'width': '80%'}),

    ], style={'display': 'flex'}),
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)