from dask.distributed import Client
from dask import delayed, compute
import os
import csv
import re
import time
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

def crop_upper_left(image_path):
    """
    Opens the image, crops its upper left quadrant, and returns a NumPy array.
    """
    img = Image.open(image_path)
    width, height = img.size
    cropped_img = img.crop((0, 0, width // 2, height // 2))
    return np.array(cropped_img)

def has_red_color(image_path, threshold=50, fraction=0.1):
    """
    Returns True if at least `fraction` of the pixels in the image (after comparing red channel
    to green and blue channels) have a red value > threshold.
    """
    img = Image.open(image_path).convert("RGB")
    np_img = np.array(img)
    # Create a mask: red channel is greater than threshold and red >> green and blue.
    red_mask = (np_img[:,:,0] > threshold) & (np_img[:,:,0] > np_img[:,:,1]) & (np_img[:,:,0] > np_img[:,:,2])
    if np.mean(red_mask) > fraction:
        return True
    return False
# def process_image_file(image_path, selected_prop, regex, prompt):
#     """
#     Crop the image to its upper left quadrant, run PaddleOCR to extract text,
#     then try to extract a numeric value based on the given prompt, selected property, and regex.
#     Returns (extracted_text, extracted_value).
#     """
#     # Crop the image
#     cropped_image = crop_upper_left(image_path)
    
#     # Import PaddleOCR locally to avoid pickling issues on Dask workers
#     from paddleocr import PaddleOCR

#     # Initialize PaddleOCR with desired options
#     ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, image_orientation=True)
#     # Run OCR on the cropped image (a NumPy array)
#     result = ocr.ocr(cropped_image, cls=True)
    
#     extracted_text = ""
#     for line in result:
#         for word in line:
#             text, confidence = word[1]
#             if confidence >= 0.70:
#                 extracted_text += str(text) + " "
#     extracted_text = extracted_text.strip()
    
#     # Remove tokens that are mis-detections for ranges like "Range100-750)" etc.
#     filtered_tokens = []
#     for token in extracted_text.split():
#         lower_token = token.lower()
#         # If token starts with one of the unwanted patterns, skip it
#         if (lower_token.startswith("range") or lower_token.startswith("rang") or
#             lower_token.startswith("rag") or lower_token.startswith("fange")):
#             continue
#         filtered_tokens.append(token)
    
#     extracted_text = " ".join(filtered_tokens).strip()
    
#     print(f"Processed {os.path.basename(image_path)} - Extracted Text: {extracted_text}")
    
#     extracted_value = None
#     # Attempt to extract a numeric value if the selected property is found
#     generalized_prop = re.sub(r'[_\s]', r'[\\s_]*', selected_prop, flags=re.IGNORECASE)
#     prop_pattern = re.compile(generalized_prop, re.IGNORECASE)
#     prop_match = prop_pattern.search(extracted_text)
#     if prop_match:
#         start_pos = prop_match.end()
#         # First try: search for a number immediately after the property match
#         value_pattern = re.compile(regex)
#         window_forward = extracted_text[start_pos: start_pos + 50]
#     value_match = value_pattern.search(window_forward)
    
#     # If not found, search backward (100 characters before start_pos)
#     if not value_match:
#             print("Forward search failed. Searching backward within a window of 100 characters.")
#             start_backward = max(0, start_pos - 100)
#             window_backward = extracted_text[start_backward: start_pos]
#             # Find all numeric matches in the backward window:
#             backward_matches = list(value_pattern.finditer(window_backward))
#             if backward_matches:
#                 # Choose the last match (closest to the property)
#                 value_match = backward_matches[-1]
#                 print(f"Backward window text: {window_backward}")
#                 print(f"Selected backward match: {value_match.group()}")
    
#     if value_match:
#         extracted_value = value_match.group()
#         if len(extracted_value) == 1:
#             extracted_value = None
#     return extracted_text, extracted_value
def process_image_file(image_path, selected_prop, regex, prompt):
    """
    Crop the image to its upper left quadrant, run PaddleOCR to extract text,
    then try to extract a numeric value based on the given prompt, selected property, and regex.
    Returns (extracted_text, extracted_value, status).
    """
    cropped_image = crop_upper_left(image_path)
    
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, image_orientation=True)
    result = ocr.ocr(cropped_image, cls=True)
    # print(f"OCR result for {os.path.basename(image_path)}: {result}")
    
    if not result:
        extracted_text = ""
    else:
        extracted_text = ""
        for line in result:
            if line is None:
                continue
            for word in line:
                if word is None or len(word) < 2:
                    continue
                text, confidence = word[1]
                if confidence >= 0.70:
                    extracted_text += str(text) + " "
    extracted_text = extracted_text.strip()
    
    # Remove tokens that are mis-detections for ranges.
    filtered_tokens = []
    for token in extracted_text.split():
        lower_token = token.lower()
        if (lower_token.startswith("range") or lower_token.startswith("rang") or
            lower_token.startswith("rag") or lower_token.startswith("fange")):
            continue
        filtered_tokens.append(token)
    extracted_text = " ".join(filtered_tokens).strip()
    
    print(f"Processed {os.path.basename(image_path)} - Extracted Text: {extracted_text}")
    
    extracted_value = None
    status = "running"
    
    if not extracted_text:
        if has_red_color(image_path):
            extracted_text = "machine is On"
            status = "on"
        else:
            extracted_text = "machine is off"
            status = "off"
    elif extracted_text == "0":
        extracted_text = "machine is On"
        status = "on"
    else:
        generalized_prop = re.sub(r'[_\s]', r'[\\s_]*', selected_prop, flags=re.IGNORECASE)
        prop_pattern = re.compile(generalized_prop, re.IGNORECASE)
        prop_match = prop_pattern.search(extracted_text)
        if prop_match:
            start_pos = prop_match.end()
            value_pattern = re.compile(regex)
            window_forward = extracted_text[start_pos: start_pos + 50]
            value_match = value_pattern.search(window_forward)
            if not value_match:
                print("Forward search failed. Searching backward within a window of 100 characters.")
                start_backward = max(0, start_pos - 100)
                window_backward = extracted_text[start_backward: start_pos]
                backward_matches = list(value_pattern.finditer(window_backward))
                if backward_matches:
                    value_match = backward_matches[-1]
                    print(f"Backward window text: {window_backward}")
                    print(f"Selected backward match: {value_match.group()}")
            if value_match:
                extracted_value = value_match.group()
                if len(extracted_value) == 1:
                    extracted_value = None

    return extracted_text, extracted_value, status


def extract_filename(filepath):
    return os.path.basename(filepath)

def is_valid_image_file(filepath):
    valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    return any(filepath.lower().endswith(ext) for ext in valid_extensions)

def process_images(image_paths, selected_prop, regex, prompt):
    delayed_results = [delayed(process_image_file)(image_path, selected_prop, regex, prompt)
                       for image_path in image_paths]
    results = compute(*delayed_results)
    return results




def main():
    # Record the start time of the whole execution frame
    t_start = time.time()

    # Initialize Dask client
    # client = Client(heartbeat_interval="10s", timeout="30s")
    client = Client()

    # Folder containing images to process
    input_folder = r"D:\Work\field-app\1main\paddle\Paddleocr-search\pics_correct"  # Change this to your images folder
    # Output CSV file for OCR results
    output_csv = "ocr_results.csv"
    output_debug_csv = "ocr_debug_results.csv"
    
    # Define parameters for extraction
    selected_prop = "set speed"
    regex = r"\b\d+\.?\d*\b"
    prompt = "other"  # Use "digital_no" if you want to extract the first number
    
    # List of image files to process
    image_files = [os.path.join(input_folder, file)
                   for file in os.listdir(input_folder) if is_valid_image_file(file)]

    # Process images in parallel (each image file is processed as a separate task)
    results = process_images(image_files, selected_prop, regex, prompt)
    #  Write results to CSV
    with open(output_debug_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "extracted_text", "extracted_value"])
        for file, (extracted_text, extracted_value, _) in zip(image_files, results):
            writer.writerow([extract_filename(file), extracted_text, extracted_value])
            print(f"Written results for {file}")

    # Write results to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "extracted_value", "properties", "status"])
        for file, (extracted_text, extracted_value, status) in zip(image_files, results):
            # Replace spaces with underscores for the key
            prop_key = selected_prop.replace(" ", "_")
            prop_dict = {prop_key: extracted_value}
            writer.writerow([extract_filename(file), extracted_value, str(prop_dict), status])
            print(f"Written results for {file}")
    
    # Record end time and print total execution time
    t_end = time.time()
    total_time = t_end - t_start
    print(f"Total execution time: {total_time:.2f} seconds")
    
    # Note: For per-line timing, consider using a profiler such as 'line_profiler'.

