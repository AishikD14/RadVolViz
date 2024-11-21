import numpy as np
import matplotlib.pyplot as plt
from skimage import segmentation, color
from skimage.io import imread
from skimage import graph
from skimage.segmentation import mark_boundaries
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.decomposition import PCA
from skimage.util import img_as_float, img_as_ubyte
from skimage.color import label2rgb
import math
import random
import matplotlib.colors as mcolors
import warnings
import matplotlib.patheffects as patheffects
import cv2
from sklearn.metrics.pairwise import cosine_distances

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------------

# Generate histogram (2D) using numpy
def generate_histogram(data, bins, range_x, range_y):
    hist, xedges, yedges = np.histogram2d(data[:, 0], data[:, 1], bins=bins, range=[range_x, range_y])
    return hist, xedges, yedges

# Function to create a representative sampling of points from histogram bins
def draw(hist, data, xedges, yedges, vararr, ss):
    Q = []
    T = 0

    rowName = np.array(["Ce","Co","Fe","Gd"])
    
    # Iterate over each bin in the histogram
    for i in range(hist.shape[0]):
        for j in range(hist.shape[1]):
            bin_count = int(hist[i, j])
            # Get indices of data points that fall within the current bin
            bin_mask = (
                (data[:, 0] >= xedges[i]) & (data[:, 0] < xedges[i + 1]) &
                (data[:, 1] >= yedges[j]) & (data[:, 1] < yedges[j + 1])
            )
            bin_points = data[bin_mask]

            if bin_count > 500:
                # Sample points proportional to 5 * log2 of the bin size
                sample_size = int(5 * math.log2(bin_count))
                Q.extend(random.sample(list(bin_points), min(sample_size, len(bin_points))))
            elif 50 < bin_count < 500:
                # Sample points proportional to log2 of the bin size
                sample_size = int(math.log2(bin_count))
                Q.extend(random.sample(list(bin_points), min(sample_size, len(bin_points))))
            else:
                # Sample half of the bin points if bin size is <= 50
                sample_size = bin_count // 2
                Q.extend(random.sample(list(bin_points), min(sample_size, len(bin_points))))
    
    Q = np.array(Q)

    # Replace the first 4 entries of the Q array with the last 4 rows of the data (vararr)
    for ij in range(4):
        Q[T] = vararr[ij]
        T += 1

    # Length of the 'ss' array and number of keys in the first row of 'datum'
    m = len(ss)
    n = len(rowName)

    # Create an array of dictionaries for varPoints
    varPoints = [{} for _ in range(n)]

    # Populate varPoints with GBCX, GBCY, and NAME values
    for i in range(n):
        varPoints[i]['GBCX'] = ss[m - n + i][0]
        varPoints[i]['GBCY'] = ss[m - n + i][1]
        varPoints[i]['NAME'] = rowName[i]

    # Setup for the canvas dimensions
    color_space_width = 400
    color_space_height = 400
    diameter = round(color_space_height * 2.4 / 3.1)

    # Offsets and centers
    x_offset = (color_space_width - diameter) / 2
    y_offset = (color_space_height - diameter) / 2

    # Create a figure and axis for plotting
    fig, ax = plt.subplots(figsize=(color_space_width / 100, color_space_height / 100))

    # Color scale mapping (simulating the D3 scale)
    scale_gbc2canvas_x = lambda x: np.interp(x, [-1, 1], [x_offset, x_offset + diameter])
    scale_gbc2canvas_y = lambda y: np.interp(y, [-1, 1], [y_offset, y_offset + diameter])

    scale_gbc2canvas_x_inverse = lambda x: np.interp(x, [x_offset, x_offset + diameter], [-1, 1])
    scale_gbc2canvas_y_inverse = lambda y: np.interp(y, [y_offset, y_offset + diameter], [-1, 1])

    # Create the canvas (in this case, a blank image that we'll fill in)
    canvas = np.zeros((color_space_height, color_space_width, 3), dtype=np.uint8)

    # Assuming `guiControls.brushMode` is either 1.0 or 2.0 for colored display
    brush_mode = 0.0

    # Fill the canvas with the color space
    for i in range(int(x_offset), int(x_offset + diameter)):
        for j in range(int(y_offset), int(y_offset + diameter)):
            x_invert = scale_gbc2canvas_x_inverse(i)
            y_invert = scale_gbc2canvas_y_inverse(j)

            if brush_mode == 1.0 or brush_mode == 2.0:
                color = CoordToColor_ring(x_invert, y_invert)
            else:
                color = CoordToColor(x_invert, y_invert)

            canvas[j, i] = (np.array(color)[:3] * 255).astype(int)  # Use only RGB, ignore alpha & Scale to [0, 255] for display

    # Display the image using matplotlib
    # ax.imshow(canvas)
    ax.axis('off')  # Turn off the axis

    # Plot scatter points on the color space based on downsampled data Q
    num_ch = len(Q)  # Assuming Q is your downsampled data

    scatter_x = [scale_gbc2canvas_x(d[0]) for d in Q]
    scatter_y = [scale_gbc2canvas_y(d[1]) for d in Q]
    ax.scatter(scatter_x, scatter_y, c=[GBCtoHCL_ring(d[0], d[1]) for d in Q], s=2.5, edgecolors='white', alpha=0.5)
    
    scatter_x1 = [scale_gbc2canvas_x(d['GBCX'] * 0.997) for d in varPoints]
    scatter_y1 = [scale_gbc2canvas_y(d['GBCY'] * 0.997) for d in varPoints]
    ax.scatter(scatter_x1, scatter_y1, c=[GBCtoHCL_ring(d['GBCX'] * 0.997, d['GBCY'] * 0.997) for d in varPoints], s=15)
    
    for d in varPoints:
        x = scale_gbc2canvas_x(d['GBCX'] * 0.997)
        y = scale_gbc2canvas_y(d['GBCY'] * 0.997)

        # Determine the text offsets
        dy = "-.230em" if d['GBCY'] < 0 else ".531em"
        dx = "-1.40em" if d['GBCX'] < 0 else ".35em"

        # Convert `em` offsets to pixel values if needed (in this example, using a fixed pixel offset)
        dy_pixel = -8 if d['GBCY'] < 0 else 8
        dx_pixel = -20 if d['GBCX'] < 0 else 5

        # Add text to the plot
        text = ax.text(
            x + dx_pixel,
            y + dy_pixel,
            d['NAME'],
            fontsize=20,
            color='black',
            ha='center',
            va='center',
            alpha=1  # Text opacity
        )

        # Add stroke effect for text
        text.set_path_effects([patheffects.withStroke(linewidth=2, foreground="white")])

    # plt.show()

