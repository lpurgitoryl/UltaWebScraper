# example query result in productquery.json
# this was used to figure out how to parse the json result using the bs4 scraper
import json

def write_to_file(filename, text, mode="w"):
    """Writes the given text to the specified file.

    Args:
        filename: The name of the file to write to.
        text: The text to write.
        mode: The mode to open the file in ("w" for write, "a" for append).
    """
    with open(filename, mode) as file:
        file.write(text)

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return f"Error: File not found at path: {file_path}"
    except json.JSONDecodeError:
         return f"Error: Invalid JSON format in file: {file_path}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    
def get_all_keys(json_obj, keys_list=None, prefix=""):
    if keys_list is None:
        keys_list = []
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            keys_list.append(new_prefix)
            get_all_keys(v, keys_list, new_prefix)
    elif isinstance(json_obj, list):
        for i, item in enumerate(json_obj):
            get_all_keys(item, keys_list, f"{prefix}[{i}]")
    return keys_list

def find_keys_by_value(json_data, target_value, path=""):
    """
    Recursively searches a JSON object for keys leading to a specific value.

    Args:
        json_data: The JSON object (dict or list) to search.
        target_value: The value to search for.
        path: The current path of keys (used in recursive calls).

    Returns:
        A list of paths (lists of keys) leading to the target value, or an empty list if not found.
    """
    results = []

    if isinstance(json_data, dict):
        for key, value in json_data.items():
            new_path = path + "." + key if path else key
            if value == target_value:
                results.append(new_path)
            elif isinstance(value, (dict, list)):
                results.extend(find_keys_by_value(value, target_value, new_path))

    elif isinstance(json_data, list):
        for index, item in enumerate(json_data):
            new_path = path + f"[{index}]" if path else f"[{index}]"
            if item == target_value:
                results.append(new_path)
            elif isinstance(item, (dict, list)):
                results.extend(find_keys_by_value(item, target_value, new_path))
    return results
    
file_path = 'productquery.json'
json_data = read_json_file(file_path)
all_keys = get_all_keys(json_data["data"]["Page"]["content"]["modules"])

keys = json_data["data"]["Page"]["content"]["modules"]

target_value = "ProductInformation"
paths = find_keys_by_value(keys, target_value)
print(paths)

target_value = "ProductPricing"
paths = find_keys_by_value(keys, target_value)
print(paths)

target_value = "ProductSummary"
paths = find_keys_by_value(keys, target_value)
print(paths)

target_value = "ProductDetail"
paths = find_keys_by_value(keys, target_value)
print(paths)

target_value = '40b1ef54-01a7-4c3e-bc9c-8b8c0d3d1840' #"ProductVariant"
paths = find_keys_by_value(keys, target_value)
print(paths)

target_value = "ProductReviews"
paths = find_keys_by_value(keys, target_value)
print(paths)

# write_to_file("keys.txt", ", ".join(json_data["data"]["Page"]["content"]["modules"][4]["modules"][1]))

# ProductInformation json_data["data"]["Page"]["content"]["modules"][4]["modules"][1]
# ProductPricing json_data["data"]["Page"]["content"]["modules"][4]["modules"][3]

# ProductSummary json_data["data"]["Page"]["content"]["modules"][4]["modules"][4]
# ProductDetail json_data["data"]["Page"]["content"]["modules"][4]["modules"][5]

# ProductVariant json_data["data"]["Page"]["content"]["modules"][4]["modules"][6]
# ProductReviews json_data["data"]["Page"]["content"]["modules"][12]

# excluding producthero and 


