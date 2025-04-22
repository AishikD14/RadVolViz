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

# Function to create cluster vector plot
def create_cluster_vector_plot(segment_vectors, cluster_labels, visualization, hovered_segment_id):

    # Create a DataFrame for easier plotting
    if visualization == 'pca':
        # Perform PCA for dimensionality reduction
        pca = PCA(n_components=2, random_state=42)
        reduced_data = pca.fit_transform(segment_vectors)

        # Create a DataFrame for easier plotting
        df = pd.DataFrame(reduced_data, columns=['PCA Dimension 1', 'PCA Dimension 2'])

    elif visualization == 'tsne':
        # Perform t-SNE for dimensionality reduction
        tsne = TSNE(n_components=2, random_state=42)
        reduced_data = tsne.fit_transform(segment_vectors)

        # Create a DataFrame for easier plotting
        df = pd.DataFrame(reduced_data, columns=['t-SNE Dimension 1', 't-SNE Dimension 2'])

    elif visualization == 'PC':
        reduced_data = segment_vectors

        df = pd.DataFrame(reduced_data, columns=['Ce', 'Co', 'Fe', 'Gd'])

    df['Cluster ID'] = cluster_labels
    # Convert Cluster ID to a string to ensure it's treated as categorical
    df['Cluster ID'] = df['Cluster ID'].astype(str)
    df['Cluster-ID'] = df['Cluster ID'].astype(int)

    segment_labels = np.arange(len(reduced_data))
    df['Segment ID'] = segment_labels

    # Extract Tab10 colors from Matplotlib
    tab10_colors = [plt.get_cmap("tab10")(i) for i in range(len(df['Cluster ID'].unique()))]
    tab10_colors = ["rgb({}, {}, {})".format(int(r*255), int(g*255), int(b*255)) for r, g, b, _ in tab10_colors]

    # Normalized levels
    normalized_levels = np.linspace(0, 1, len(tab10_colors))

    # Create color scale of format [[level, color], ...]
    color_scale = [[level, color] for level, color in zip(normalized_levels, tab10_colors)]

    if visualization == 'pca':
        fig = px.scatter(
            df,
            x='PCA Dimension 1',
            y='PCA Dimension 2',
            color='Cluster ID',
            category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
            hover_data=['Cluster ID', 'Segment ID'],
            labels={"Cluster ID": "Cluster ID"},
            color_discrete_sequence=tab10_colors
        )

    elif visualization == 'tsne':
        fig = px.scatter(
            df,
            x='t-SNE Dimension 1',
            y='t-SNE Dimension 2',
            color='Cluster ID',
            category_orders={"Cluster ID": ["0", "1", "2", "3", "4"]},
            hover_data=['Cluster ID', 'Segment ID'],
            labels={"Cluster ID": "Cluster ID"},
            color_discrete_sequence=tab10_colors
        )

    elif visualization == 'PC':

        df_copy = df.copy()

        df_copy.drop(columns=['Segment ID', 'Cluster ID'], inplace=True)

        color_column = 'Cluster-ID'

        # Generate dimensions dynamically from df_copy, excluding the color column
        dimensions = list([
            dict(label=col, values=df_copy[col]) 
            if col != color_column 
            else dict(label=col, values=df_copy[col], tickvals=np.arange(len(df_copy[color_column].unique())))
            for col in df_copy.columns
        ])

        # Create the figure dynamically
        fig = go.Figure(data=[
            go.Parcoords(
                line=dict(
                    color=df_copy[color_column], 
                    colorscale=color_scale  
                ),
                dimensions=dimensions
            )
        ])

        fig.update_layout(
            font=dict(color="white")
        )

    if visualization == 'pca' or visualization == 'tsne':
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

        if hovered_segment_id is not None:

            # Highlight the corresponding segment in the t-SNE plot
            highlighted_segment = df[df['Segment ID'] == hovered_segment_id]

            # Dim non-selected segments
            fig.update_traces(marker=dict(opacity=0.3), selector=dict(mode='markers'))

            # Add a trace for the highlighted segment
            fig.add_trace(
                go.Scatter(
                    x=highlighted_segment['t-SNE Dimension 1' if visualization == 'tsne' else 'PCA Dimension 1'],
                    y=highlighted_segment['t-SNE Dimension 2' if visualization == 'tsne' else 'PCA Dimension 2'],
                    mode='markers',
                    marker=dict(size=15, color='black', opacity=1),
                    hoverinfo='skip',  # Hide hover info for the highlighted segment,
                    showlegend=False  # Hide legend for the highlighted segment
                )
            )

    return fig, df