# Function to constrain CX and CY values to the unit circle
def ConstrainInUnit(CX, CY):
    r = math.sqrt(CX**2 + CY**2)
    if r > 1:
        CX /= r
        CY /= r
    return CX, CY

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
def GBCtoHCL_ring(CX, CY):
    if CX * CX + CY * CY > 0.999999:
        return mcolors.to_rgba((0, 0, 0))  # Return black (similar to d3.rgb(0, 0, 0))

    # Compute the hue angle
    h = math.atan2(CY, CX) + math.pi / 2
    if h < 0:
        h = h + 2 * math.pi
    if h > 2 * math.pi:
        h = h - 2 * math.pi

    # Convert hue to degrees
    h = (h / math.pi) * 180

    # Saturation (distance from the origin)
    s = math.sqrt(CX**2 + CY**2)

    # Lightness (constant value)
    l = 0.55

    # Normalize hue to [0, 1] for HSL color space (as used by matplotlib)
    h /= 360.0
    s = s  # Maintain saturation as calculated
    l = l  # Use constant lightness

    # Convert HSL to RGB using matplotlib
    return mcolors.hex2color("#C7D9E8")

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

# Alternative function to handle different color behavior (ring-based)
def CoordToColor_ring(CX, CY):
    CX, CY = ConstrainInUnit(CX, CY)
    return GBCtoHCL_ring(CX, CY)

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

# Custom SLIC function with cosine distance metric
def custom_slic(image, n_segments=100, compactness=10, sigma=1):
    # Get initial superpixels using standard SLIC
    segments = segmentation.slic(image, n_segments=n_segments, compactness=compactness, sigma=sigma, start_label=0)
    
    # Iterate over each segment and refine based on cosine distance between pixels in each segment
    refined_segments = np.zeros_like(segments)
    
    for seg_val in np.unique(segments):
        mask = segments == seg_val
        
        # Extract pixels belonging to this segment
        segment_pixels = image[mask]
        
        # Compute pairwise cosine distances within this segment
        distances = cosine_distances(segment_pixels)
        
        # Cluster pixels based on cosine distances (for simplicity, we keep it as one segment here)
        refined_segments[mask] = seg_val
    
    return refined_segments

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
    
