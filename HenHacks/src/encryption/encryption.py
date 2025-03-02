import os
import uuid
import json
import sqlite3
from base64 import b64encode, b64decode
from datetime import datetime

# Import cryptography components
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1

# For Argon2id (requires argon2-cffi package)
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False


class KeyManager:
    def __init__(self, db_path):
        """Initialize the key manager with path to SQLite database"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for key storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for master keys and segment keys if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_keys (
            file_id TEXT PRIMARY KEY,
            salt BLOB NOT NULL,
            kdf_type TEXT NOT NULL,
            kdf_params TEXT NOT NULL,
            verification_hash BLOB,
            creation_date TEXT NOT NULL,
            encrypted_key BLOB,
            encryption_info TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS segment_keys_info (
            segment_id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            segment_index INTEGER NOT NULL,
            encryption_algorithm TEXT NOT NULL,
            nonce BLOB NOT NULL,
            tag BLOB,
            FOREIGN KEY (file_id) REFERENCES master_keys(file_id)
        )
        ''')
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_segment_file ON segment_keys_info(file_id)")
        
        conn.commit()
        conn.close()
    
    def derive_master_key(self, password, salt=None, use_argon2=True):
        """
        Derive a master key from user password using Argon2id or PBKDF2
        
        Args:
            password (str): User-provided password
            salt (bytes, optional): Salt for key derivation. Generated if None.
            use_argon2 (bool): Whether to use Argon2id (if available) or PBKDF2
            
        Returns:
            tuple: (master_key, salt, kdf_type, kdf_params, verification_hash)
        """
        if salt is None:
            salt = os.urandom(16)  # Generate 128-bit salt
            
        if use_argon2 and ARGON2_AVAILABLE:
            # Use argon2.low_level API to provide a salt directly
            from argon2.low_level import Type, hash_secret_raw
            
            master_key = hash_secret_raw(
                secret=password.encode('utf-8'),
                salt=salt,
                time_cost=3,
                memory_cost=65536,
                parallelism=4,
                hash_len=32,
                type=Type.ID  # Argon2id
            )
            
            kdf_type = "argon2id"
            kdf_params = json.dumps({
                "time_cost": 3,
                "memory_cost": 65536,
                "parallelism": 4,
                "hash_len": 32
            })
        else:
            # Use PBKDF2 with high iteration count
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,             # 256-bit key
                salt=salt,
                iterations=600000,     # High iteration count for security
            )
            
            master_key = kdf.derive(password.encode('utf-8'))
            
            kdf_type = "pbkdf2"
            kdf_params = json.dumps({
                "algorithm": "sha256",
                "iterations": 600000,
                "length": 32
            })
        
        # Generate a verification hash to check password correctness later
        # without storing the actual key
        verification_hash = self._create_verification_hash(master_key)
        
        return master_key, salt, kdf_type, kdf_params, verification_hash

    def _create_verification_hash(self, key):
        """Create a hash to verify the key without storing it"""
        digest = hashes.Hash(hashes.SHA256())
        digest.update(key + b"verification")
        return digest.finalize()
    
    def verify_master_key(self, derived_key, verification_hash):
        """Verify that a derived key matches the stored verification hash"""
        expected_hash = self._create_verification_hash(derived_key)
        return expected_hash == verification_hash
    
    def derive_segment_key(self, master_key, segment_id, file_id):
        """
        Derive a unique key for a specific segment using HKDF
        
        Args:
            master_key (bytes): The master key from which to derive
            segment_id (str): Unique identifier for the segment
            file_id (str): Identifier for the parent file
            
        Returns:
            bytes: Unique key for this segment
        """
        # Use HKDF to derive a segment-specific key
        segment_info = f"{file_id}:{segment_id}".encode('utf-8')
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,    # 256-bit key
            salt=None,    # HKDF doesn't require a salt but can use one
            info=segment_info,
        )
        
        return hkdf.derive(master_key)
    
    def store_master_key_info(self, file_id, salt, kdf_type, kdf_params, verification_hash):
        """
        Store master key derivation info (not the key itself)
        
        Args:
            file_id (str): Unique identifier for the file
            salt (bytes): Salt used for key derivation
            kdf_type (str): Type of KDF used ("argon2id" or "pbkdf2")
            kdf_params (str): JSON string of KDF parameters
            verification_hash (bytes): Hash to verify the key
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO master_keys (
                file_id, salt, kdf_type, kdf_params, 
                verification_hash, creation_date
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, 
            (
                file_id, 
                salt, 
                kdf_type, 
                kdf_params, 
                verification_hash, 
                datetime.now().isoformat()
            )
        )
        
        conn.commit()
        conn.close()
    
    def store_segment_key_info(self, segment_id, file_id, segment_index, 
                              algorithm, nonce, tag=None):
        """
        Store information about a segment encryption
        
        Args:
            segment_id (str): Unique identifier for the segment
            file_id (str): Identifier for the parent file
            segment_index (int): Index of this segment in the file
            algorithm (str): Encryption algorithm used
            nonce (bytes): Nonce or IV used for encryption
            tag (bytes, optional): Authentication tag for AEAD ciphers
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO segment_keys_info (
                segment_id, file_id, segment_index, 
                encryption_algorithm, nonce, tag
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (segment_id, file_id, segment_index, algorithm, nonce, tag)
        )
        
        conn.commit()
        conn.close()
    
    def get_segment_key_info(self, segment_id):
        """
        Retrieve segment encryption information
        
        Args:
            segment_id (str): Unique identifier for the segment
            
        Returns:
            dict: Segment encryption information or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM segment_keys_info WHERE segment_id = ?",
            (segment_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_master_key_info(self, file_id):
        """
        Retrieve master key information
        
        Args:
            file_id (str): Unique identifier for the file
            
        Returns:
            dict: Master key information or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM master_keys WHERE file_id = ?",
            (file_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None


class EncryptionEngine:
    def __init__(self, key_manager, default_algorithm="AES-256-GCM"):
        """
        Initialize encryption engine
        
        Args:
            key_manager (KeyManager): KeyManager instance for key operations
            default_algorithm (str): Default encryption algorithm to use
        """
        self.key_manager = key_manager
        self.default_algorithm = default_algorithm
        self._validate_algorithm(default_algorithm)
    
    def _validate_algorithm(self, algorithm):
        """Validate that the selected algorithm is supported"""
        valid_algorithms = ["AES-256-GCM", "ChaCha20-Poly1305"]
        if algorithm not in valid_algorithms:
            raise ValueError(f"Algorithm must be one of: {valid_algorithms}")
    
    def encrypt_segment(self, segment_data, segment_key, algorithm=None):
        """
        Encrypt a segment with the provided key
        
        Args:
            segment_data (bytes): Raw bytes of the segment to encrypt
            segment_key (bytes): Key to use for encryption
            algorithm (str, optional): Override default algorithm if specified
            
        Returns:
            dict: Containing encrypted data and metadata (nonce, tag, etc.)
        """
        if algorithm is None:
            algorithm = self.default_algorithm
        else:
            self._validate_algorithm(algorithm)
        
        if algorithm == "AES-256-GCM":
            # Use AES-256-GCM (requires 256-bit key)
            aesgcm = AESGCM(segment_key)
            nonce = os.urandom(12)  # 96-bit nonce (recommended for GCM)
            ciphertext = aesgcm.encrypt(nonce, segment_data, None)
            
            # In GCM, the tag is appended to the ciphertext in the cryptography library
            # We'll separate it for clarity in our metadata
            tag = ciphertext[-16:]  # Last 16 bytes are the auth tag
            actual_ciphertext = ciphertext[:-16]
            
            return {
                "algorithm": algorithm,
                "nonce": nonce,
                "tag": tag,
                "ciphertext": actual_ciphertext
            }
            
        elif algorithm == "ChaCha20-Poly1305":
            # Use ChaCha20-Poly1305 (requires 256-bit key)
            chacha = ChaCha20Poly1305(segment_key)
            nonce = os.urandom(12)  # 96-bit nonce (required for ChaCha20-Poly1305)
            ciphertext = chacha.encrypt(nonce, segment_data, None)
            
            # Similar to GCM, the tag is at the end
            tag = ciphertext[-16:]
            actual_ciphertext = ciphertext[:-16]
            
            return {
                "algorithm": algorithm,
                "nonce": nonce,
                "tag": tag,
                "ciphertext": actual_ciphertext
            }
    
    def decrypt_segment(self, ciphertext, nonce, tag, algorithm, segment_key):
        """
        Decrypt a segment using the provided key and metadata
        
        Args:
            ciphertext (bytes): Encrypted segment data
            nonce (bytes): Nonce or IV used in encryption
            tag (bytes): Authentication tag
            algorithm (str): Encryption algorithm used
            segment_key (bytes): Key to use for decryption
            
        Returns:
            bytes: Decrypted segment data
        """
        self._validate_algorithm(algorithm)
        
        # Reconstruct the full ciphertext with tag for the cryptography library
        full_ciphertext = ciphertext + tag
        
        if algorithm == "AES-256-GCM":
            aesgcm = AESGCM(segment_key)
            return aesgcm.decrypt(nonce, full_ciphertext, None)
            
        elif algorithm == "ChaCha20-Poly1305":
            chacha = ChaCha20Poly1305(segment_key)
            return chacha.decrypt(nonce, full_ciphertext, None)


class MetadataHandler:
    """Handles creation and parsing of segment metadata"""
    
    def generate_segment_metadata(self, segment_id, file_id, segment_index, 
                                 algorithm, nonce, tag, ciphertext_size):
        """
        Generate metadata for an encrypted segment
        
        Args:
            segment_id (str): Unique identifier for the segment
            file_id (str): Identifier for the parent file
            segment_index (int): Index of this segment in the file
            algorithm (str): Encryption algorithm used
            nonce (bytes): Nonce or IV used in encryption
            tag (bytes): Authentication tag (for AEAD ciphers)
            ciphertext_size (int): Size of the ciphertext in bytes
            
        Returns:
            dict: Metadata for the segment
        """
        # Create metadata dictionary with all necessary fields
        metadata = {
            "segment_id": segment_id,
            "file_id": file_id,
            "segment_index": segment_index,
            "algorithm": algorithm,
            "nonce": b64encode(nonce).decode('utf-8'),
            "tag": b64encode(tag).decode('utf-8'),
            "ciphertext_size": ciphertext_size,
            "encryption_time": datetime.now().isoformat()
        }
        
        return metadata
    
    def serialize_metadata(self, metadata):
        """Convert metadata to JSON format for storage/transmission"""
        return json.dumps(metadata)
    
    def deserialize_metadata(self, serialized_metadata):
        """Parse serialized metadata back into a dictionary"""
        metadata = json.loads(serialized_metadata)
        
        # Convert base64 strings back to bytes for cryptographic operations
        if "nonce" in metadata:
            metadata["nonce"] = b64decode(metadata["nonce"])
        if "tag" in metadata:
            metadata["tag"] = b64decode(metadata["tag"])
            
        return metadata


class SegmentEncryptor:
    """Main class coordinating the encryption process"""
    
    def __init__(self, db_path, default_algorithm="AES-256-GCM"):
        """Initialize with database path and default algorithm"""
        self.key_manager = KeyManager(db_path)
        self.encryption_engine = EncryptionEngine(self.key_manager, default_algorithm)
        self.metadata_handler = MetadataHandler()
    
    def setup_encryption(self, password):
        """
        Initialize encryption for a new file with password
        
        Args:
            password (str): User-provided password
            
        Returns:
            str: file_id for the encryption session
        """
        # Generate a unique file ID
        file_id = str(uuid.uuid4())
        
        # Derive master key from password
        master_key, salt, kdf_type, kdf_params, verification_hash = \
            self.key_manager.derive_master_key(password)
        
        # Store key derivation info (not the key itself)
        self.key_manager.store_master_key_info(
            file_id, salt, kdf_type, kdf_params, verification_hash
        )
        
        return file_id, master_key
    
    def encrypt_file_segment(self, file_id, master_key, segment_data, segment_index):
        """
        Encrypt a single file segment
        
        Args:
            file_id (str): Identifier for the file encryption session
            master_key (bytes): The master key for this file
            segment_data (bytes): Raw data of the segment to encrypt
            segment_index (int): Index of this segment in the file
            
        Returns:
            tuple: (encrypted_data, metadata_dict, serialized_metadata)
        """
        # Generate a unique segment ID
        segment_id = f"{file_id}_{segment_index}"
        
        # Derive a unique key for this segment
        segment_key = self.key_manager.derive_segment_key(
            master_key, segment_id, file_id
        )
        
        # Encrypt the segment data
        encryption_result = self.encryption_engine.encrypt_segment(
            segment_data, segment_key
        )
        
        # Extract encryption details
        algorithm = encryption_result["algorithm"]
        nonce = encryption_result["nonce"]
        tag = encryption_result["tag"]
        ciphertext = encryption_result["ciphertext"]
        
        # Store segment encryption info in the database
        self.key_manager.store_segment_key_info(
            segment_id, file_id, segment_index, algorithm, nonce, tag
        )
        
        # Generate metadata
        metadata = self.metadata_handler.generate_segment_metadata(
            segment_id, file_id, segment_index, algorithm, 
            nonce, tag, len(ciphertext)
        )
        
        # Serialize metadata for storage/transmission
        serialized_metadata = self.metadata_handler.serialize_metadata(metadata)
        
        return ciphertext, metadata, serialized_metadata
    
    def decrypt_file_segment(self, encrypted_data, metadata, password=None, master_key=None):
        """
        Decrypt a file segment using either password or master key
        
        Args:
            encrypted_data (bytes): Encrypted segment data
            metadata (dict or str): Segment metadata (or serialized metadata)
            password (str, optional): User password (if master_key not provided)
            master_key (bytes, optional): Master key (if already derived)
            
        Returns:
            bytes: Decrypted segment data
        """
        # Parse metadata if it's serialized
        if isinstance(metadata, str):
            metadata = self.metadata_handler.deserialize_metadata(metadata)
        
        segment_id = metadata["segment_id"]
        file_id = metadata["file_id"]
        algorithm = metadata["algorithm"]
        nonce = metadata["nonce"]
        tag = metadata["tag"]
        
        # If master key not provided, derive it from password
        if master_key is None and password is not None:
            # Get key derivation info from database
            key_info = self.key_manager.get_master_key_info(file_id)
            if not key_info:
                raise ValueError(f"No key information found for file ID: {file_id}")
            
            # Derive master key using stored parameters
            salt = key_info["salt"]
            kdf_type = key_info["kdf_type"]
            verification_hash = key_info["verification_hash"]
            
            # Use the same derivation method based on stored KDF type
            use_argon2 = (kdf_type == "argon2id")
            master_key, _, _, _, _ = self.key_manager.derive_master_key(
                password, salt, use_argon2
            )
            
            # Verify the derived key is correct
            if not self.key_manager.verify_master_key(master_key, verification_hash):
                raise ValueError("Invalid password")
        
        if master_key is None:
            raise ValueError("Either password or master_key must be provided")
        
        # Derive segment key
        segment_key = self.key_manager.derive_segment_key(
            master_key, segment_id, file_id
        )
        
        # Decrypt the segment
        decrypted_data = self.encryption_engine.decrypt_segment(
            encrypted_data, nonce, tag, algorithm, segment_key
        )
        
        return decrypted_data