# Function to create clusters
def create_clusters(segment_vectors, clustering, cluster_number):
    num_clusters = cluster_number

    if clustering == 'gmm':
        gmm = GaussianMixture(n_components=num_clusters, random_state=42)
        cluster_labels = gmm.fit_predict(segment_vectors)

    elif clustering == 'kmeans':
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(segment_vectors)

    # Initialize selected clusters for swapping
    cluster_color_dict = {}

    colormap = plt.cm.get_cmap("tab10")

    cluster_colors = {}
    for i in range(num_clusters): 
        color = colormap(i)
        cluster_colors[i] = color

    cluster_color_dict = cluster_colors

    for cluster_id in np.unique(cluster_labels):
        cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), cluster_color_dict[cluster_id][:3]))

    return cluster_labels, cluster_color_dict

# Function to create cluster stats plot for KMeans clustering
def create_cluster_stats_plot(segment_vectors, clustering, cluster_number, cluster_stats):
    distortions = []
    K = range(2, 11)

    if clustering == 'gmm':
        for k in K:
            gmm = GaussianMixture(n_components=k, random_state=42)

            if cluster_stats == 'Elbow':
                gmm.fit(segment_vectors)
                distortions.append(gmm.bic(segment_vectors))
            elif cluster_stats == 'Silhouette':
                cluster_labels = gmm.fit_predict(segment_vectors)
                silhouette_score = metrics.silhouette_score(segment_vectors, cluster_labels)
                distortions.append(silhouette_score)
            elif cluster_stats == 'DBI':
                cluster_labels = gmm.fit_predict(segment_vectors)
                davies_bouldin_score = metrics.davies_bouldin_score(segment_vectors, cluster_labels)            
                distortions.append(davies_bouldin_score)

        if cluster_stats == 'Elbow':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'BIC'}, markers=True)
        elif cluster_stats == 'Silhouette':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Silhouette Score'}, markers=True)
        elif cluster_stats == 'DBI':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Davies-Bouldin Score'}, markers=True)

        # Highlight the point where K = cluster_number
        highlight_x = cluster_number
        highlight_y = distortions[K.index(cluster_number)]

        # Add a scatter point for K=cluster_number
        fig.add_trace(go.Scatter(
            x=[highlight_x],
            y=[highlight_y],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            name=' (Selected)',
            showlegend=False,
            hovertemplate=f'No of Cluster={cluster_number}'
        ))

        fig.update_layout(
            xaxis_title={
                'font': {
                    # 'color': 'white'
                    'color': '#eeeeee'
                }
            },
            yaxis_title={
                'font': {
                    # 'color': 'white'
                    'color': '#eeeeee'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            # Set the background color to light gray
            plot_bgcolor='#222831',
        )

        # Color the line
        fig.update_traces(line=dict(color='#00adb5'))

        fig.update_layout(clickmode='event')

        return fig
    
    elif clustering == 'kmeans':
        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=42)

            if cluster_stats == 'Elbow':
                kmeans.fit(segment_vectors)
                distortions.append(kmeans.inertia_)
            elif cluster_stats == 'Silhouette':
                cluster_labels = kmeans.fit_predict(segment_vectors)
                silhouette_score = metrics.silhouette_score(segment_vectors, cluster_labels)
                distortions.append(silhouette_score)
            elif cluster_stats == 'DBI':
                cluster_labels = kmeans.fit_predict(segment_vectors)
                davies_bouldin_score = metrics.davies_bouldin_score(segment_vectors, cluster_labels)
                distortions.append(davies_bouldin_score)

        if cluster_stats == 'Elbow':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Distortion'}, markers=True)
        elif cluster_stats == 'Silhouette':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Silhouette Score'}, markers=True)
        elif cluster_stats == 'DBI':
            fig = px.line(x=K, y=distortions, labels={'x': 'Number of Clusters', 'y': 'Davies-Bouldin Score'}, markers=True)

        # Highlight the point where K = cluster_number
        highlight_x = cluster_number
        highlight_y = distortions[K.index(cluster_number)]

        # Add a scatter point for K=cluster_number
        fig.add_trace(go.Scatter(
            x=[highlight_x],
            y=[highlight_y],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            name=' (Selected)',
            showlegend=False,
            hovertemplate=f'No of Cluster={cluster_number}'
        ))

        fig.update_layout(
            xaxis_title={
                'font': {
                    'color': '#eeeeee'
                }
            },
            yaxis_title={
                'font': {
                    'color': '#eeeeee'
                }
            },
            xaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            yaxis={
                'tickfont': {
                    'color': 'white'
                },
                'showgrid': False,
                'zeroline': True,
                'zerolinecolor': 'white',
                'linecolor': '#eeeeee',
                'linewidth': 2
            },
            # Set the background color to light gray
            plot_bgcolor='#222831',
        )

        # Color the line
        fig.update_traces(line=dict(color='#00adb5'))

        fig.update_layout(clickmode='event')

    return fig

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
                        # dcc.Checklist(
                        #     id='autoencoder-checkbox',
                        #     options=[
                        #         {'label': 'Enable Autoencoder', 'value': 'enable'}
                        #     ],
                        #     value=[]
                        # ),

                        # # -------------------------------------------------------------------------------

                        # # Add break
                        # html.Br(),

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
        dcc.Store(id='superpixel-data'),
        dcc.Store(id='vector-data'),
        dcc.Store(id='cluster-data'),
        dcc.Store(id='cluster-number', data=5),
        dcc.Store(id='class-tracker'),
    ]
)

