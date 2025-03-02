import os
import sys
from encryption import KeyManager, SegmentEncryptor

# Database for encryption keys
DB_PATH = "test_keys.db"

def test_basic_encryption():
    """
    Simple test to verify the encryption/decryption functionality works.
    """
    print("=== Basic Encryption Test ===")
    
    # Initialize encryptor
    print("Initializing encryptor...")
    key_manager = KeyManager(DB_PATH)
    segment_encryptor = SegmentEncryptor(DB_PATH)
    
    # Setup encryption (generate master key)
    print("Setting up encryption...")
    password = "testpassword123"
    try:
        # First, manually verify derive_master_key works
        master_key, salt, kdf_type, kdf_params, verification_hash = key_manager.derive_master_key(password)
        print(f"Master key derived successfully: {len(master_key)} bytes")
        print(f"KDF type: {kdf_type}")
        
        # Now try setup_encryption 
        file_id, master_key = segment_encryptor.setup_encryption(password)
        print(f"File ID created: {file_id}")
        print(f"Master key: {len(master_key)} bytes")
    except Exception as e:
        print(f"ERROR in setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Create test data
    test_data = b"This is a test message that will be encrypted and then decrypted."
    print(f"Test data: {len(test_data)} bytes")
    
    # Encrypt the data
    try:
        print("Encrypting data...")
        ciphertext, metadata, serialized_metadata = segment_encryptor.encrypt_file_segment(
            file_id, master_key, test_data, 0
        )
        print(f"Encryption successful: {len(ciphertext)} bytes")
        print(f"Metadata type: {type(metadata)}")
        
        # Save to files for verification
        with open("test_ciphertext.bin", "wb") as f:
            f.write(ciphertext)
        with open("test_metadata.json", "w") as f:
            f.write(serialized_metadata)
        
        print("Encrypted data saved to test_ciphertext.bin")
        print("Metadata saved to test_metadata.json")
    except Exception as e:
        print(f"ERROR in encryption: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Decrypt the data
    try:
        print("\nDecrypting data...")
        decrypted_data = segment_encryptor.decrypt_file_segment(
            ciphertext, serialized_metadata, master_key=master_key
        )
        print(f"Decryption successful: {len(decrypted_data)} bytes")
        
        # Verify decryption worked
        if decrypted_data == test_data:
            print("\nSUCCESS: Decrypted data matches original!")
            print(f"Original: {test_data}")
            print(f"Decrypted: {decrypted_data}")
        else:
            print("\nFAILURE: Decrypted data does not match original!")
            print(f"Original: {test_data}")
            print(f"Decrypted: {decrypted_data}")
    except Exception as e:
        print(f"ERROR in decryption: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Try decrypting with password instead of master key
    try:
        print("\nDecrypting with password...")
        decrypted_with_pwd = segment_encryptor.decrypt_file_segment(
            ciphertext, serialized_metadata, password=password
        )
        
        if decrypted_with_pwd == test_data:
            print("SUCCESS: Password-based decryption works!")
        else:
            print("FAILURE: Password-based decryption failed!")
    except Exception as e:
        print(f"ERROR in password decryption: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    print("\nCleaning up test files...")
    os.remove("test_ciphertext.bin")
    os.remove("test_metadata.json")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    print("Test completed!")

if __name__ == "__main__":
    test_basic_encryption()