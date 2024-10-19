import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from skimage import color
from skimage.io import imread
from sklearn.preprocessing import LabelEncoder

# Load the image and convert to RGB
image = imread('data1.jpg')
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Step 1: Flatten the image into a 2D array of pixels (with 3 color channels)
height, width, channels = image.shape
pixels = image.reshape(-1, 3)  # Reshape into (num_pixels, 3)

# Step 2: Load the ground truth (segmentation labels) as a grayscale image
# The ground truth image should have different regions labeled with different pixel values
# For simplicity, assuming a labeled image is available, typically generated manually.
ground_truth = imread('path_to_labeled_image.png', as_gray=True)

# Flatten the ground truth labels
labels = ground_truth.flatten()

# Ensure labels are integers for classification (if using grayscale)
le = LabelEncoder()
labels = le.fit_transform(labels)

# Step 3: Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(pixels, labels, test_size=0.3, random_state=42)

# Step 4: Train a Random Forest Classifier
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Step 5: Predict labels for the test set
y_pred = clf.predict(X_test)

# Step 6: Evaluate the accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f'Random Forest Classifier Accuracy: {accuracy:.2f}')

# Step 7: Predict the labels for all pixels in the image
pred_labels = clf.predict(pixels)

# Reshape the predicted labels back to the image's shape
segmented_image = pred_labels.reshape(height, width)

# Step 8: Display the original image and segmented image
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title('Original Image')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(segmented_image, cmap='nipy_spectral')
plt.title('Random Forest Segmentation')
plt.axis('off')

plt.tight_layout()
plt.show()
