import os
import subprocess
import sys
import time
from io import BytesIO

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, PictureType, ID3NoHeaderError 
from PIL import Image


def scan_dir(dir, ext):
    subfolders = []
    files = []
    processed = {}

    with os.scandir(dir) as f:
        for entry in f:
            dir_path = os.path.dirname(entry.path)
            file_ext = os.path.splitext(entry.name)[1].lower()

            is_allowed_filetype = file_ext in ext
            subfolder_has_cover = entry.is_dir() and has_cover(entry.path)
            newly_processed_subfolder = entry.is_file() and dir_path in processed
            if subfolder_has_cover or newly_processed_subfolder:
                continue
            elif entry.is_dir():
                subfolders.append(entry.path)
            elif entry.is_file() and is_allowed_filetype:
                is_processed = process_file(entry)
                processed[dir_path] = is_processed
                if is_processed:
                    files.append(entry.path)

    # Process subfolders
    for dir in list(subfolders):
        nested_folders, nested_files = scan_dir(dir, ext)
        subfolders.extend(nested_folders)
        files.extend(nested_files)

    return subfolders, files

def process_file(entry):
    file_ext = os.path.splitext(entry.name)[1].lower()
    is_mp3 = file_ext == '.mp3'
    if is_mp3:
        extract_jpg(entry)
        return True
    return False

def has_cover(dir):
    with os.scandir(dir) as f:
        for entry in f:
            if entry.is_file() and entry.name == "cover.jpg":
                return True
    return False

def extract_jpg(entry):
    try:
        tag = ID3(entry.path)
        for tag_key in tag.keys():
            if not tag_key.startswith('APIC'):
                continue
            apic_frame = tag[tag_key]
            if apic_frame.mime != 'image/jpeg':
                print("No JPEG image found", entry.path)
                continue
            image_data = apic_frame.data
            image = Image.open(BytesIO(image_data))
            if image.width > 500 or image.height > 500:
                image = image.resize((500, 500))
            path =  dir_path = os.path.dirname(entry.path) + '/cover.jpg'
            image.save(path, 'JPEG')
    except ID3NoHeaderError:
        print("Error fetching ID3 tag", entry.path)
        return


if len(sys.argv) > 1:
    start = time.time()
    print("scanning directory", sys.argv[1])
    subfolders, files = scan_dir(sys.argv[1], [".mp3"])
    end = time.time()
    print(f"Processed {len(files)} covers over {len(subfolders)} subfolders in {end-start} seconds.")
else:
    print("You must provide a path between quotes. For example: python fix_albumart.py \"R:\\My Music\"")