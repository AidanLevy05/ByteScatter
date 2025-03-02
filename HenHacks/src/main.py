import os
import base64
import json
import sqlite3
from io import BytesIO
import argparse
import sys
from math import ceil
import shutil
import mimetypes
import uuid
import time
import io
import pyfiglet
from gui import introMenu
from encryption import KeyManager, SegmentEncryptor
from dropbox_helper import download_and_delete_file, list_files, upload_file

# Settings file path
SETTINGS_FILE = "settings.json"

# Database for encryption keys
DB_PATH = "keys.db"
key_manager = KeyManager(DB_PATH)
segment_encryptor = SegmentEncryptor(DB_PATH)

def introMenu():
    text = pyfiglet.figlet_format("Byte Scatter", justify="center")
    print(text)

# Ensure the output directory exists
def ensure_output_dir():
    if not os.path.exists("output"):
        os.makedirs("output")

#
#   Loads settings from JSON file or prompts the user to enter them if missing
#
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as file:
                settings = json.load(file)
                return settings
        except json.JSONDecodeError:
            print("Error: Corrupt settings.json. Resetting settings.")
    return setup_settings()

#
#   Prompts user for API keys and saves them
#
def setup_settings():
    print("\n[Setup] Enter your API keys and login details.")
    settings = {
        "GoogleDrive": input("Enter Google Drive API Key: ").strip(),
        "Dropbox": input("Enter Dropbox API Key: ").strip(),
        "OneDrive": input("Enter OneDrive API Key: ").strip()
    }

    save_settings(settings)
    print("\n Settings saved successfully!")
    return settings

#
#   Saves settings to JSON file
#
def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

#
#   Detect what file type - using mimetypes instead of magic
#
def detect_file_type(filepath):
    # Use mimetypes module instead of magic for better compatibility
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
        # If mimetype can't be determined, check if it's text by trying to read it
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read a bit of the file
                return "text/plain"  # If no error, it's probably text
        except UnicodeDecodeError:
            return "application/octet-stream"  # It's binary
    return mime_type

