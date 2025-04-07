import os
import re

# Define the source folders
folders = {
    'mosaic_images': '../Figures/Mosaicked_Image/',
    'single_images': '../Figures/Single_Date_Image/'
}

# Create the available_dates folder and its subfolders if they don't exist
output_folder = '../Available_Dates/'
os.makedirs(os.path.join(output_folder, 'mosaic_images'), exist_ok=True)
os.makedirs(os.path.join(output_folder, 'single_images'), exist_ok=True)

patterns = {
    'mosaic_images': re.compile(r'SWOT_Mosaicked_(\d{8})'),
    'single_images': re.compile(r'SWOT_(\d{8})')
}

# Loop over the folders and extract dates for each subfolder
for subfolder_name, folder_path in folders.items():
    dates = set()

    # Check if the folder exists
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            match = patterns[subfolder_name].search(filename)  # Use the correct pattern for the folder
            if match:
                dates.add(match.group(1))

    # Sort the dates to ensure consistency
    sorted_dates = sorted(dates)

    # Define the output file path
    output_file = os.path.join(output_folder, subfolder_name, 'available_dates.txt')

    # Write the dates to available_dates.txt in the corresponding subfolder
    with open(output_file, 'w') as file:
        for date in sorted_dates:
            file.write(f"{date}\n")

    # print(f"Available dates for {subfolder_name} have been saved to {output_file}.")