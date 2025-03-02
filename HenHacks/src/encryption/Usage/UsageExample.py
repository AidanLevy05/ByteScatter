"""
Usage example for the SecureSegment encryption module

This demonstrates how other components can interact with our encryption system.
"""

import os
from securesegment.encryption import SegmentEncryptor

# Example usage scenario: encrypting file segments
def example_encrypt_segments():
    """Demonstrate encryption of multiple file segments"""
    
    # Initialize the encryptor with a SQLite database path
    encryptor = SegmentEncryptor(db_path="securesegment.db")
    
    # User provides a password for file encryption
    user_password = "strong-user-password"
    
    # Set up encryption for a new file
    file_id, master_key = encryptor.setup_encryption(user_password)
    print(f"Initialized encryption for file with ID: {file_id}")
    
    # In a real scenario, file segments would come from the I/O team
    # Here we simulate 3 segments of a file
    sample_segments = [
        b"This is the first segment of the file with some sample content.",
        b"This is the second segment with different content for demonstration.",
        b"And this is the third and final segment of our sample file."
    ]
    
    # Store encrypted segments and their metadata
    encrypted_segments = []
    
    for index, segment_data in enumerate(sample_segments):
        # Encrypt the segment
        ciphertext, metadata, serialized_metadata = encryptor.encrypt_file_segment(
            file_id, master_key, segment_data, index
        )
        
        print(f"Encrypted segment {index}:")
        print(f"  - Segment ID: {metadata['segment_id']}")
        print(f"  - Algorithm: {metadata['algorithm']}")
        print(f"  - Ciphertext size: {metadata['ciphertext_size']} bytes")
        
        # In a real scenario, the I/O team would store or upload:
        # 1. The ciphertext to cloud storage
        # 2. The metadata for later retrieval
        encrypted_segments.append((ciphertext, serialized_metadata))
    
    return file_id, encrypted_segments

# Example usage scenario: decrypting file segments
def example_decrypt_segments(file_id, encrypted_segments, password):
    """Demonstrate decryption of previously encrypted segments"""
    
    # Initialize the encryptor with the same database
    encryptor = SegmentEncryptor(db_path="securesegment.db")
    
    # Decrypt each segment
    decrypted_segments = []
    
    for index, (ciphertext, serialized_metadata) in enumerate(encrypted_segments):
        # Decrypt using the same password
        decrypted_data = encryptor.decrypt_file_segment(
            ciphertext, serialized_metadata, password=password
        )
        
        print(f"Decrypted segment {index}:")
        print(f"  - Size: {len(decrypted_data)} bytes")
        print(f"  - Content: {decrypted_data.decode('utf-8')}")
        
        decrypted_segments.append(decrypted_data)
    
    # In a real scenario, the I/O team would reassemble the original file
    # from these decrypted segments
    reassembled_file = b"".join(decrypted_segments)
    print("\nReassembled file content:")
    print(reassembled_file.decode('utf-8'))

# Example showing how another component would handle file upload
def example_file_upload_flow():
    """Demonstrate the integration with a file upload component"""
    
    # Initialize our encryptor
    encryptor = SegmentEncryptor(db_path="securesegment.db")
    
    # Sample scenario: User wants to encrypt and upload a 30MB file
    # The I/O team handles file reading and segmentation
    
    # 1. I/O team reads the file and determines segments (example)
    file_path = "large_document.pdf"  # Hypothetical file
    segment_size = 10 * 1024 * 1024  # 10MB segments
    
    # This would be handled by the I/O team's code
    def simulate_file_segmentation(file_path, segment_size):
        # In reality, this would read an actual file
        # For this example, we'll just simulate 3 segments
        print(f"Simulating segmentation of {file_path} into 10MB chunks")
        return [
            b"[Simulated first 10MB of file data]" * 500000,
            b"[Simulated second 10MB of file data]" * 500000,
            b"[Simulated third 10MB of file data]" * 500000
        ]
    
    segments = simulate_file_segmentation(file_path, segment_size)
    
    # 2. Our encryption component handles the security
    user_password = "user-secure-password-123"
    file_id, master_key = encryptor.setup_encryption(user_password)
    
    # Process each segment
    for i, segment_data in enumerate(segments):
        print(f"Processing segment {i+1}/{len(segments)}...")
        
        # Encrypt the segment
        ciphertext, metadata, serialized_metadata = encryptor.encrypt_file_segment(
            file_id, master_key, segment_data, i
        )
        
        # 3. I/O team would handle the actual upload to cloud storage
        def simulate_cloud_upload(segment_data, metadata, segment_index):
            # This would be the I/O team's code to upload to a cloud provider
            cloud_provider = ["Google Drive", "Dropbox", "OneDrive"][segment_index % 3]
            print(f"  Uploading segment {segment_index} ({len(segment_data)/1024/1024:.2f}MB) to {cloud_provider}")
            print(f"  Storing metadata ({len(serialized_metadata)} bytes) in database")
            # Return a simulated remote ID
            return f"cloud-id-{cloud_provider}-{segment_index}"
        
        remote_id = simulate_cloud_upload(ciphertext, serialized_metadata, i)
        
        # 4. I/O team would store the mapping of segment to remote location
        print(f"  Recorded mapping: Segment {i} -> {remote_id}")
    
    print(f"\nEncryption and upload complete. File ID: {file_id}")
    print("The user only needs to remember their password to decrypt and download later")
    
    # Return the file_id so it can be used for the download example
    return file_id, user_password