# -------------------------------------------------------------------------------

# Callback to populate the dropdown on page load
@app.callback(
    [Output('superpixel-data', 'data'), Output('vector-data', 'data'), Output('supervoxel-slider', 'max'), Output('supervoxel-slider', 'marks')],
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

    print('Load volume data completed in:', time.time() - start_time)

    return json.dumps({'segments': segments}), json.dumps({'segment_vectors': segment_vectors.tolist()}), max_val, marks

# -------------------------------------------------------------------------------

# Callback for performing clustering
@app.callback(
    Output('cluster-data', 'data'),
    [Input('clustering-radio', 'value'), Input('cluster-number', 'data'), Input('clustering-checkbox', 'value'), Input('vector-data', 'data')],
    prevent_initial_call=True
)
def perform_clustering(clustering, cluster_number, clustering_checkbox, jsonified_vector_data):
    if jsonified_vector_data is None:
        return dash.no_update

    if 'enable' not in clustering_checkbox:
        return dash.no_update
    
    print("--------------------------------")
    print("Performing clustering...")
    start_time = time.time()

    vector_data = json.loads(jsonified_vector_data)

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])

    # -------------------------------------------------------------------------------

    cluster_labels, cluster_color_dict = create_clusters(segment_vectors, clustering, cluster_number)

    print('Clustering done in:', time.time() - start_time)

    return json.dumps({'cluster_labels': cluster_labels.tolist(), 'cluster_color_dict': cluster_color_dict})

# -------------------------------------------------------------------------------

