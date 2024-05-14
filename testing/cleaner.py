import os
import csv

# Function to delete files from a folder based on a list of filenames


def delete_files(folder, filenames):
    for filename in filenames:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")


# Paths to the folders
test_images_folder = "./test_images"
results_folder = "./results"
plates_folder = "./plates"

# Path to the CSV file
csv_file_path = "./results/predictions.csv"

# Lists to store filenames of files to delete
files_to_delete_images = []
files_to_delete_results = []
files_to_delete_plates = []

# Read the CSV file
with open(csv_file_path, "r") as csvfile:
    csv_reader = csv.reader(csvfile)
    next(csv_reader)  # Skip the header row
    for row in csv_reader:
        if row[-1] == "False":  # Check if the last column indicates FALSE
            filename = row[0].strip()
            print("Extracted filename:", filename)  # Print extracted filename
            files_to_delete_images.append(os.path.basename(
                filename))  # Extract just the filename
            files_to_delete_plates.append(os.path.basename(filename))
            # Add "roi_" prefix to filename for results folder
            files_to_delete_results.append("roi_" + os.path.basename(filename))

# Print the list of files to delete
print("Files to delete from test_images folder:", files_to_delete_images)
print("Files to delete from plates folder:", files_to_delete_plates)
print("Files to delete from results folder:", files_to_delete_results)

# Delete images from test_images folder
delete_files(test_images_folder, files_to_delete_images)
print("Deletion from test_images folder completed.")

# Delete images from plates folder
delete_files(plates_folder, files_to_delete_plates)
print("Deletion from plates folder completed.")

# Delete images from results folder
delete_files(results_folder, files_to_delete_results)
print("Deletion from results folder completed.")
