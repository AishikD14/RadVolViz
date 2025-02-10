import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import warnings
import math
import matplotlib.colors as mcolors
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import time

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------------

isimage = False

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

if isimage:

    # Load the image
    image = cv2.imread('data1.jpg')
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert from BGR (OpenCV) to RGB (matplotlib friendly)

    # Reshape the image to a 2D array of pixels
    pixels = image.reshape(-1, 3)

    # --------------------------------------------------------------
    # Preprocessing steps

    # Normalize pixel values to the [0, 1] range
    pixels_normalized = pixels / 255.0

    # Apply Gaussian blur to the image
    blurred_image = cv2.GaussianBlur(image, (5, 5), 0)
    pixels_blurred = blurred_image.reshape(-1, 3)

    # --------------------------------------------------------------

    # Apply KMeans to cluster the pixel intensities
    k = 7  # Number of clusters
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels_blurred)

    # Replace each pixel value with its corresponding cluster centroid
    clustered = kmeans.cluster_centers_[kmeans.labels_]
    clustered = np.clip(clustered.astype('uint8'), 0, 255)

    # Reshape the clustered pixels back into the original image shape
    clustered_image = clustered.reshape(image.shape)

    # Display the original and clustered image
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(image)
    plt.title('Original Image')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(clustered_image)
    plt.title(f'K-Means Clustering with {k} Clusters')
    plt.axis('off')

    plt.show()

# -------------------------------------------------------------------------------------------

else:

    # Load volume data
    volume = np.load('../../xray_volume.npy')

    # Loop over each x-axis slice
    slice_allowed = [90, 100, 130, 150]
    slice_allowed = [130]
    for x in range(volume.shape[0]):
        if x not in slice_allowed:
            continue

        image = volume[x, :, :]
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

        plt.figure(figsize=(6, 5))

        # Visualize the Original image 
        # plt.subplot(1, 2, 1)
        plt.imshow(input_image)  
        plt.title('Original Image')
        plt.axis('off')

        # Set an overall title for the figure
        plt.suptitle(f'Volume Slice {x}')

        plt.tight_layout()
        # plt.show()

        # -------------------------------------------------------------------------------

        vector = []

        for i in range(resized_image.shape[0]):
            for j in range(resized_image.shape[1]):
                vector.append(resized_image[i][j])

        vector = np.array(vector)

        # -------------------------------------------------------------------------------

        # Perform t-SNE for dimensionality reduction
        tsne = TSNE(n_components=2, random_state=42)
        reduced_data = tsne.fit_transform(vector)

        # Create dummy labels for visualization (use actual labels if available)
        segment_labels = np.arange(len(reduced_data))

        # Extract colors for each segment in the same order as `segment_ids`
        # color_array = np.array([segmentColorDict[seg_id] for seg_id in segment_labels])

        # Create a scatter plot of the t-SNE reduced data
        plt.figure(figsize=(10, 8))

        scatter = plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=segment_labels, cmap='viridis', alpha=0.7)

        plt.title('t-SNE Visualization of Segments')
        plt.xlabel('t-SNE Component 1')
        plt.ylabel('t-SNE Component 2')
        plt.grid(True)
        # plt.show()
        # quit()

        # -------------------------------------------------------------------------------
        
        # Perform K-means clustering on the segment vectors to get an initial set of clusters

        start_time = time.time()

        # Number of clusters
        num_clusters = 5

        # Perform K-means clustering
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(vector)

        print(f"K-means clustering completed in {time.time() - start_time:.2f} seconds")

        colormap = plt.get_cmap("tab10")

        # Create a scatter plot of the t-SNE reduced data with cluster labels
        plt.figure(figsize=(10, 8))
        for i in range(num_clusters):  # 5 clusters
            plt.scatter(reduced_data[cluster_labels == i, 0], reduced_data[cluster_labels == i, 1], color=colormap(i), label=f'Cluster {i+1}')

        # Add legend
        plt.legend()

        plt.title('t-sne Visualization of Segments after K-means Clustering')
        plt.xlabel('t-sne Component 1')
        plt.ylabel('t-sne Component 2')
        plt.grid(True)
        # plt.show()

        # -------------------------------------------------------------------------------

        # Extract the color codes for the final clusters to create the final segmented image

        # Get unique cluster IDs from the cluster labels and store the corresponding colors in a dictionary
        cluster_color_dict = dict()
        for cluster_id in np.unique(cluster_labels):
            cluster_color_dict[cluster_id] = tuple(map(lambda x: int(x * 255), colormap(cluster_id)[:3]))

        print("Cluster Color Dictionary for K-means clusters: ", cluster_color_dict)
        print("---------------------------------")

        # -------------------------------------------------------------------------------

        # Create the final segmented image using the cluster colors

        # Create an image to store the colors for each pixel
        final_segmented_image = np.zeros_like(resized_image, dtype=np.uint8)
        # Drop the alpha channel
        final_segmented_image = final_segmented_image[:, :, :3]

        count = 0
        for i in range(resized_image.shape[0]):
            for j in range(resized_image.shape[1]):
                final_segmented_image[i][j] = cluster_color_dict[cluster_labels[count]]
                count += 1

        # Display the original image and the final segmented image
        plt.figure(figsize=(12, 5))

        # Visualize the Original image
        plt.subplot(1, 2, 1)
        plt.imshow(input_image)
        plt.title('Original Image')
        plt.axis('off')

        # Visualize the Final Segmented image
        plt.subplot(1, 2, 2)
        plt.imshow(final_segmented_image)
        plt.title('Final Segmented Image')
        plt.axis('off')

        # Set an overall title for the figure
        plt.suptitle(f'Volume Slice {x}')

        plt.tight_layout()
        plt.show()
        # quit()