# Callback for updating vector plot with clustering
@app.callback(
    [Output('cluster-vector-plot', 'figure'), Output('class-tracker', 'data'), Output('vector-data', 'data')],
    [Input('cluster-data', 'data'), Input('visualization-radio', 'value'), Input('clustering-checkbox', 'value')],
    [State('vector-data', 'data')], 
    prevent_initial_call=True
)
def update_cluster_vector_plot(jsonified_cluster_data, visualization, checkbox_value, jsonified_vector_data):
    if checkbox_value == []:
        return dash.no_update, dash.no_update, dash.no_update
    
    if jsonified_vector_data is None or jsonified_cluster_data is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    print("--------------------------------")
    print("Updating cluster vector plot...")
    start_time = time.time()

    vector_data = json.loads(jsonified_vector_data)
    cluster_data = json.loads(jsonified_cluster_data)

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])
    cluster_labels = np.array(cluster_data['cluster_labels'])

    cluster_vector_plot_fig, df = create_cluster_vector_plot(segment_vectors, cluster_labels, visualization, None)

    print('Cluster vector plot ready in:', time.time() - start_time)

    # Create vector_data JSON
    vector_data["dataframe"] = df.to_json(orient="split")
    vector_data["filters"] = {}

    return cluster_vector_plot_fig, ".cluster-vector-plot-class", json.dumps(vector_data)

# -------------------------------------------------------------------------------

# Callback for Cluster Stats Plot
@app.callback(
    [Output('elbow-plot', 'figure'), Output('cluster-number', 'data'), Output('cluster-stats-label', 'children'), Output('class-tracker', 'data')],
    [Input('vector-data', 'data'), Input('clustering-radio', 'value'), Input('elbow-plot', 'clickData'), Input('cluster-stats-radio', 'value')],
    [State('cluster-number', 'data')],
    prevent_initial_call=True
)
def update_cluster_stats_plot(jsonified_vector_data, clustering, click_data, cluster_stats, cluster_number_data):
    ctx_id = ctx.triggered_id.split('.')[0]

    print("--------------------------------")
    print("Updating cluster stats plot...")
    start_time = time.time()

    vector_data = json.loads(jsonified_vector_data)

    # Convert stored lists back to numpy arrays
    segment_vectors = np.array(vector_data['segment_vectors'])

    # -------------------------------------------------------------------------------

    if ctx_id == "elbow-plot" and click_data is not None:
        cluster_number = click_data['points'][0]['x']

        if cluster_number == cluster_number_data:
            print('Cluster stats plot ready in:', time.time() - start_time)
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        else:
            final_cluster_number_data = cluster_number

    else:
        final_cluster_number_data = cluster_number_data

    elbow_fig = create_cluster_stats_plot(segment_vectors, clustering, final_cluster_number_data, cluster_stats)

    plot_label = cluster_stats + ' Plot for Clustering'

    print('Cluster stats plot ready in:', time.time() - start_time)

    if cluster_number_data == final_cluster_number_data:
        return elbow_fig, dash.no_update, plot_label, ".elbow-plot-class"
    else:
        return elbow_fig, final_cluster_number_data, plot_label, ".elbow-plot-class"

# ------------------------------------------------------------------------------

