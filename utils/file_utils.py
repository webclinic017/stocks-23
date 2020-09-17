import os 
import logging

def deleteFile(file_type, file_dir):
    logging.info(f"Delete files of type \"{file_type}\" in {file_dir}")
    directory = file_dir
    files = os.listdir(directory)
    filtered_files = [file for file in files if file.endswith(file_type)]
    for file in filtered_files:
        file_path = os.path.join(directory, file)
        os.remove(file_path)