if __name__ == "__main__":
    main()


# def main():
#     # Record the start time of the whole execution frame
#     t_start = time.time()


#     # Initialize Dask client
#     client = Client()

#     # Folder containing images to process
#     input_folder = r"D:\Work\field-app\1main\paddle\dask-ocr-project\pics_correct"  # Change this to your images folder
#     # Output CSV file for OCR results
#     output_csv = "ocr_results.csv"
    
#     # Define parameters for extraction
#     selected_prop = "set speed"
#     regex = r"\b\d+\.?\d*\b"
#     prompt = "other"  # Use "digital_no" if you want to extract the first number
    
#     # List of image files to process
#     image_files = [os.path.join(input_folder, file)
#                    for file in os.listdir(input_folder) if is_valid_image_file(file)]

#     # Process images in parallel (each image file is processed as a separate task)
#     results = process_images(image_files, selected_prop, regex, prompt)
#     '''
#     Use this to debug the extracted text and value for each image:
#     '''
#     # Write results to CSV
#     # with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
#     #     writer = csv.writer(csvfile)
#     #     writer.writerow(["filename", "extracted_text", "extracted_value"])
#     #     for file, (extracted_text, extracted_value) in zip(image_files, results):
#     #         writer.writerow([extract_filename(file), extracted_text, extracted_value])
#     #         print(f"Written results for {file}")
#     # Write results to CSV

#     '''
#     use this to get the result only no debugging 
#     '''
# # Write results to CSV
#     with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(["filename", "extracted_value", "properties"])
#         for file, (extracted_text, extracted_value) in zip(image_files, results):
#             # Replace spaces with underscores for the key
#             prop_key = selected_prop.replace(" ", "_")
#             prop_dict = {prop_key: extracted_value}
#             writer.writerow([extract_filename(file), extracted_value, str(prop_dict)])
#             print(f"Written results for {file}")
#     # Record end time and print total execution time
#     t_end = time.time()
#     total_time = t_end - t_start
#     print(f"Total execution time: {total_time:.2f} seconds")
    
#     # Note: For per-line timing, consider using a profiler such as 'line_profiler'.

# if __name__ == "__main__":
#     main()