# Visualize 3D volume inside Dash app
@app.callback(
    [Output('content-div', 'children'), Output('vector-data', 'data')],
    [Input('volume-dropdown', 'value'), Input('supervoxel-slider', 'value'), Input('filter-sv-checkbox', 'value'), Input('normalize-channels-checkbox', 'value'), Input('vector-plot', 'restyleData'), Input('cluster-vector-plot', 'restyleData'), Input('visualization-radio', 'value'), Input('cluster-number', 'data')],
    [State('superpixel-data', 'data'), State('vector-data', 'data')]
)
def embed_page(volume_name, supervoxel, filter_sv, normalize_channels, restyle_data1, restyle_data2, visualization, cluster_number_data, jsonified_superpixel_data, jsonified_vector_data):
    print("----------------------------------------------------")
    print("Generating 3D visualization")

    if ctx.triggered_id is not None:
        ctx_id = ctx.triggered_id.split('.')[0]

        if ctx_id == 'vector-plot' or ctx_id == 'cluster-vector-plot':
            if visualization == "PC":
                if restyle_data1 is not None or restyle_data2 is not None:
                    if restyle_data1 is not None and ctx_id == 'vector-plot':
                        restyle_data = restyle_data1
                    elif restyle_data2 is not None and ctx_id == 'cluster-vector-plot':
                        restyle_data = restyle_data2

                    for key, val in restyle_data[0].items():
                        if 'constraintrange' in key:
                            print(restyle_data)

                            vector_data = json.loads(jsonified_vector_data)
                            superpixel_data = json.loads(jsonified_superpixel_data)

                            segments = np.array(superpixel_data['segments'])

                            # Retrieve DataFrame
                            df_original = pd.read_json(vector_data["dataframe"], orient="split")
                            updated_filters = vector_data["filters"].copy()

                            # Extract dimension index and label
                            dimension_index = int(key.split('[')[1].split(']')[0])
                            dimension_label = df_original.columns[dimension_index]

                            if val is None or val == []:  # If filter is removed, delete it
                                updated_filters.pop(dimension_label, None)
                            else:
                                updated_filters[dimension_label] = val[0]

                            print(updated_filters)

                            # Filter the DataFrame based on the updated filters
                            filtered_df  = df_original.copy()

                            print("Applying filters...")

                            # Apply all active filters
                            for column_name, filter_ranges in updated_filters.items():
                                print("Filter ranges", filter_ranges)

                                multiple_filter = False

                                if isinstance(filter_ranges[0], list):
                                    multiple_filter = True

                                if multiple_filter:
                                    # Take into account multiple filters for the same column
                                    mask = np.zeros(len(filtered_df), dtype=bool)
                                    for filter in filter_ranges:
                                        mask |= (filtered_df[column_name] >= filter[0]) & (filtered_df[column_name] <= filter[1])
                                        
                                else:
                                    mask = (filtered_df[column_name] >= filter_ranges[0]) & (filtered_df[column_name] <= filter_ranges[1])
                                    
                                filtered_df = filtered_df[mask]

                            # Extract the segment IDs
                            segment_ids = filtered_df['Segment ID'].tolist()

                            # Create vector_data JSON
                            vector_data["filters"] = updated_filters

    print("Volume name: ", volume_name)
    print("Supervoxel: ", supervoxel)
    print("Filter supervoxel: ", filter_sv)
    print("Normalize channels: ", normalize_channels)
    print("Cluster number: ", cluster_number_data)

    print("----------------------------------------------------")

    # url = 'http://localhost:8080/index.html?dataset='+volume_name+'&timestamp={'+str(time.time())+'}'
    url = 'http://localhost:8080/index.html?dataset='+volume_name+'&cluster_count='+str(cluster_number_data)

    if 'enable' in normalize_channels:
        url = url + '&normalize_channels=True'

    if 'enable' in filter_sv:
        url = url + '&selected_supervoxel='+str(supervoxel)

    iframe = html.Iframe(
        src= url,
        style={
            'width': '100%',
            'height': '520px',
            'border': 'none'
        }
    )

    if jsonified_vector_data is None:
        return iframe, dash.no_update
    else:
        return iframe, dash.no_update
        # return iframe, json.dumps(vector_data)

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

# Clientside callback to trigger JavaScript
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="changeStyle"),
    Output("dummy", "children"),  # Dummy output
    Input("class-tracker", "data"),
    prevent_initial_call=True
)

# -------------------------------------------------------------------------------

# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True, use_reloader=True)
    app.run(dev_tools_hot_reload=False, debug=True)