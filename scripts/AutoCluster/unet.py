import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from matplotlib.patches import Patch
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from skimage.color import label2rgb
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import json

# -------------------------------------------------------------------------------

class UNet(nn.Module):
    def __init__(self, n_channels, n_classes):
        super(UNet, self).__init__()
        self.inc = DoubleConv(n_channels, 64)
        self.down1 = Down(64, 128)
        self.down2 = Down(128, 256)
        self.down3 = Down(256, 512)
        self.down4 = Down(512, 1024)
        self.up1 = Up(1024, 512)
        self.up2 = Up(512, 256)
        self.up3 = Up(256, 128)
        self.up4 = Up(128, 64)
        self.outc = OutConv(64, n_classes)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        logits = self.outc(x)
        return logits

# Helper classes for building U-Net components

class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(DoubleConv, self).__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)

class Down(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(Down, self).__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_ch, out_ch)
        )

    def forward(self, x):
        return self.maxpool_conv(x)

class Up(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(Up, self).__init__()
        self.up = nn.ConvTranspose2d(in_ch, out_ch // 2, kernel_size=2, stride=2)
        self.conv = DoubleConv(in_ch, out_ch)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)

class OutConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(OutConv, self).__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=1)

    def forward(self, x):
        return self.conv(x)

# -------------------------------------------------------------------------------