# Example showing how another component would handle file download
def example_file_download_flow(file_id, password):
    """Demonstrate the integration with a file download component"""
    
    # Initialize our encryptor
    encryptor = SegmentEncryptor(db_path="securesegment.db")
    
    # 1. I/O team retrieves metadata about the file segments
    def simulate_metadata_retrieval(file_id):
        # In reality, this would query a database
        print(f"Retrieving metadata for file {file_id}")
        # Simulate 3 segments with their locations
        return [
            {
                "segment_index": 0,
                "cloud_provider": "Google Drive",
                "remote_id": "cloud-id-Google Drive-0",
                "metadata": "{\"segment_id\": \"" + file_id + "_0\", \"file_id\": \"" + file_id + "\", \"segment_index\": 0, \"algorithm\": \"AES-256-GCM\", \"nonce\": \"AAAAAAAAAAAAAAAAAAAAAA==\", \"tag\": \"AAAAAAAAAAAAAAAAAAAAAA==\", \"ciphertext_size\": 5000000, \"encryption_time\": \"2023-01-01T12:00:00\"}"
            },
            {
                "segment_index": 1,
                "cloud_provider": "Dropbox",
                "remote_id": "cloud-id-Dropbox-1",
                "metadata": "{\"segment_id\": \"" + file_id + "_1\", \"file_id\": \"" + file_id + "\", \"segment_index\": 1, \"algorithm\": \"AES-256-GCM\", \"nonce\": \"AAAAAAAAAAAAAAAAAAAAAA==\", \"tag\": \"AAAAAAAAAAAAAAAAAAAAAA==\", \"ciphertext_size\": 5000000, \"encryption_time\": \"2023-01-01T12:00:00\"}"
            },
            {
                "segment_index": 2,
                "cloud_provider": "OneDrive",
                "remote_id": "cloud-id-OneDrive-2",
                "metadata": "{\"segment_id\": \"" + file_id + "_2\", \"file_id\": \"" + file_id + "\", \"segment_index\": 2, \"algorithm\": \"AES-256-GCM\", \"nonce\": \"AAAAAAAAAAAAAAAAAAAAAA==\", \"tag\": \"AAAAAAAAAAAAAAAAAAAAAA==\", \"ciphertext_size\": 5000000, \"encryption_time\": \"2023-01-01T12:00:00\"}"
            }
        ]
    
    segment_info = simulate_metadata_retrieval(file_id)
    
    # Sort segments by index to ensure correct order
    segment_info.sort(key=lambda x: x["segment_index"])
    
    # 2. I/O team downloads each segment
    decrypted_segments = []
    
    for segment in segment_info:
        print(f"Processing segment {segment['segment_index']+1}/{len(segment_info)}...")
        
        # Download the encrypted segment from cloud storage
        def simulate_cloud_download(remote_id, provider):
            # This would be the I/O team's code to download from a cloud provider
            print(f"  Downloading from {provider}: {remote_id}")
            # Return simulated encrypted data
            return b"[Encrypted segment data would be here in reality]" * 500000
        
        # Download the encrypted data
        encrypted_data = simulate_cloud_download(
            segment["remote_id"], segment["cloud_provider"]
        )
        
        # 3. Our encryption component handles the decryption
        try:
            decrypted_data = encryptor.decrypt_file_segment(
                encrypted_data, segment["metadata"], password=password
            )
            
            print(f"  Successfully decrypted segment {segment['segment_index']} "
                  f"({len(decrypted_data)/1024/1024:.2f}MB)")
            
            decrypted_segments.append((segment['segment_index'], decrypted_data))
            
        except Exception as e:
            print(f"  Error decrypting segment {segment['segment_index']}: {str(e)}")
            # In a real scenario, we might retry or handle this error
    
    # Sort again by index (in case they were downloaded out of order)
    decrypted_segments.sort(key=lambda x: x[0])
    
    # 4. I/O team reassembles the file
    def simulate_file_reassembly(segments):
        # This would be the I/O team's code to rebuild the original file
        print("Reassembling file from downloaded segments...")
        # In reality, this would write to an actual file
        total_size = sum(len(data) for _, data in segments)
        print(f"Reassembled file size: {total_size/1024/1024:.2f}MB")
    
    simulate_file_reassembly(decrypted_segments)
    print("Download and decryption complete!")

# Run the examples
if __name__ == "__main__":
    print("=" * 80)
    print("EXAMPLE 1: Basic Encryption and Decryption")
    print("=" * 80)
    
    # Run the basic encryption example
    file_id, encrypted_segments = example_encrypt_segments()
    
    print("\nNow demonstrating decryption...\n")
    
    # Run the basic decryption example
    example_decrypt_segments(file_id, encrypted_segments, "strong-user-password")
    
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Integration with File Upload/Download Components")
    print("=" * 80)
    
    # Run the file upload flow example
    file_id, password = example_file_upload_flow()
    
    print("\nNow demonstrating download flow...\n")
    
    # Run the file download flow example
    example_file_download_flow(file_id, password)