#
#   Reads a file in binary mode and returns its raw data
#
def read_file_raw(filepath):
    try:    
        with open(filepath, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except PermissionError:
        print(f"Error: Permission denied for '{filepath}'.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

#
#   Gets file line count or size for binary files
#
def get_file_info(file_path):
    file_type = detect_file_type(file_path)
    
    if file_type and "text" in file_type: 
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return {"type": "text", "lines": len(f.readlines()), "size": os.path.getsize(file_path)}
        except Exception as e:
            print(f"Error reading text file: {e}")
            # Fallback to binary handling
    
    # For binary or if text file reading failed
    try:
        return {"type": "binary", "size": os.path.getsize(file_path)}
    except Exception as e:
        print(f"Error getting file size: {e}")
        return None

#
#   Splits a text file into chunks based on line count
#
def split_text_file(filename, input_file, num_files, num_lines):
    ensure_output_dir()
    
    # create size for each new file
    size_of_new_file = ceil(num_lines / num_files)
    splits = []

    temp_dir = os.path.join("output", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for file_num in range(num_files):
        # create new file name, which is appended with the current file number
        new_output_file = os.path.join(temp_dir, f"split_{file_num}_{filename}")

        # define start and end line number
        start_line = file_num * size_of_new_file
        end_line = ((file_num + 1) * size_of_new_file) - 1

        print(f"File #{file_num} | Start: {start_line} | End: {end_line}")

        # open new output file for writing
        with open(new_output_file, "w") as o:
            with open(input_file, "r", encoding='utf-8', errors='ignore') as i:
                for line_num, line in enumerate(i, start=0):
                    # Write lines within the specified range
                    if start_line <= line_num <= end_line:
                        o.write(line)

        # Append the output file path to the list of splits
        splits.append(new_output_file)

    return splits

#
#   Split binary file into chunks
#
def split_binary_file(file_path, num_splits):
    """ Splits a binary file into multiple parts and returns a list of chunked filenames. """
    ensure_output_dir()
    
    temp_dir = os.path.join("output", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    file_size = os.path.getsize(file_path)
    chunk_size = ceil(file_size / num_splits)
    file_name = os.path.basename(file_path)

    splits = []
    with open(file_path, "rb") as f:
        for i in range(num_splits):
            chunk_data = f.read(chunk_size)  # Read a chunk of bytes
            if not chunk_data:
                break  # Stop if there's no more data to read

            chunk_filename = os.path.join(temp_dir, f"split_{i}_{file_name}")
            with open(chunk_filename, "wb") as chunk_file:
                chunk_file.write(chunk_data)  # Write chunk to new file

            splits.append(chunk_filename)

    return splits

#
#   Encrypt a file segment and save metadata with clear file ID association
#
def encrypt_segment(segment_path, file_id, master_key, segment_index):
    """
    Encrypts a file segment using the SegmentEncryptor.
    
    Args:
        segment_path (str): Path to the segment file
        file_id (str): Unique ID for the original file
        master_key (bytes): The master encryption key
        segment_index (int): Index of this segment in the original file
        
    Returns:
        tuple: (encrypted_file_path, metadata_path)
    """
    # Read the segment data
    segment_data = read_file_raw(segment_path)
    if segment_data is None:
        print(f"Error: Could not read segment {segment_path}")
        return None, None

    # Print the first few bytes to verify we're reading binary data
    print(f"Debug: First 20 bytes of segment data: {segment_data[:20]}")

    # Encrypt the segment using our encryption module
    try:
        ciphertext, metadata, serialized_metadata = segment_encryptor.encrypt_file_segment(
            file_id, master_key, segment_data, segment_index
        )
        
        # Print the first few bytes of ciphertext to verify encryption worked
        print(f"Debug: First 20 bytes of encrypted data: {ciphertext[:20]}")
        
        # Check if ciphertext actually differs from input
        if ciphertext == segment_data:
            print("WARNING: Encryption did not change the data! This is a security risk.")
            
    except Exception as e:
        print(f"Encryption error: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    # Rename the segment files to include the file_id for easier matching
    file_base = os.path.basename(segment_path)
    encrypted_path = os.path.join("output", f"{file_id[:8]}_{file_base}_{segment_index}.enc")
    
    # Save encrypted data to file
    with open(encrypted_path, "wb") as f:
        f.write(ciphertext)
    
    # Save metadata to file alongside the encrypted segment
    metadata_path = encrypted_path.replace(".enc", ".meta")
    with open(metadata_path, "w") as f:
        f.write(serialized_metadata)
    
    print(f"Encrypted: {segment_path} -> {encrypted_path}")
    return encrypted_path, metadata_path

#
#   Decrypts a file segment using stored metadata
#
def decrypt_segment(encrypted_path, metadata_path, password=None, master_key=None):
    """
    Decrypts a file segment using the SegmentEncryptor.
    
    Args:
        encrypted_path (str): Path to the encrypted segment file
        metadata_path (str): Path to the metadata file
        password (str, optional): Password for decryption
        master_key (bytes, optional): Master key for decryption
        
    Returns:
        str: Path to the decrypted segment file
    """
    # Read the encrypted data and metadata
    encrypted_data = read_file_raw(encrypted_path)
    if encrypted_data is None:
        print(f"Error: Could not read encrypted file {encrypted_path}")
        return None
    
    try:
        with open(metadata_path, "r") as f:
            serialized_metadata = f.read()
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        return None
    
    # Decrypt the segment using our encryption module
    try:
        decrypted_data = segment_encryptor.decrypt_file_segment(
            encrypted_data, serialized_metadata, password=password, master_key=master_key
        )
    except ValueError as e:
        print(f"Decryption error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during decryption: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Save decrypted data to file - create a decrypted path based on the encrypted path
    # For the new naming format (fileid_originalname_segmentindex.enc)
    basename = os.path.basename(encrypted_path)
    # Remove the file ID prefix and keep only the original part
    if '_' in basename:
        original_part = '_'.join(basename.split('_')[1:])
    else:
        original_part = basename
        
    # Create decrypted path
    decrypted_path = os.path.join(os.path.dirname(encrypted_path), f"dec_{original_part.replace('.enc', '')}")
    
    try:
        with open(decrypted_path, "wb") as f:
            f.write(decrypted_data)
        
        print(f"Decrypted: {encrypted_path} -> {decrypted_path}")
        return decrypted_path
    except Exception as e:
        print(f"Error writing decrypted file: {e}")
        return None

#
#   Process of encrypting all segments of a file
#
def encrypt_file_segments(segments, file_password, original_filename, upload_to_cloud=False):
    """
    Encrypts all segments of a file and returns data needed for later decryption.
    
    Args:
        segments (list): List of segment file paths
        file_password (str): Password for encryption
        original_filename (str): Original file name for metadata
        upload_to_cloud (bool): Whether to upload segments to cloud services
        
    Returns:
        tuple: (file_id, encrypted_segments, master_key)
    """
    # Set up encryption for the file (generate file_id and master key)
    file_id, master_key = segment_encryptor.setup_encryption(file_password)
    print(f"Created encryption profile for file with ID: {file_id}")
    
    # Store additional metadata about the original file in the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create master_files table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS master_files (
        file_id TEXT PRIMARY KEY,
        original_filename TEXT NOT NULL,
        segment_count INTEGER NOT NULL,
        creation_date TEXT NOT NULL
    )
    ''')
    
    # Create table for cloud storage locations if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS segment_cloud_locations (
        segment_id TEXT PRIMARY KEY,
        cloud_service TEXT NOT NULL,
        remote_id TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        FOREIGN KEY (segment_id) REFERENCES segment_keys_info(segment_id)
    )
    ''')
    
    # Insert file info
    cursor.execute(
        "INSERT INTO master_files (file_id, original_filename, segment_count, creation_date) VALUES (?, ?, ?, datetime('now'))",
        (file_id, original_filename, len(segments))
    )
    conn.commit()
    conn.close()
    
    # Initialize cloud services if needed
    cloud_services = []
    if upload_to_cloud:
        settings = load_settings()
        if settings["GoogleDrive"] != "000":
            cloud_services.append(GoogleDriveConnector(settings["GoogleDrive"]))
        if settings["Dropbox"] != "000":
            cloud_services.append(DropboxConnector(settings["Dropbox"]))
        if settings["OneDrive"] != "000":
            cloud_services.append(OneDriveConnector(settings["OneDrive"]))
    
    encrypted_segments = []
    
    # Encrypt each segment
    for idx, segment_path in enumerate(segments):
        # Ensure the output directory exists
        if not os.path.exists("output"):
            os.makedirs("output")
            
        encrypted_path, metadata_path = encrypt_segment(segment_path, file_id, master_key, idx)
        
        segment_info = {
            "encrypted_path": encrypted_path,
            "metadata_path": metadata_path,
            "segment_index": idx,
            "cloud_locations": []
        }
        
        # Upload to cloud if requested
        if upload_to_cloud and cloud_services and encrypted_path:
            # Get the encrypted data
            with open(encrypted_path, "rb") as f:
                encrypted_data = f.read()
            
            # Choose a cloud service (round-robin)
            service = cloud_services[idx % len(cloud_services)]
            
            # Generate a remote path
            remote_path = f"{file_id}_{idx}.enc"
            
            # Upload the segment
            print(f"Uploading segment {idx} to {service.service_name}...")
            remote_id = service.upload_segment(encrypted_data, remote_path)
            
            if remote_id:
                # Store cloud location in database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Generate segment_id that matches what's in segment_keys_info
                segment_id = f"{file_id}_{idx}"
                
                cursor.execute(
                    """
                    INSERT INTO segment_cloud_locations (
                        segment_id, cloud_service, remote_id, upload_date
                    ) VALUES (?, ?, ?, datetime('now'))
                    """, 
                    (segment_id, service.service_name, remote_id)
                )
                
                conn.commit()
                conn.close()
                
                # Add to the segment info
                segment_info["cloud_locations"].append({
                    "service": service.service_name,
                    "remote_id": remote_id
                })
                
                print(f"Segment {idx} uploaded to {service.service_name} successfully.")
        
        if encrypted_path:
            encrypted_segments.append(segment_info)
            # Verify the encrypted file exists
            if not os.path.exists(encrypted_path):
                print(f"WARNING: Expected encrypted file {encrypted_path} was not created!")
            if not os.path.exists(metadata_path):
                print(f"WARNING: Expected metadata file {metadata_path} was not created!")
    
    print(f"All {len(encrypted_segments)} segments encrypted successfully")
    
    # Verify encryption by checking if content is actually encrypted
    if encrypted_segments:
        with open(encrypted_segments[0]["encrypted_path"], "rb") as f:
            sample = f.read(100)  # Read first 100 bytes
            try:
                # If this decodes as valid UTF-8 text without errors, it might not be encrypted
                sample.decode('utf-8')
                if sample.decode('utf-8').isprintable():
                    print("WARNING: Encrypted files may not be properly encrypted! Check implementation.")
            except UnicodeDecodeError:
                # This is expected for properly encrypted data
                print("Encryption verified: Files contain non-plaintext data.")
    
    # Clean up temporary segment files
    for segment_path in segments:
        if os.path.exists(segment_path):
            try:
                os.remove(segment_path)
            except Exception as e:
                print(f"Warning: Could not remove temporary segment file {segment_path}: {e}")
    
    # Also try to remove the temp directory if it's empty
    temp_dir = os.path.join("output", "temp")
    if os.path.exists(temp_dir):
        try:
            os.rmdir(temp_dir)
        except:
            pass  # Ignore if directory is not empty or can't be removed
    
    return file_id, encrypted_segments, master_key

#
#   Get all segments for a file from the database
#
def get_file_segments(file_id):
    """
    Retrieves all segment information for a file from the database.
    
    Args:
        file_id (str): The file ID to look up
        
    Returns:
        list: List of segment info dictionaries sorted by index
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the file info
        cursor.execute("SELECT * FROM master_files WHERE file_id = ?", (file_id,))
        file_info = cursor.fetchone()
        
        if not file_info:
            print(f"No file found with ID: {file_id}")
            conn.close()
            return None, None
        
        # Get all segments for this file from the segment_keys_info table
        cursor.execute("""
            SELECT * FROM segment_keys_info 
            WHERE file_id = ? 
            ORDER BY segment_index
        """, (file_id,))
        
        segment_rows = cursor.fetchall()
        conn.close()
        
        if not segment_rows:
            print(f"No segments found for file ID: {file_id}")
            return None, file_info
        
        # Look for segment files using file_id as part of the filename
        output_dir = "output"
        segments = []
        
        # First try to find segments by their filename pattern with file_id
        file_id_prefix = file_id[:8]  # Use first 8 chars of file_id as prefix
        segment_count = int(file_info['segment_count']) if file_info and 'segment_count' in file_info else 0
        
        print(f"Looking for segments with prefix '{file_id_prefix}' for file ID: {file_id}")
        
        # Look for files with the file_id prefix
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.startswith(file_id_prefix) and filename.endswith(".enc"):
                    enc_path = os.path.join(output_dir, filename)
                    meta_path = enc_path.replace(".enc", ".meta")
                    
                    if os.path.exists(meta_path):
                        # Get the segment index from the filename
                        try:
                            # Extract segment index from filename
                            segment_index = int(filename.split("_")[-1].replace(".enc", ""))
                            
                            segments.append({
                                "encrypted_path": enc_path,
                                "metadata_path": meta_path,
                                "segment_index": segment_index
                            })
                            print(f"Found segment {segment_index} file: {filename}")
                        except (ValueError, IndexError):
                            print(f"Couldn't determine segment index from filename: {filename}")
        
        # If we found enough segments, return them
        if len(segments) == segment_count:
            print(f"Found all {segment_count} segments for file ID: {file_id}")
            segments.sort(key=lambda x: x["segment_index"])
            return segments, file_info
        
        # If not all segments were found, try reading metadata from all files
        if len(segments) < segment_count:
            print(f"Only found {len(segments)} out of {segment_count} segments. Trying metadata search...")
            
            # Clear the segments list to avoid duplicates
            segments = []
            
            for filename in os.listdir(output_dir):
                if filename.endswith(".meta"):
                    meta_path = os.path.join(output_dir, filename)
                    enc_path = meta_path.replace(".meta", ".enc")
                    
                    if os.path.exists(enc_path):
                        try:
                            with open(meta_path, "r") as f:
                                metadata = json.loads(f.read())
                                if metadata.get("file_id") == file_id:
                                    segment_index = metadata.get("segment_index", 0)
                                    segments.append({
                                        "encrypted_path": enc_path,
                                        "metadata_path": meta_path,
                                        "segment_index": segment_index
                                    })
                                    print(f"Found segment {segment_index} via metadata")
                        except Exception as e:
                            print(f"Error reading metadata from {meta_path}: {e}")
        
        # Sort by segment index to ensure correct order
        segments.sort(key=lambda x: x["segment_index"])
        
        if segments:
            print(f"Found {len(segments)} segments for file ID: {file_id}")
            return segments, file_info
        else:
            print(f"Could not find any segments for file ID: {file_id}")
            return None, file_info
    
    except Exception as e:
        print(f"Error retrieving segments: {e}")
        import traceback
        traceback.print_exc()
        return None, None

#
#   List all files in the database with deduplication
#
def list_encrypted_files():
    """
    Lists all files in the database with their details,
    combining duplicates into a single entry.
    
    Returns:
        list: List of file info dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_id, original_filename, segment_count, creation_date 
            FROM master_files 
            ORDER BY creation_date DESC
        """)
        
        all_files = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # If there are no files, return empty list
        if not all_files:
            return []
            
        # Create a map to group by original filename, keeping only the most recent
        filename_map = {}
        for file in all_files:
            filename = file['original_filename']
            if filename not in filename_map or file['creation_date'] > filename_map[filename]['creation_date']:
                filename_map[filename] = file
        
        # Convert map back to list, sorted by creation date
        unique_files = list(filename_map.values())
        unique_files.sort(key=lambda x: x['creation_date'], reverse=True)
        
        # Clean up the database - remove old duplicate entries
        # Be careful not to delete files that are still needed
        if len(unique_files) < len(all_files):
            print(f"Found {len(all_files) - len(unique_files)} duplicate files in database.")
            # In a real implementation, we might clean up old duplicates here
            
        return unique_files
    except Exception as e:
        print(f"Error listing files: {e}")
        return []
    
# 
#   Download all segments from dropbox
#
from dropbox_helper import list_files, download_and_delete_file

def download_all_segments_from_dropbox(file_id):
    """
    Pulls all encrypted segments and metadata files from Dropbox for a given file_id.
    """
    print(f"🔄 Attempting to download segments for File ID: {file_id} from Dropbox...")

    # Get list of all files currently in Dropbox
    dropbox_files = list_files()

    if not dropbox_files:
        print("❌ No files found in Dropbox.")
        return False

    # Use the first 8 characters of file_id as prefix (as seen in your filenames)
    file_id_prefix = file_id[:8]
    print(f"Looking for files with prefix: {file_id_prefix}")
    
    # Match files that contain the prefix in their name
    files_to_download = []
    for file in dropbox_files:
        if file_id_prefix in file.name and file.name.endswith('.enc'):
            files_to_download.append(file.name)
            print(f"Found matching file: {file.name}")
            
            # Also look for corresponding metadata file
            meta_filename = file.name.replace('.enc', '.meta')
            for meta_file in dropbox_files:
                if meta_file.name == meta_filename:
                    files_to_download.append(meta_filename)
                    print(f"Found matching metadata: {meta_filename}")

    if not files_to_download:
        print(f"❌ No matching segments found for File ID: {file_id}.")
        return False

    print(f"📥 Found {len(files_to_download)} files to download. Downloading...")

    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Download each file
    segment_files = []
    metadata_files = []
    for file_name in files_to_download:
        local_path = os.path.join(output_dir, file_name)
        print(f"⏳ Downloading {file_name}...")

        try:
            download_and_delete_file(file_name, local_path)
            
            # Confirm the file was successfully downloaded
            if os.path.exists(local_path):
                print(f"✅ Successfully downloaded {file_name}")
                
                # Track which files we downloaded
                if file_name.endswith('.enc'):
                    segment_files.append(local_path)
                elif file_name.endswith('.meta'):
                    metadata_files.append(local_path)
            else:
                print(f"❌ Failed to download {file_name}.")
        except Exception as e:
            print(f"❌ Error downloading {file_name}: {e}")

    # Verify we have the required files
    downloaded_enc_files = [f for f in os.listdir(output_dir) if f.endswith('.enc') and file_id_prefix in f]
    if downloaded_enc_files:
        print(f"✅ Successfully downloaded {len(downloaded_enc_files)} encrypted segments.")
        
        # Now update the database with the downloaded files
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for segment_file in segment_files:
            try:
                # Extract segment index from filename
                # Assuming filename format like: 9a015cee_split_0_henhacks.png_0.enc
                segment_index = int(os.path.basename(segment_file).split('_')[-1].replace('.enc', ''))
                segment_id = f"{file_id}_{segment_index}"
                
                # Check if this segment exists in segment_keys_info
                cursor.execute("SELECT 1 FROM segment_keys_info WHERE segment_id = ?", (segment_id,))
                if cursor.fetchone() is None:
                    # If not, create an entry
                    cursor.execute(
                        """
                        INSERT INTO segment_keys_info (
                            segment_id, file_id, segment_index
                        ) VALUES (?, ?, ?)
                        """,
                        (segment_id, file_id, segment_index)
                    )
                
                # Update the local path in the database
                print(f"🔄 Updating database to record downloaded segment {segment_index}")
            except Exception as e:
                print(f"⚠️ Warning: Could not update database for {segment_file}: {e}")
        
        conn.commit()
        conn.close()
        return True
    else:
        print("❌ Failed to download any encrypted segments.")
        return False

#   Process of decrypting all segments of a file
#
def decrypt_file_segments(file_id, password, output_path=None, download_from_cloud=True):
    """
    Decrypts all segments of a file and reassembles them.
    
    Args:
        file_id (str): ID of the file to decrypt
        password (str): Password for decryption
        output_path (str, optional): Path where to save the reassembled file
        download_from_cloud (bool): Whether to download segments from cloud if local not found
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get segments for this file
    segments_info, file_info = get_file_segments(file_id)

    #####
    # Add this at the beginning of the decrypt_file_segments function, right after getting segments_info
# This should be the very first check after getting segments_info

    if not segments_info and download_from_cloud:
        print(f"No local segments found for file ID: {file_id}")
        print(f"Attempting to download segments from Dropbox...")
        
        # Direct call to download from Dropbox
        download_success = download_all_segments_from_dropbox(file_id)
        
        if download_success:
            print("✅ Successfully downloaded segments from Dropbox. Retrying segment detection...")
            # Re-check for segments after download
            segments_info, file_info = get_file_segments(file_id)
            
            if segments_info:
                print(f"Found {len(segments_info)} segments after Dropbox download")
            else:
                print("⚠️ Still no segments found after Dropbox download. Check file naming or permissions.")
        else:
            print("❌ Failed to download segments from Dropbox")
    if not segments_info:
        if file_info:
            print(f"Found file info but no segments for file ID: {file_id}")
            
            # Try direct Dropbox download first if cloud download is enabled
            if download_from_cloud:
                print(f"Attempting to download segments from Dropbox for file ID: {file_id}")
                download_success = download_all_segments_from_dropbox(file_id)
                
                if download_success:
                    print("Successfully downloaded segments from Dropbox. Retrying segment detection...")
                    # Retry getting segments after Dropbox download
                    segments_info, file_info = get_file_segments(file_id)
                    if segments_info:
                        print(f"Found {len(segments_info)} segments after Dropbox download")
                    else:
                        print("Still no segments found after Dropbox download")
                else:
                    print("Failed to download segments from Dropbox")
            
            # If still no segments, try a direct search in the output directory as a fallback
            if not segments_info:
                output_dir = "output"
                if os.path.exists(output_dir):
                    print("Searching for segments in output directory...")
                    
                    # Create a list to hold found segments
                    segments = []
                    segment_pattern = file_id.split('-')[0]  # Use part of the file_id as a pattern
                    
                    # Look for any files that might be segments
                    for filename in os.listdir(output_dir):
                        if filename.endswith(".enc"):
                            enc_path = os.path.join(output_dir, filename)
                            meta_path = enc_path.replace(".enc", ".meta")
                            
                            if os.path.exists(meta_path):
                                # Try to read the metadata
                                try:
                                    with open(meta_path, "r") as f:
                                        metadata_str = f.read()
                                        metadata = json.loads(metadata_str)
                                        
                                        # If this segment belongs to our file_id or we don't have a good way to check
                                        if "file_id" in metadata and metadata["file_id"] == file_id:
                                            segment_index = metadata.get("segment_index", 0)
                                            segments.append({
                                                "encrypted_path": enc_path,
                                                "metadata_path": meta_path,
                                                "segment_index": segment_index
                                            })
                                            print(f"Found segment {segment_index} for file {file_id}")
                                except Exception as e:
                                    print(f"Error reading metadata from {meta_path}: {e}")
                    
                    if segments:
                        print(f"Found {len(segments)} segments directly from files")
                        segments_info = segments
                    else:
                        print("No segments found via direct file search")
        
        if not segments_info and download_from_cloud:
            # Try to check for cloud-stored segments
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if any segments exist in the cloud locations table
            cursor.execute("""
                SELECT s.segment_id, s.segment_index, c.cloud_service, c.remote_id
                FROM segment_keys_info s
                JOIN segment_cloud_locations c ON s.segment_id = c.segment_id
                WHERE s.file_id = ?
                ORDER BY s.segment_index
            """, (file_id,))
            
            cloud_segments = cursor.fetchall()
            conn.close()
            
            if cloud_segments:
                print(f"Found {len(cloud_segments)} segments in cloud storage.")
                # Will download them in the cloud download section below
                segments_info = [{"segment_index": s["segment_index"], 
                                 "cloud_service": s["cloud_service"],
                                 "remote_id": s["remote_id"],
                                 "segment_id": s["segment_id"]} for s in cloud_segments]
            else:
                print("No segments found in cloud storage.")
        
        if not segments_info:
            print(f"Could not find segments for file ID: {file_id}")
            return False
    
    # Initialize cloud services if needed
    cloud_services = {}
    if download_from_cloud:
        settings = load_settings()
        if settings["GoogleDrive"] != "000":
            cloud_services["GoogleDrive"] = GoogleDriveConnector(settings["GoogleDrive"])
        if settings["Dropbox"] != "000":
            cloud_services["Dropbox"] = DropboxConnector(settings["Dropbox"])
        if settings["OneDrive"] != "000":
            cloud_services["OneDrive"] = OneDriveConnector(settings["OneDrive"])
    
    # Set default output path if not specified
    if not output_path and file_info and 'original_filename' in file_info:
        output_path = f"restored_{file_info['original_filename']}"
    elif not output_path:
        output_path = f"restored_file_{file_id}"
    
    # Decrypt each segment
    decrypted_segments = []
    
    for segment_info in segments_info:
        try:
            segment_index = segment_info["segment_index"]
            # Check if local files exist
            if "encrypted_path" in segment_info and "metadata_path" in segment_info and \
               os.path.exists(segment_info["encrypted_path"]) and \
               os.path.exists(segment_info["metadata_path"]):
                # Decrypt from local file
                decrypted_path = decrypt_segment(
                    segment_info["encrypted_path"],
                    segment_info["metadata_path"],
                    password=password
                )
                if decrypted_path:
                    decrypted_segments.append((segment_index, decrypted_path))
                    continue  # Skip cloud download if local decrypt succeeded
            
            # If we reach here, either local files don't exist or decryption failed
            if download_from_cloud and cloud_services:
                # Get cloud locations for this segment
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Generate segment_id that matches what's in segment_keys_info
                segment_id = segment_info.get("segment_id", f"{file_id}_{segment_index}")
                
                # Try direct cloud info from segment_info if available
                if "cloud_service" in segment_info and "remote_id" in segment_info:
                    cloud_locations = [{
                        "cloud_service": segment_info["cloud_service"],
                        "remote_id": segment_info["remote_id"]
                    }]
                else:
                    # Otherwise query the database
                    cursor.execute(
                        "SELECT * FROM segment_cloud_locations WHERE segment_id = ?",
                        (segment_id,)
                    )
                    cloud_locations = cursor.fetchall()
                
                # Get metadata for this segment from database
                cursor.execute(
                    "SELECT * FROM segment_keys_info WHERE segment_id = ?",
                    (segment_id,)
                )
                db_segment_info = cursor.fetchone()
                
                conn.close()
                
                if cloud_locations:
                    # Try each cloud location
                    for location in cloud_locations:
                        service_name = location["cloud_service"]
                        remote_id = location["remote_id"]
                        
                        if service_name in cloud_services:
                            print(f"Downloading segment {segment_index} from {service_name}...")
                            service = cloud_services[service_name]
                            
                            # Download the segment
                            encrypted_data = service.download_segment(remote_id)
                            
                            if encrypted_data:
                                # Save to temporary file
                                temp_dir = os.path.join("output", "temp")
                                if not os.path.exists(temp_dir):
                                    os.makedirs(temp_dir)
                                    
                                temp_encrypted_path = os.path.join(temp_dir, f"temp_{segment_id}.enc")
                                with open(temp_encrypted_path, "wb") as f:
                                    f.write(encrypted_data)
                                
                                # Create temporary metadata file if needed
                                if not "metadata_path" in segment_info or not os.path.exists(segment_info["metadata_path"]):
                                    temp_metadata_path = temp_encrypted_path.replace(".enc", ".meta")
                                    if db_segment_info:
                                        # Generate minimal metadata for decryption
                                        metadata = {
                                            "segment_id": segment_id,
                                            "file_id": file_id,
                                            "segment_index": segment_index
                                            # Other fields will be retrieved from database during decryption
                                        }
                                        with open(temp_metadata_path, "w") as f:
                                            f.write(json.dumps(metadata))
                                    else:
                                        print(f"Cannot create metadata for segment {segment_index}")
                                        continue
                                else:
                                    temp_metadata_path = segment_info["metadata_path"]
                                
                                # Try to decrypt
                                decrypted_path = decrypt_segment(
                                    temp_encrypted_path,
                                    temp_metadata_path,
                                    password=password
                                )
                                
                                if decrypted_path:
                                    decrypted_segments.append((segment_index, decrypted_path))
                                    # Clean up temp files
                                    if temp_encrypted_path.startswith(os.path.join("output", "temp")):
                                        os.remove(temp_encrypted_path)
                                        if temp_metadata_path.startswith(os.path.join("output", "temp")):
                                            os.remove(temp_metadata_path)
                                    break  # Successfully downloaded and decrypted
                                else:
                                    # Clean up temp files on failure
                                    if temp_encrypted_path.startswith(os.path.join("output", "temp")):
                                        os.remove(temp_encrypted_path)
                                        if temp_metadata_path.startswith(os.path.join("output", "temp")):
                                            os.remove(temp_metadata_path)
                        
                if segment_index not in [idx for idx, _ in decrypted_segments]:
                    print(f"Failed to get segment {segment_index} from any source")
            else:
                print(f"Segment {segment_index} not found locally and cloud download disabled")
        except Exception as e:
            print(f"Error processing segment {segment_info['segment_index']}: {e}")
            import traceback
            traceback.print_exc()
    
    if not decrypted_segments:
        print("Failed to decrypt any segments. Check the password.")
        return False
    
    # Reassemble the file
    try:
        # Sort by segment index to ensure correct order
        decrypted_segments.sort(key=lambda x: x[0])
        
        with open(output_path, "wb") as output_file:
            for _, segment_path in decrypted_segments:
                with open(segment_path, "rb") as segment_file:
                    output_file.write(segment_file.read())
        
        print(f"File reassembled successfully: {output_path}")
        
        # Clean up decrypted segments
        for _, path in decrypted_segments:
            if os.path.exists(path):
                os.remove(path)
                
        return True
    except Exception as e:
        print(f"Error reassembling file: {e}")
        import traceback
        traceback.print_exc()
        return False
#
#   Delete encrypted file and all its segments
#
def delete_encrypted_file(file_id):
    """
    Delete all segments of an encrypted file and its database records.
    
    Args:
        file_id (str): ID of the file to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get segments for this file
    segments_info, file_info = get_file_segments(file_id)
    
    if not file_info:
        print(f"No file found with ID: {file_id}")
        return False
    
    deleted_count = 0
    
    # Delete segment files from disk if they exist
    if segments_info:
        for segment_info in segments_info:
            try:
                if os.path.exists(segment_info["encrypted_path"]):
                    os.remove(segment_info["encrypted_path"])
                    deleted_count += 1
                
                if os.path.exists(segment_info["metadata_path"]):
                    os.remove(segment_info["metadata_path"])
            except Exception as e:
                print(f"Error deleting segment {segment_info['segment_index']}: {e}")
    
    # Delete cloud-stored segments if possible
    try:
        # Initialize cloud services 
        settings = load_settings()
        cloud_services = {}
        if settings["GoogleDrive"] != "000":
            cloud_services["GoogleDrive"] = GoogleDriveConnector(settings["GoogleDrive"])
        if settings["Dropbox"] != "000":
            cloud_services["Dropbox"] = DropboxConnector(settings["Dropbox"])
        if settings["OneDrive"] != "000":
            cloud_services["OneDrive"] = OneDriveConnector(settings["OneDrive"])
        
        if cloud_services:
            # Get cloud segment info from database
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find all cloud segments for this file
            cursor.execute("""
                SELECT c.* 
                FROM segment_cloud_locations c
                JOIN segment_keys_info s ON c.segment_id = s.segment_id
                WHERE s.file_id = ?
            """, (file_id,))
            
            cloud_segments = cursor.fetchall()
            conn.close()
            
            # Delete each cloud segment
            cloud_deleted = 0
            for segment in cloud_segments:
                service_name = segment["cloud_service"]
                remote_id = segment["remote_id"]
                
                if service_name in cloud_services:
                    service = cloud_services[service_name]
                    if service.delete_segment(remote_id):
                        cloud_deleted += 1
                        print(f"Deleted segment from {service_name}")
            
            if cloud_deleted > 0:
                print(f"Deleted {cloud_deleted} segments from cloud storage")
    except Exception as e:
        print(f"Error deleting cloud segments: {e}")
    
    # Remove database records
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all segment IDs for this file
        cursor.execute("SELECT segment_id FROM segment_keys_info WHERE file_id = ?", (file_id,))
        segment_ids = [row[0] for row in cursor.fetchall()]
        
        # Delete cloud location records
        for segment_id in segment_ids:
            cursor.execute("DELETE FROM segment_cloud_locations WHERE segment_id = ?", (segment_id,))
        
        # Delete segment records
        cursor.execute("DELETE FROM segment_keys_info WHERE file_id = ?", (file_id,))
        
        # Delete master key record
        cursor.execute("DELETE FROM master_keys WHERE file_id = ?", (file_id,))
        
        # Delete file record
        cursor.execute("DELETE FROM master_files WHERE file_id = ?", (file_id,))
        
        conn.commit()
        conn.close()
        
        print(f"Deleted {deleted_count} segments and database records for file ID: {file_id}")
        return True
    except Exception as e:
        print(f"Error deleting database records: {e}")
        return False

#
#   Verify if a file can be reconstructed from available segments
#
def verify_file_availability(file_id):
    """
    Check if a file can be reconstructed (either from local or cloud)
    
    Args:
        file_id (str): ID of the file to check
        
    Returns:
        dict: Status of file segments
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get file info
        cursor.execute(
            "SELECT * FROM master_files WHERE file_id = ?",
            (file_id,)
        )
        file_info = cursor.fetchone()
        
        if not file_info:
            return {"status": "not_found", "message": "File not found in database"}
        
        # Get all segments
        cursor.execute(
            "SELECT * FROM segment_keys_info WHERE file_id = ? ORDER BY segment_index",
            (file_id,)
        )
        segments = cursor.fetchall()
        
        segment_status = []
        missing_segments = []
        
        for segment in segments:
            segment_id = segment["segment_id"]
            segment_index = segment["segment_index"]
            
            # Get expected file paths
            expected_enc_path = os.path.join("output", f"{file_id[:8]}_split_{segment_index}_{file_info['original_filename']}_{segment_index}.enc")
            local_available = os.path.exists(expected_enc_path)
            
            # Also check for any files matching the pattern with this segment index
            if not local_available:
                # Try the more general pattern match
                for filename in os.listdir("output"):
                    if filename.endswith(f"_{segment_index}.enc") and filename.startswith(file_id[:8]):
                        local_available = True
                        expected_enc_path = os.path.join("output", filename)
                        break
            
            # Check cloud locations
            cursor.execute(
                "SELECT * FROM segment_cloud_locations WHERE segment_id = ?",
                (segment_id,)
            )
            cloud_locs = cursor.fetchall()
            
            segment_info = {
                "segment_index": segment_index,
                "local_available": local_available,
                "local_path": expected_enc_path if local_available else None,
                "cloud_available": len(cloud_locs) > 0,
                "cloud_services": [loc["cloud_service"] for loc in cloud_locs]
            }
            
            if not local_available and len(cloud_locs) == 0:
                missing_segments.append(segment_index)
            
            segment_status.append(segment_info)
        
        conn.close()
        
        if missing_segments:
            return {
                "status": "incomplete",
                "message": f"File is missing {len(missing_segments)} segments",
                "missing_segments": missing_segments,
                "segments": segment_status
            }
        else:
            return {
                "status": "available",
                "message": "All segments available (local or cloud)",
                "segments": segment_status
            }
    except Exception as e:
        print(f"Error verifying file availability: {e}")
        return {"status": "error", "message": str(e)}

#
#   Get locations for a specific segment
#
def get_segment_locations(segment_id):
    """
    Get all known locations (local and cloud) for a segment
    
    Args:
        segment_id (str): ID of the segment
        
    Returns:
        dict: Information about segment locations
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get local file info
        cursor.execute(
            "SELECT * FROM segment_keys_info WHERE segment_id = ?",
            (segment_id,)
        )
        segment_info = cursor.fetchone()
        
        # Get cloud locations
        cursor.execute(
            "SELECT * FROM segment_cloud_locations WHERE segment_id = ?",
            (segment_id,)
        )
        cloud_locations = cursor.fetchall()
        
        conn.close()
        
        if not segment_info:
            return None
        
        # Determine local file paths based on naming convention
        file_id = segment_info["file_id"]
        segment_index = segment_info["segment_index"]
        
        # Get file info for the original filename
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT original_filename FROM master_files WHERE file_id = ?", (file_id,))
        file_info = cursor.fetchone()
        conn.close()
        
        original_filename = file_info["original_filename"] if file_info else ""
        
        # Try to find the actual file
        expected_enc_path = None
        for filename in os.listdir("output"):
            if filename.endswith(f"_{segment_index}.enc") and filename.startswith(file_id[:8]):
                expected_enc_path = os.path.join("output", filename)
                expected_meta_path = expected_enc_path.replace(".enc", ".meta")
                break
        
        # If not found, use a default pattern
        if not expected_enc_path:
            expected_enc_path = os.path.join("output", f"{file_id[:8]}_split_{segment_index}_{original_filename}_{segment_index}.enc")
            expected_meta_path = expected_enc_path.replace(".enc", ".meta")
        
        # Check if local files exist
        local_exists = os.path.exists(expected_enc_path) and os.path.exists(expected_meta_path)
        
        # Compile result
        result = {
            "segment_id": segment_id,
            "file_id": file_id,
            "segment_index": segment_index,
            "local_available": local_exists,
            "local_path": expected_enc_path if local_exists else None,
            "metadata_path": expected_meta_path if local_exists else None,
            "cloud_locations": [dict(loc) for loc in cloud_locations]
        }
        
        return result
    except Exception as e:
        print(f"Error getting segment locations: {e}")
        return None

#
#   Test encryption/decryption functionality with a sample file
def test_encryption():
    """
    Tests the encryption and decryption process on a sample file.
    Creates a test file, splits it, encrypts all segments, decrypts them,
    and reassembles the original file.
    """
    print("\n=== Running Encryption/Decryption Test ===")
    
    # Create a test file
    test_file = "test_file.txt"
    test_content = "This is a test file.\n" * 1000  # Create some content
    with open(test_file, "w") as f:
        f.write(test_content)
    
    # Define test parameters
    num_splits = 5
    password = "testpassword123"
    
    print(f"Created test file: {test_file} with {len(test_content)} bytes")
    
    # Get file info
    file_info = get_file_info(test_file)
    
    # Split the file
    if file_info["type"] == "text":
        segments = split_text_file(test_file, test_file, num_splits, file_info["lines"])
    else:
        segments = split_binary_file(test_file, num_splits)
        
    print(f"Split file into {len(segments)} segments")
    
    # Encrypt all segments
    file_id, encrypted_segments, master_key = encrypt_file_segments(segments, password, test_file)
    print(f"Encrypted segments with file ID: {file_id}")
    
    # Use the actual encrypted files from the output
    print("Finding encrypted files...")
    segments_info = []
    
    # Get the actual paths from the encrypted_segments list
    for segment in encrypted_segments:
        if "encrypted_path" in segment and "metadata_path" in segment:
            encrypted_path = segment["encrypted_path"]
            metadata_path = segment["metadata_path"]
            segment_index = segment["segment_index"]
            
            if os.path.exists(encrypted_path) and os.path.exists(metadata_path):
                segments_info.append({
                    "encrypted_path": encrypted_path,
                    "metadata_path": metadata_path,
                    "segment_index": segment_index
                })
                print(f"Found segment {segment_index}: {encrypted_path}")
    
    if not segments_info:
        print("No encrypted segments found. Test failed.")
        return
    
    # Decrypt each segment
    decrypted_segments = []
    
    for segment_info in segments_info:
        decrypted_path = decrypt_segment(
            segment_info["encrypted_path"],
            segment_info["metadata_path"],
            password=password
        )
        if decrypted_path:
            decrypted_segments.append((segment_info["segment_index"], decrypted_path))
    
    # Sort by segment index to ensure correct order
    decrypted_segments.sort(key=lambda x: x[0])
    
    # Reassemble the file
    output_path = "test_file_reassembled.txt"
    success = False
    
    if decrypted_segments:
        try:
            with open(output_path, "wb") as output_file:
                for _, segment_path in decrypted_segments:
                    with open(segment_path, "rb") as segment_file:
                        output_file.write(segment_file.read())
            
            print(f"File reassembled successfully: {output_path}")
            success = True
            
            # Verify the content matches
            with open(output_path, "r") as f:
                reassembled_content = f.read()
            
            if reassembled_content == test_content:
                print("\nSUCCESS: Reassembled file content matches original!")
            else:
                print("\nFAILURE: Reassembled file content differs from original!")
                print(f"Original length: {len(test_content)}, Reassembled length: {len(reassembled_content)}")
        except Exception as e:
            print(f"Error reassembling file: {e}")
    else:
        print("Failed to decrypt any segments")
    
    # Clean up test files
    print("\nCleaning up test files...")
    if os.path.exists(test_file):
        os.remove(test_file)
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Clean up encrypted and decrypted files
    for segment_info in segments_info:
        if os.path.exists(segment_info["encrypted_path"]):
            try:
                os.remove(segment_info["encrypted_path"])
            except:
                pass
        if os.path.exists(segment_info["metadata_path"]):
            try:
                os.remove(segment_info["metadata_path"])
            except:
                pass
    
    # Clean up decrypted files
    for _, path in decrypted_segments:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    
    print("Test completed!")
#
#   Cloud Service Connection abstract class
#
class CloudServiceConnector:
    """Interface for cloud service operations"""
    
    def __init__(self, service_name, api_key):
        """Initialize with service name and API key/token"""
        self.service_name = service_name
        self.api_key = api_key
        
    def upload_segment(self, segment_data, remote_path):
        """
        Upload a segment to the cloud service
        
        Args:
            segment_data (bytes): Encrypted segment data
            remote_path (str): Path in cloud storage
            
        Returns:
            str: Remote identifier for the segment
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def download_segment(self, remote_id):
        """
        Download a segment from the cloud service
        
        Args:
            remote_id (str): Remote identifier for the segment
            
        Returns:
            bytes: Segment data
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def delete_segment(self, remote_id):
        """
        Delete a segment from the cloud service
        
        Args:
            remote_id (str): Remote identifier for the segment
            
        Returns:
            bool: True if successful
        """
        raise NotImplementedError("Subclasses must implement this method")

#
#   Google Drive implementation
#
class GoogleDriveConnector(CloudServiceConnector):
    def __init__(self, api_key):
        super().__init__("GoogleDrive", api_key)
        
    def upload_segment(self, segment_data, remote_path):
        try:
            # Actual implementation would use Google Drive API
            # For demonstration purposes, we'll simulate a successful upload
            print(f"Simulating upload to Google Drive: {remote_path}")
            # In a real implementation, you would:
            # 1. Use google-api-python-client to create a Drive service
            # 2. Create an upload request with the segment data
            # 3. Execute the request and return the file ID
            
            # Simulate a file ID
            file_id = f"gdrive_{uuid.uuid4().hex[:12]}"
            return file_id
        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")
            return None
    
    def download_segment(self, remote_id):
        try:
            # Actual implementation would use Google Drive API to download
            print(f"Simulating download from Google Drive: {remote_id}")
            # In a real implementation, you would:
            # 1. Use google-api-python-client to create a Drive service
            # 2. Get the file using the file ID (remote_id)
            # 3. Download the content and return it
            
            # For demo, return some placeholder data
            return b"This is simulated data from Google Drive"
        except Exception as e:
            print(f"Error downloading from Google Drive: {e}")
            return None
    
    def delete_segment(self, remote_id):
        try:
            # Actual implementation would use Google Drive API to delete
            print(f"Simulating deletion from Google Drive: {remote_id}")
            # In a real implementation, you would:
            # 1. Use google-api-python-client to create a Drive service
            # 2. Delete the file using the file ID (remote_id)
            
            return True
        except Exception as e:
            print(f"Error deleting from Google Drive: {e}")
            return False

#
#   Dropbox implementation
#
class DropboxConnector(CloudServiceConnector):
    def __init__(self, api_key):
        super().__init__("Dropbox", api_key)
        
    def upload_segment(self, segment_data, remote_path):
        try:
            # Actual implementation would use Dropbox API
            print(f"Simulating upload to Dropbox: {remote_path}")
            # In a real implementation, you would:
            # 1. Create a Dropbox client using the SDK
            # 2. Upload the file using files_upload method
            # 3. Return the path or ID
            
            # Simulate a path ID
            path_id = f"/bytescatter/{remote_path}"
            return path_id
        except Exception as e:
            print(f"Error uploading to Dropbox: {e}")
            return None
    
    def download_segment(self, remote_id):
        try:
            # Actual implementation would use Dropbox API to download
            print(f"Simulating download from Dropbox: {remote_id}")
            # In a real implementation, you would:
            # 1. Create a Dropbox client using the SDK
            # 2. Download the file using files_download method
            # 3. Return the content
            
            # For demo, return some placeholder data
            return b"This is simulated data from Dropbox"
        except Exception as e:
            print(f"Error downloading from Dropbox: {e}")
            return None
    
    def delete_segment(self, remote_id):
        try:
            # Actual implementation would use Dropbox API to delete
            print(f"Simulating deletion from Dropbox: {remote_id}")
            # In a real implementation, you would:
            # 1. Create a Dropbox client using the SDK
            # 2. Delete the file using files_delete method
            
            return True
        except Exception as e:
            print(f"Error deleting from Dropbox: {e}")
            return False

#
#   OneDrive implementation
#
class OneDriveConnector(CloudServiceConnector):
    def __init__(self, api_key):
        super().__init__("OneDrive", api_key)
        
    def upload_segment(self, segment_data, remote_path):
        try:
            # Actual implementation would use Microsoft Graph API
            print(f"Simulating upload to OneDrive: {remote_path}")
            # In a real implementation, you would:
            # 1. Create a Microsoft Graph client
            # 2. Create an upload session
            # 3. Upload the file in chunks
            # 4. Return the item ID
            
            # Simulate an item ID
            item_id = f"onedrive_{uuid.uuid4().hex[:12]}"
            return item_id
        except Exception as e:
            print(f"Error uploading to OneDrive: {e}")
            return None
    
    def download_segment(self, remote_id):
        try:
            # Actual implementation would use Microsoft Graph API to download
            print(f"Simulating download from OneDrive: {remote_id}")
            # In a real implementation, you would:
            # 1. Create a Microsoft Graph client
            # 2. Get the file content using the item ID
            # 3. Return the content
            
            # For demo, return some placeholder data
            return b"This is simulated data from OneDrive"
        except Exception as e:
            print(f"Error downloading from OneDrive: {e}")
            return None
    
    def delete_segment(self, remote_id):
        try:
            # Actual implementation would use Microsoft Graph API to delete
            print(f"Simulating deletion from OneDrive: {remote_id}")
            # In a real implementation, you would:
            # 1. Create a Microsoft Graph client
            # 2. Delete the item using the item ID
            
            return True
        except Exception as e:
            print(f"Error deleting from OneDrive: {e}")
            return False

#
#   Handles the file upload process (splitting, encrypting, etc.)
#

def upload(file_path, number_of_splits, file_pass, upload_to_cloud=False):
    """
    Handles the complete file upload process: splitting, encrypting, and preparing for upload.
    
    Args:
        file_path (str): Path to the original file
        number_of_splits (int): Number of segments to split into
        file_pass (str): Password for encryption
        upload_to_cloud (bool): Whether to upload to cloud services
    """
    print(f"Current working directory: {os.getcwd()}")

    # Try to handle both absolute and relative paths
    if not os.path.isabs(file_path):
        possible_paths = [
            file_path,
            os.path.join(os.getcwd(), file_path),
            os.path.abspath(file_path),
            os.path.join('..', file_path),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                print(f"Found file at: {file_path}")
                break
        else:
            print(f"Error: Could not find file at any of these locations:")
            for path in possible_paths:
                print(f"  - {path}")
            return None, None
    elif not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None, None

    ensure_output_dir()
    file_name = os.path.basename(file_path)

    file_info = get_file_info(file_path)
    if not file_info:
        print("Error: Could not analyze the file.")
        return None, None

    if file_info["type"] == "text":
        splits = split_text_file(file_name, file_path, number_of_splits, file_info["lines"])
        print(f"File split into {len(splits)} text parts.")
    else:
        splits = split_binary_file(file_path, number_of_splits)
        print(f"Binary file split into {len(splits)} parts.")

    # Encrypt segments
    file_id, encrypted_segments, master_key = encrypt_file_segments(
        splits, file_pass, file_name
    )

    
    if upload_to_cloud:
        print("\n📤 Uploading ALL encrypted segments to Dropbox...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for segment in encrypted_segments:
            segment_path = segment.get("encrypted_path") 
            segment_index = segment.get("segment_index")
            
            if not segment_path:
                print(f"❌ Error: Missing file path for segment: {segment}")
                continue
            
            if not os.path.exists(segment_path):
                print(f"❌ Error: Encrypted file not found: {segment_path}")
                continue
            
            # Upload the encrypted segment
            upload_result = upload_file(segment_path)
            
            if upload_result["success"]:
                # Add to database - IMPORTANT: This is what was missing
                segment_id = f"{file_id}_{segment_index}"
                
                # Check if the segment_id exists in segment_keys_info
                cursor.execute("SELECT 1 FROM segment_keys_info WHERE segment_id = ?", (segment_id,))
                if cursor.fetchone() is None:
                    print(f"⚠️ Warning: Segment ID {segment_id} not found in segment_keys_info table.")
                    # You might want to insert it here if missing
                
                # Delete any existing cloud location for this segment (to avoid duplicates)
                cursor.execute("DELETE FROM segment_cloud_locations WHERE segment_id = ?", (segment_id,))
                
                # Insert the new cloud location
                cursor.execute(
                    """
                    INSERT INTO segment_cloud_locations (
                        segment_id, cloud_service, remote_id, upload_date
                    ) VALUES (?, ?, ?, datetime('now'))
                    """, 
                    (segment_id, "Dropbox", upload_result["remote_path"])
                )
                
                conn.commit()
                print(f"✅ Recorded cloud location in database for segment {segment_index}.")
                print(f"✅ Uploaded encrypted segment: {segment_path} -> {upload_result['remote_path']}")

            # Upload metadata file if it exists
            meta_file = segment_path.replace(".enc", ".meta")
            if os.path.exists(meta_file):
                meta_upload_result = upload_file(meta_file)
                if meta_upload_result["success"]:
                    print(f"✅ Uploaded metadata: {meta_file} -> {meta_upload_result['remote_path']}")
        
        conn.close()
###


    print("\n=== Upload Summary ===")
    print(f"File ID: {file_id}")
    print(f"Number of segments: {len(encrypted_segments)}")
    print(f"Password required for decryption: {file_pass}")

    if upload_to_cloud:
        print("Encrypted segments uploaded to Dropbox.")
        verify_upload_to_dropbox(file_id)
    else:
        print("Encrypted segments stored locally.")

    return file_id, encrypted_segments

#
#   Validates user input to ensure it is a valid, non-negative integer
#
def get_valid_input(prompt, min_value=1):
    while True:
        try:
            value = int(input(prompt))
            if value < min_value:
                print(f"Error: Please enter a positive integer greater than or equal to {min_value}.")
                continue
            return value
        except ValueError:
            print("Error: Please enter a valid integer.")

###

def verify_upload_to_dropbox(file_id):
    """
    Verifies that all segments for a file have been properly uploaded to Dropbox
    and recorded in the database.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the file info
        cursor.execute("SELECT * FROM master_files WHERE file_id = ?", (file_id,))
        file_info = cursor.fetchone()
        
        if not file_info:
            print(f"❌ No file found with ID: {file_id}")
            conn.close()
            return False
            
        # Get all segments for this file
        cursor.execute("""
            SELECT * FROM segment_keys_info 
            WHERE file_id = ? 
            ORDER BY segment_index
        """, (file_id,))
        
        segments = cursor.fetchall()
        if not segments:
            print(f"❌ No segments found for file ID: {file_id}")
            conn.close()
            return False
            
        # Check for cloud locations
        segment_statuses = []
        for segment in segments:
            segment_id = segment["segment_id"]
            segment_index = segment["segment_index"]
            
            # Check for cloud location
            cursor.execute("""
                SELECT * FROM segment_cloud_locations
                WHERE segment_id = ?
            """, (segment_id,))
            
            cloud_location = cursor.fetchone()
            if cloud_location:
                print(f"✅ Segment {segment_index} has cloud location in {cloud_location['cloud_service']}")
                segment_statuses.append(True)
            else:
                print(f"❌ Segment {segment_index} has no cloud location recorded")
                segment_statuses.append(False)
        
        conn.close()
        
        # Return True only if all segments have cloud locations
        if all(segment_statuses):
            print(f"✅ All {len(segment_statuses)} segments have cloud locations recorded")
            return True
        else:
            print(f"❌ Only {sum(segment_statuses)} out of {len(segment_statuses)} segments have cloud locations")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying upload: {e}")
        return False
    
###
#
#   Displays the menu and handles user input
#
def menu():
    settings = load_settings()
    
    while True:
        print("\n=== ByteScatter Encryption Manager ===")
        print("1. View Settings")
        print("2. Update API Keys")
        print("3. Upload File (Local)")
        print("4. Upload File to Cloud")
        print("5. List Encrypted Files")
        print("6. Download File")
        print("7. Check File Availability")
        print("8. Delete Encrypted File")
        print("9. Run Encryption Test")
        print("10. Create Test File")
        print("11. List all files from dropbox")
        print("99. Exit")

        choice = input("Select an option >> ").strip()

        if choice == "1":
            print("\n Current Settings:")
            for key, value in settings.items():
                # Mask API keys for security
                masked_value = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else value
                print(f"{key}: {masked_value}")
                
        elif choice == "2":
            settings = setup_settings()  # Re-enter API keys
            
        elif choice == "3":
            file_path = input("Enter full/local file path >> ")
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                print(f"Current working directory: {os.getcwd()}")
                print("Try using either an absolute path (e.g., C:\\path\\to\\file.txt) or a path relative to this directory.")
                continue
                
            numSpl = get_valid_input("Enter number of segments >> ")
            file_pass = input("Enter password for file >> ")
            
            file_id, _ = upload(file_path, numSpl, file_pass)
            if file_id:
                print(f"File uploaded successfully with ID: {file_id}")
                print("Remember this ID or use option 5 to list your files later.")
                
        elif choice == "4":
            file_path = input("Enter full/local file path >> ")
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                print(f"Current working directory: {os.getcwd()}")
                print("Try using either an absolute path (e.g., C:\\path\\to\\file.txt) or a path relative to this directory.")
                continue
                
            numSpl = get_valid_input("Enter number of segments >> ")
            file_pass = input("Enter password for file >> ")
            
            file_id, _ = upload(file_path, numSpl, file_pass, upload_to_cloud=True)
            if file_id:
                print(f"File uploaded successfully with ID: {file_id}")
                print("Segments distributed across cloud services.")
                
        elif choice == "5":
            files = list_encrypted_files()
            if not files:
                print("No encrypted files found in the database.")
                continue
                
            print("\nYour Encrypted Files:")
            print("-" * 80)
            print(f"{'#':<3} {'File ID':<36} {'Original Filename':<30} {'Segments':<8} {'Created':<20}")
            print("-" * 80)
            
            for i, file in enumerate(files, 1):
                print(f"{i:<3} {file['file_id']:<36} {file['original_filename']:<30} {file['segment_count']:<8} {file['creation_date']:<20}")
                
        elif choice == "6":
            files = list_encrypted_files()
            if not files:
                print("No encrypted files found in the database.")
                continue
                
            print("\nSelect a file to download:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file['original_filename']} (File ID: {file['file_id'][:8]}...)")
                
            try:
                selection = get_valid_input("Enter file number >> ")
                if selection < 1 or selection > len(files):
                    print("Invalid selection.")
                    continue
                    
                selected_file = files[selection-1]
                file_id = selected_file['file_id']
                
                password = input("Enter password for decryption >> ")
                output_path = input(f"Enter output path (default: restored_{selected_file['original_filename']}) >> ")
                if not output_path:
                    output_path = f"restored_{selected_file['original_filename']}"
                
                cloud_download = input("Download from cloud if local segments not found? (y/n) >> ")
                download_from_cloud = cloud_download.lower() == 'y'
                
                success = decrypt_file_segments(file_id, password, output_path, download_from_cloud)
                if success:
                    print(f"File successfully restored to {output_path}")
                
            except ValueError:
                print("Please enter a valid number.")
                
        elif choice == "7":
            files = list_encrypted_files()
            if not files:
                print("No encrypted files found in the database.")
                continue
                
            print("\nSelect a file to check:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file['original_filename']} (File ID: {file['file_id'][:8]}...)")
                
            try:
                selection = get_valid_input("Enter file number >> ")
                if selection < 1 or selection > len(files):
                    print("Invalid selection.")
                    continue
                    
                selected_file = files[selection-1]
                file_id = selected_file['file_id']
                
                status = verify_file_availability(file_id)
                
                print(f"\nStatus for '{selected_file['original_filename']}':")
                print(f"Status: {status['status']}")
                print(f"Message: {status['message']}")
                
                if status['status'] == 'available':
                    print("\nSegment Locations:")
                    for segment in status['segments']:
                        locations = []
                        if segment['local_available']:
                            locations.append("Local")
                        if segment['cloud_available']:
                            locations.extend(segment['cloud_services'])
                            
                        print(f"  Segment {segment['segment_index']}: Available on {', '.join(locations)}")
                
                elif status['status'] == 'incomplete':
                    print("\nMissing segments:", ', '.join(str(idx) for idx in status['missing_segments']))
                    print("\nAvailable segments:")
                    for segment in status['segments']:
                        if segment['local_available'] or segment['cloud_available']:
                            locations = []
                            if segment['local_available']:
                                locations.append("Local")
                            if segment['cloud_available']:
                                locations.extend(segment['cloud_services'])
                                
                            print(f"  Segment {segment['segment_index']}: Available on {', '.join(locations)}")
            except ValueError:
                print("Please enter a valid number.")
                
        elif choice == "8":
            files = list_encrypted_files()
            if not files:
                print("No encrypted files found in the database.")
                continue
                
            print("\nSelect a file to delete:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file['original_filename']} (File ID: {file['file_id'][:8]}...)")
                
            try:
                selection = get_valid_input("Enter file number >> ")
                if selection < 1 or selection > len(files):
                    print("Invalid selection.")
                    continue
                    
                selected_file = files[selection-1]
                file_id = selected_file['file_id']
                
                confirm = input(f"Are you sure you want to delete '{selected_file['original_filename']}'? (y/n) >> ")
                if confirm.lower() == 'y':
                    success = delete_encrypted_file(file_id)
                    if success:
                        print(f"File '{selected_file['original_filename']}' deleted successfully.")
                    else:
                        print("Error deleting file. Some segments or records may remain.")
            except ValueError:
                print("Please enter a valid number.")
                
        elif choice == "9":
            test_encryption()
            
        elif choice == "10":
            # Create a simple test file in the current directory
            test_file_name = input("Enter test file name (default: test1.txt) >> ") or "test1.txt"
            test_file_path = os.path.join(os.getcwd(), test_file_name)
            
            try:
                with open(test_file_path, "w") as f:
                    f.write("This is a test file created by ByteScatter.\n" * 50)
                print(f"Test file created successfully at: {test_file_path}")
            except Exception as e:
                print(f"Error creating test file: {e}")

        elif choice == "11":
            files = list_files()  # Get all files from Dropbox
            if not files:
                print("No files found in Dropbox.")
                continue

            print("\nSelect a file to download and delete from Dropbox:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file.name}")

            try:
                selection = get_valid_input("Enter file number >> ")
                if selection < 1 or selection > len(files):
                    print("Invalid selection.")
                    continue

                selected_file = files[selection - 1]
                dropbox_filename = selected_file.name
                local_save_path = os.path.join("output", dropbox_filename)

                download_and_delete_file(dropbox_filename, local_save_path)

                if os.path.exists(local_save_path):
                    print(f"✅ Successfully downloaded and deleted '{dropbox_filename}' to '{local_save_path}'.")
                else:
                    print("❌ Failed to download file.")
            except ValueError:
                print("Please enter a valid number.")

                
        elif choice == "99":
            print("\nExiting program.")
            break
            
        else:
            print("\n Invalid option. Please choose again.")

#
#   Gracefully handle Ctrl+C interruption
#
def handle_exit(signum, frame):
    print("\nExiting program...")
    sys.exit(0)

#
#   Main function to handle the process
#
def main():
    # Call intro menu
    introMenu()

    # Set up signal handling for graceful exit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, handle_exit)

    # Setup argparse
    parser = argparse.ArgumentParser(description="File encryption and upload utility.")
    parser.add_argument("-f", "--file", type=str, help="Path to the file you want to encrypt and upload.")
    parser.add_argument("-ns", "--num_splits", type=int, help="Number of splits for the file.", default=3)
    parser.add_argument("-fp", "--file_password", type=str, help="Password for file encryption")
    parser.add_argument("-c", "--cloud", action="store_true", help="Upload segments to cloud services.")
    parser.add_argument("-i", "--interface", action="store_true", help="Use the interactive menu instead of command-line input.")
    parser.add_argument("-t", "--test", action="store_true", help="Run the encryption/decryption test.")
    
    args = parser.parse_args()

    if args.test:
        test_encryption()
    elif args.interface or (len(sys.argv) == 1):  # Default to interface if no args
        menu() 
    else:
        if args.file:
            file_path = args.file
            number_of_splits = args.num_splits
            file_pass = args.file_password
            if not file_pass:
                file_pass = input("Enter password for file encryption: ")
            upload(file_path, number_of_splits, file_pass, upload_to_cloud=args.cloud)
        else:
            print("Error: You must specify a file with -f/--file.")

if __name__ == '__main__':
    main()