# Define the custom weight function based on both mean color and variance differences
def weight_mean_color_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean color and variance similarity."""

    # Check if any region is below the intensity threshold (black background)
    if graph.nodes[src]['mean intensity'] < intensity_threshold or graph.nodes[dst]['mean intensity'] < intensity_threshold:
        # print("source: ", src, "dest: ", dst)
        # print(f"src intensity: {graph.nodes[src]['mean intensity']}, dst intensity: {graph.nodes[dst]['mean intensity']}")
        return {'weight': 1e6}  # Prevent merging by assigning a very high weight
    
    # print("hi")
    
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_color_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)
    
    # Combine mean color and variance differences into the total weight
    total_weight = mean_color_weight + var_weight
    
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
    for i in range(iterations):
        # Perform one iteration of merging based on mean color and variance similarity
        labels = graph.merge_hierarchical(
            labels, rag, thresh=35, rag_copy=False, in_place_merge=True,
            merge_func=merge_mean_color_and_variance, weight_func=weight_mean_color_and_variance
        )

        # Rebuild the RAG based on the newly merged labels
        rag = graph.rag_mean_color(image, labels)
        
        # Reinitialize variance for the updated regions
        for region in rag.nodes:
            mask = (labels == region)
            pixels = image[mask]
            variance = np.var(pixels, axis=0)
            rag.nodes[region]['variance'] = variance
            rag.nodes[region]['mean intensity'] = np.mean(color.rgb2gray(pixels))

    return labels

# -------------------------------------------------------------------------------

# Load the image
image = imread('data1.jpg')

# -------------------------------------------------------------------------------

# Initialize variance and filter based on mean intensity
intensity_threshold = 0.15  # Threshold to ignore black regions (adjust as needed)

# Step 1: SLIC superpixels for initial segmentation
labels1 = segmentation.slic(image, compactness=30, n_segments=400, start_label=1)

# -------------------------------------------------------------------------------

# Step 3: Create a Region Adjacency Graph (RAG)
rag = graph.rag_mean_color(image, labels1)

# Initialize variance for each region (superpixel)
for region in rag.nodes:
    # Extract the pixels of the current superpixel
    mask = (labels1 == region)
    pixels = image[mask]

    # Calculate variance for each color channel (R, G, B)
    variance = np.var(pixels, axis=0)

    # Calculate mean intensity (grayscale equivalent or sum of RGB)
    mean_intensity = np.mean(color.rgb2gray(pixels))  # Using grayscale for intensity

    # Store the variance in the RAG
    rag.nodes[region]['variance'] = variance
    rag.nodes[region]['mean intensity'] = mean_intensity

# -------------------------------------------------------------------------------

# Specify the number of iterations
num_iterations = 20  # You can change this value as needed

# Step 5: Perform the iterative merging
segments = iterative_merge(image, labels1, rag, num_iterations)

# -------------------------------------------------------------------------------

# Initialize phase labels (default is -1 for all superpixels, meaning unassigned)
phase_labels = np.full(segments.shape, -1, dtype=np.int32)

# -------------------------------------------------------------------------------

# Define RGB colors for each phase (normalized to [0, 1])
phase_colors_rgb = np.array([[141/255, 211/255, 199/255], [255/255, 255/255, 179/255], [190/255, 186/255, 218/255], [251/255, 128/255, 114/255], [128/255, 177/255, 211/255]])

phase_colors = np.array([[141,211,199], [255,255,179], [190,186,218], [251,128,114], [128,177,211]])

# -------------------------------------------------------------------------------

num_phases = len(phase_colors_rgb)

# Display the image with superpixel boundaries
fig, ax = plt.subplots()
superpixel_boundaries = mark_boundaries(image, segments)
ax.imshow(superpixel_boundaries)

# Legend for phase colors
legend_patches = [Patch(color=phase_colors_rgb[i], label=f'Phase {i+1}') for i in range(num_phases)]
plt.legend(handles=legend_patches, bbox_to_anchor=(1.05, 1), loc='center')

def on_click(event):
    """Handle mouse clicks to annotate superpixels."""
    x, y = int(event.xdata), int(event.ydata)
    
    # Get the superpixel label at the clicked point
    superpixel_label = segments[y, x]
    
    # Ask for phase label
    print(f"Superpixel label: {superpixel_label}")
    phase = input(f"Enter phase for superpixel {superpixel_label} (1-{num_phases}): ")
    
    try:
        phase = int(phase)
        if 1 <= phase <= num_phases:
            # Assign the phase label to the clicked superpixel
            phase_labels[segments == superpixel_label] = phase
        else:
            print(f"Invalid phase. Please enter a value between 1 and {num_phases}.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    
    # Update the visualization: only display colored regions for labeled superpixels
    labeled_image = np.copy(image)
    for i in range(1, num_phases + 1):
        # Color only superpixels that have been labeled with phase i
        mask = (phase_labels == i)
        labeled_image[mask] = phase_colors[i-1]  # Assign phase color

    # Reapply superpixel boundaries after coloring
    labeled_image_with_boundaries = mark_boundaries(labeled_image, segments)
    ax.imshow(labeled_image_with_boundaries)
    plt.draw()

def save_annotations(phase_labels, filename='annotations.json'):
    """Save the annotated superpixel phase labels as a JSON file."""
    unique_segments = np.unique(segments)
    annotations = {str(segment): int(phase_labels[segments == segment][0]) for segment in unique_segments if np.any(phase_labels[segments == segment] != -1)}

    with open(filename, 'w') as f:
        json.dump(annotations, f)
    print(f"Annotations saved to {filename}")

# Connect the click event to the figure for interactive annotation
fig.canvas.mpl_connect('button_press_event', on_click)

# Show the initial figure
plt.show()

# Ask the user if they want to save the annotations after the plot closes
# save = input("Do you want to save the annotations? (y/n): ")
# if save.lower() == 'y':
#     save_annotations(phase_labels, 'superpixel_annotations.json')

quit()  # Exit the script after labeling the superpixels

# -------------------------------------------------------------------------------

# Step 2: Create a Region Adjacency Graph (RAG) based on the superpixels
rag = graph.rag_mean_color(image, segments)

# Initialize variance for each node in the RAG
for region in rag.nodes:
    # Extract the pixels of the current superpixel
    mask = (segments == region)
    pixels = image[mask]

    # Calculate variance for each color channel (R, G, B)
    variance = np.var(pixels, axis=0)
    
    # Store variance in the RAG
    rag.nodes[region]['variance'] = variance

# -------------------------------------------------------------------------------

# Assuming input images are normalized PCA images
n_channels = 3  # for RGB-like PCA-reduced images
n_classes = num_phases  # number of phases you're identifying
num_epochs = 10  # number of training epochs

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = UNet(n_channels, n_classes).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Training loop
for epoch in range(num_epochs):
    model.train()
    for batch in dataloader:
        images, labels = batch  # images are 3-channel, labels are phase annotations
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

    print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss.item()}")

# -------------------------------------------------------------------------------

# Display the original image, SLIC superpixels, and final segmentation
fig, ax = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)

ax[0].imshow(image)
ax[0].set_title("Original Image")
ax[0].axis('off')

ax[1].imshow(mark_boundaries(image, segments))
ax[1].set_title("SLIC Superpixels")
ax[1].axis('off')

plt.tight_layout()
plt.show()
