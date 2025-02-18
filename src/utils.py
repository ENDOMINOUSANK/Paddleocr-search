

# def process_nested_list_padd(input_list):
#     normalized_patterns = []
#     for item in input_list:
#         if isinstance(item, str):
#             if item.startswith('r"') or item.startswith("r'"):
#                 item = item[2:]
#             item = item.strip('"').strip("'")
#             normalized_item = bytes(item, "utf-8").decode("unicode_escape")
#             normalized_item = normalized_item.replace('\x08', '\\b')
#             normalized_patterns.append(normalized_item)
#         else:
#             raise ValueError(f"Unexpected non-string item in list: {item}")
#     return normalized_patterns


# def extract_filename(filepath):
#     import os
#     # Extract the filename from a given file path
#     return os.path.basename(filepath)

# def is_valid_image_file(filepath):
#     # Check if the file has a valid image extension
#     valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
#     return any(filepath.lower().endswith(ext) for ext in valid_extensions)