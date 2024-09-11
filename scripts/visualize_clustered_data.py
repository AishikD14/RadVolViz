import json

# Function to load and parse the JSON file
def load_array_from_file(filename):
    with open(filename, 'r') as file:
        array = json.load(file)
    return array

# Recursive function to get the shape of an n-dimensional array
def get_shape(arr):
    shape = []
    while isinstance(arr, list):
        shape.append(len(arr))
        arr = arr[0] if len(arr) > 0 else []
    return shape

# Find the number of unique values in the array
def find_unique_values(arr):
    unique_values = set()
    for item in arr:
        if isinstance(item, list):
            unique_values.update(find_unique_values(item))
        else:
            unique_values.add(item)
    return unique_values

# Function to count the number of occurrences of each unique value in the array
def count_occurrences(arr):
    occurrences = {}
    for item in arr:
        if isinstance(item, list):
            sub_occurrences = count_occurrences(item)
            for key, value in sub_occurrences.items():
                occurrences[key] = occurrences.get(key, 0) + value
        else:
            occurrences[item] = occurrences.get(item, 0) + 1
    return occurrences

# Example: Parse the 'array3D.json' file
filename = 'clusteredData.json'
parsed_array = load_array_from_file(filename)

shape = get_shape(parsed_array)

# Display the parsed array
print(shape)

# Example: Find the unique values in the parsed array
unique_values = find_unique_values(parsed_array)

# Display the unique values
print(len(unique_values))
print(unique_values)

# Example: Count the occurrences of each unique value in the parsed array
occurrences = count_occurrences(parsed_array)

# Display the occurrences
print(occurrences)