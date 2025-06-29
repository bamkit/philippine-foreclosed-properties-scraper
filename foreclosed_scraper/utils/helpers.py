import os

def find_available_filename(directory, filename):
    """
    Returns an available filename in the given directory. If the filename exists,
    appends a number before the file extension (e.g., file_1.txt).
    """
    base, ext = os.path.splitext(filename)
    candidate = filename
    counter = 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{base}_{counter}{ext}"
        counter += 1
    return candidate 