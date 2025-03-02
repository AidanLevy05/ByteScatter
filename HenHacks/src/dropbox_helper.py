import dropbox
import json
import os

# Replace with your Dropbox access token

with open("settings.json", "r") as file:
    config = json.load(file)

ACCESS_TOKEN = config.get("Dropbox")

# Initialize Dropbox client
dbx = dropbox.Dropbox(ACCESS_TOKEN)

def upload_file(local_path):
    """Uploads a file to Dropbox and returns status and remote path."""
    try:
        dropbox_path = "/" + os.path.basename(local_path)  # Upload to root Dropbox directory
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ Uploaded '{local_path}' to '{dropbox_path}' on Dropbox.")
        return {
            "success": True,
            "remote_path": dropbox_path,
            "service": "Dropbox"
        }
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def list_files():
    """Lists files in Dropbox."""
    try:
        files = dbx.files_list_folder("").entries
        if not files:
            print("📁 No files found in Dropbox.")
            return []
        print("\n📄 Files in Dropbox:")
        for i, file in enumerate(files):
            print(f"{i + 1}. {file.name}")
        return files
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def download_and_delete_file(dropbox_filename, local_save_path):
    """Downloads a file from Dropbox and deletes it after successful download."""
    try:
        # Download file
        dbx.files_download_to_file(local_save_path, "/" + dropbox_filename)
        print(f"✅ Downloaded '{dropbox_filename}' to '{local_save_path}'.")

        # Delete file from Dropbox
        dbx.files_delete_v2("/" + dropbox_filename)
        print(f"🗑️ Deleted '{dropbox_filename}' from Dropbox.")
    except Exception as e:
        print(f"❌ Error downloading or deleting file: {e}")

def main():
    # Step 1: Ask user for a file to upload
    local_path = input("Enter the file path to upload: ").strip()
    if os.path.exists(local_path):
        uploaded_path = upload_file(local_path)
        if uploaded_path:
            # Step 2: List files in Dropbox
            files = list_files()
            if files:
                # Step 3: Ask user for a file to download
                download_choice = input("\nEnter the filename to download and delete from Dropbox: ").strip()
                local_download_path = os.path.join(os.getcwd(), download_choice)
                download_and_delete_file(download_choice, local_download_path)
    else:
        print("❌ File not found. Please enter a valid file path.")

if __name__ == '__main__':
    main()