# Updated weight function to include both mean log-ratio (ALR) and variance differences
def weight_mean_alr_and_variance(graph, src, dst, n):
    """Calculate weight between two regions based on both mean log-ratio (ALR) and variance similarity."""
    mean_diff = graph.nodes[src]['mean color'] - graph.nodes[dst]['mean color']
    mean_alr_weight = np.linalg.norm(mean_diff)
    
    var_diff = graph.nodes[src]['variance'] - graph.nodes[dst]['variance']
    var_weight = np.linalg.norm(var_diff)

    total_weight = mean_alr_weight + var_weight
    
    return {'weight': total_weight}

# -------------------------------------------------------------------------------

# Load volume data
volume = np.load('../volume.npy')

# Normalize the value of each voxel so that the sum of all channels is 1
volume = volume / 255

# -------------------------------------------------------------------------------

# Create a list having all the voxels
voxels = []
for x in range(volume.shape[0]):
    for y in range(volume.shape[1]):
        for z in range(volume.shape[2]):
            voxels.append(volume[x][y][z])

# Convert the list to a numpy array
voxels = np.array(voxels)
print(voxels.shape)

# Drop all the voxels having all the channels as 0
voxels = voxels[~np.all(voxels == 0, axis=1)]
print(voxels.shape)

# Downsample the voxels to 69317
# voxels = voxels[:69317]
# print(voxels.shape)
# print(voxels[0])

# -------------------------------------------------------------------------------

# embedMode = 1
# rotateVar = 0.0

# # Get coordinate from metal ratios
# if embedMode == 1:
#     ss = GBC(voxels, rotateVar)

# row = len(ss)
# col = len(ss[0])

# # Get all data except the last 4 rows
# newarr = []
# for i in range(row - 4):
#     newarr.append([])
#     for j in range(col):
#         newarr[i].append(ss[i][j])

# vararr = []
# for i, j in zip(range(row - 4, row), range(4)):
#     vararr.append([ss[i][0], ss[i][1], 0, 0, 0, 0])

# newarr = np.array(newarr)
# vararr = np.array(vararr)

# Generate the 2D histogram
# hist, xedges, yedges = generate_histogram(newarr, bins=6, range_x=(-1, 1), range_y=(-1, 1))

# Draw the scatter points based on the histogram
# draw(hist, newarr, xedges, yedges, vararr, ss)

# quit()

# -------------------------------------------------------------------------------

# Loop over each x-axis slice
slice_allowed = [90, 100, 130, 150, 170]
slice_allowed = [130]
for x in range(volume.shape[0]):
    if x not in slice_allowed:
        continue

    image = volume[x, :, :]
    print(image.shape)

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

    # Loop though each pixel in the image and assign custom colors based on Radviz
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

    # Print the values of the first pixel before and after transformation
    print(f'Original Pixel Value: {resized_image[125, 125]}')
    print(f'ALR Transformed Pixel Value: {alr_image[125, 125]}')

    # Apply SLIC segmentation on the transformed image (now shape is (256, 256, 3))
    segments = segmentation.slic(alr_image, n_segments=400, compactness=10, sigma=1)

    # Apply custom SLIC segmentation using cosine distance metric
    # segments = custom_slic(resized_image, n_segments=400, compactness=10, sigma=1)

    # -------------------------------------------------------------------------------

    # Create a Region Adjacency Graph (RAG) based on the superpixels
    rag = graph.rag_mean_color(input_image, segments)

    # Initialize variance for each node in the RAG
    for region in rag.nodes:
        # Extract the pixels of the current superpixel
        mask = (segments == region)
        pixels = input_image[mask]

        # Calculate variance for each color channel (R, G, B)
        variance = np.var(pixels, axis=0)
        
        # Store variance in the RAG
        rag.nodes[region]['variance'] = variance

    # -------------------------------------------------------------------------------

    # Apply hierarchical merging using the mean color similarity
    labels = graph.merge_hierarchical(segments, rag, thresh=2.5, rag_copy=False,
                                    in_place_merge=True,
                                    merge_func=merge_mean_color_and_variance,
                                    weight_func=weight_mean_color_and_variance)

    # -------------------------------------------------------------------------------

    plt.figure(figsize=(16, 5))

    # Visualize the Original image 
    plt.subplot(1, 3, 1)
    plt.imshow(input_image) 
    plt.title('Original Image')
    plt.axis('off')

    # Visualize the superpixel-boundary marked image
    plt.subplot(1, 3, 2)
    plt.imshow(mark_boundaries(input_image, segments))
    plt.title('SLIC Superpixel')
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(mark_boundaries(input_image, labels))
    plt.title('Hierarchical Clustering Segmentation')
    plt.axis('off')

    # Set an overall title for the figure
    plt.suptitle(f'Volume Slice {x}')

    plt.tight_layout()
    plt.show()
