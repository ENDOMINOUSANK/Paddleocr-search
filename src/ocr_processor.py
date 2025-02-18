# from dask import delayed, compute
# import os
# from paddleocr import PaddleOCR
# import re

# ocr = PaddleOCR(use_angle_cls=True, lang='en')

# @delayed

# def process_image_file(image_path, selected_prop, regex, prompt):
#     """
#     Given an image file path, run PaddleOCR and extract text.
#     Then try to extract a value based on the given prompt, selected property, and regex.
#     Returns (extracted_text, extracted_value).
#     """
#     # Initialize PaddleOCR
#     ocr = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=False, image_orientation=True)
#     result = ocr.ocr(image_path, cls=True)
    
#     extracted_text = ""
#     for line in result:
#         for word in line:
#             text, confidence = word[1]
#             if confidence >= 0.85:
#                 extracted_text += str(text) + " "
#     extracted_text = extracted_text.strip()
#     print(f"Processed {os.path.basename(image_path)} - Extracted Text: {extracted_text}")
    
#     extracted_value = None
#     # For other prompts, find the selected property and extract value from nearby text
#     generalized_prop = re.sub(r'[_\s]', r'[\\s_]*', selected_prop, flags=re.IGNORECASE)
#     prop_pattern = re.compile(generalized_prop, re.IGNORECASE)
#     prop_match = prop_pattern.search(extracted_text)
#     if prop_match:
#         start_pos = prop_match.end()
#         # First try: search for a number immediately after the property match
#         value_pattern = re.compile(regex)
#         value_match = value_pattern.search(extracted_text, pos=start_pos)
#         # If not found, search within the next 100 characters
#         if not value_match:
#             window_text = extracted_text[start_pos: start_pos + 100]
#             value_match = value_pattern.search(window_text)
#         if value_match:
#             extracted_value = value_match.group()
#             if len(extracted_value) == 1:
#                 extracted_value = None
#     return extracted_text, extracted_value
# def process_nested_list_padd(nested_list):
#     return [item for sublist in nested_list for item in sublist]

# def process_images(image_paths):
#     delayed_results = [process_image_file(image_path) for image_path in image_paths]
#     results = compute(*delayed_results)
#     return process_nested_list_padd(results)