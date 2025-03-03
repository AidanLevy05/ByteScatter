# HenHacks2025LKAD

ByteScatter: Secure Multi-Cloud File Distribution System
---
# Executive Summary

ByteScatter is an advanced file security solution that enhances data protection through a combination of strong encryption and multi-cloud distribution. By splitting files into encrypted segments and distributing them across different cloud storage providers, ByteScatter creates a security paradigm where no single breach can compromise the entire file. This documentation provides a comprehensive overview of the system's architecture, implementation details, development challenges, and security considerations.
# 1. Core Concept and Design Philosophy
ByteScatter addresses a fundamental and relevant problem in cloud storage security: how to leverage the convenience of cloud storage while mitigating the risk of unauthorized access. With this rapid change of AI training ethics and privacy laws (such as the EU cracking down on Apple), we figure this is more relevant than ever. Traditional approaches rely solely on encryption, which creates a single point of failure if the encryption key is compromised. ByteScatter takes a different approach by implementing a "divide and conquer" strategy:
Files are split into multiple segments
Each segment is individually encrypted with strong cryptography
Segments are distributed across different cloud providers (Google Drive, Dropbox, OneDrive)
A local metadata database maintains the information needed for retrieval and reconstruction
This approach offers several significant advantages:
- Enhanced Security: Even if an attacker compromises one cloud account, they obtain only encrypted fragments, not the complete file
- Distributes Trust: No single cloud provider has access to the entire dataset
- Leverages Multiple Storage Quotas: Users can maximize available free storage across services
- Redundancy Options: The system can be configured to store redundant segments for fault tolerance
# 2. System Architecture
ByteScatter implements a modular architecture with the following core components:
## 2.1 Component Overview
File Segmentation Engine: Splits files into a (user specified) number of chunks
Encryption Module: Manages key derivation, segment encryption, and authentication
Cloud Service Connectors: Interfaces with cloud storage APIs
Metadata Management: Tracks segment locations and encryption details
User Interface: Command-line interface for file operations / GUI
## 2.2 User Workflow
The system offers two primary workflows:
\
\
File Upload (Encryption and Distribution):
\
- User provides a file, number of segments, and encryption password
- System segments the file and generates a master encryption key
- Each segment is encrypted with a unique derived key
- Segments are distributed across configured cloud services
- Metadata is recorded in the local database
\
\
File Download (Retrieval and Reconstruction):
\
- User selects a file from the database and provides the password
- System locates segments (locally if available), and orders them
- Segments are decrypted and verified
- Original file is reconstructed and saved locally
## 2.3 Data Flow
The data flow through the system follows this pattern:
Original File → Segmentation → Encryption → Cloud Distribution
                                  ↓
                              Metadata Storage
                                  ↓
Cloud Retrieval → Decryption → Reassembly → Restored File

Each step involves careful handling of data to maintain security and integrity throughout the process.
-----
# 3. Technical Implementation
## 3.1 Encryption Model
ByteScatter implements a sophisticated encryption model using a key hierarchy:
Master Key Derivation: A file-specific master key is derived from the user's password using PBKDF2 or Argon2id (when available) with a high iteration count
- Segment Key Derivation: For each segment, a unique key is derived from the master key using HKDF
Segment Encryption: Each segment is encrypted using AES-256-GCM or ChaCha20-Poly1305, providing both confidentiality and integrity
The code example below shows this key derivation process:

```python
def derive_master_key(self, password, salt=None, use_argon2=True):
    if salt is None:
        salt = os.urandom(16)  # Generate 128-bit salt
    
    if use_argon2 and ARGON2_AVAILABLE:
        # Use argon2.low_level API for stronger password hashing
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
            length=32,  # 256-bit key
            salt=salt,
            iterations=600000,  # High iteration count for security
        )
        
        master_key = kdf.derive(password.encode('utf-8'))
        
        kdf_type = "pbkdf2"
        kdf_params = json.dumps({
            "algorithm": "sha256",
            "iterations": 600000,
            "length": 32
        })
    
    # Generate a verification hash to check password correctness later
    verification_hash = self._create_verification_hash(master_key)
    
    return master_key, salt, kdf_type, kdf_params, verification_hash
```

Notably, the system stores only key derivation parameters and verification hashes, never the actual encryption keys. This zero-knowledge approach means even if the metadata database is compromised, the attacker cannot decrypt the files without the original password.
## 3.2 File Segmentation
The segmentation engine divides files intelligently based on type:
- Text Files: Split by line count, ensuring each segment contains complete lines
- Binary Files: Split by byte ranges, ensuring each segment is under configurable size limits
The system adapts segment size based on file size, with logic to prevent excessive fragmentation of large files or inefficient handling of small files.
This method of implementation proves useful, as all kinds of common files are fully supported. Whether it be encrypted data formats like .docx, plain .txt, or even images and audio! 
## 3.3 Cloud Service Integration
ByteScatter attempts to integrate with multiple cloud storage services through their respective APIs:
- Dropbox: Direct integration using the Dropbox SDK
- Google Drive: Integration via the Google API client
- OneDrive: Integration through Microsoft Graph API 
\
\
Each connector implements a common interface for upload, download, and deletion operations, making the system extensible to additional cloud services.
One significant implementation detail is the handling of API rate limits and quotas. The system implements exponential backoff for failures and distributes uploads to stay within service limits.
## 3.4 Metadata Management
The system uses SQLite for structured metadata storage with the following schema:
- master_files: Stores file-level metadata (ID, name, segment count)
- master_keys: Stores key derivation parameters and verification hashes
- segment_keys_info: Stores segment-specific encryption details
- segment_cloud_locations: Tracks where each segment is stored
This relational approach is efficient for querying file retrieval and maintenance operations.
# 4. Development Challenges and Solutions
Throughout development, we encountered and solved several significant technical challenges:
## 4.1 Encryption Implementation Issues
Early versions of the encryption module faced several critical issues: \
\

Key Derivation Problems: Initial implementation derived segment keys insecurely without proper cryptographic key derivation functions
\

- Solution: Implemented HKDF (RFC 5869) to properly derive unique segment keys
\
\
Data Authentication Handling: Early versions of the code had no checks to ensure data wasn’t corrupted. This would result in the program returning a successful encrypt/decrypt while rendering the file unusable
\
- Solution: During the decryption process, unique metadata including the algorithm used, authentication tag, segment data, etc…). Each of these parameters are loaded from the DB and used to verify each segment independently
(Any fails to this check result in instant halt and report)
\
\
## 4.2 Cloud API Integration Challenges
Integrating with multiple cloud services presented unique challenges:
\
\
Dropbox API Token Management: The original implementation hardcoded Dropbox tokens in the code dropbox_helper.py:
```python
# Replace with your Dropbox access token
ACCESS_TOKEN = "[REDACTED]"
```
- Solution: Implemented secure token storage in the settings.json file with proper access controls
\
\
Segment Identification: Early versions struggled to match downloaded segments with their metadata

\
- Solution: Developed a naming scheme that embeds file ID and segment index in filenames. 
\
\

Cloud Retrieval Coordination: The system initially couldn't handle the case where segments were distributed across services
\
- Solution: Implemented a retrieval priority system that tries local storage first, then queries each configured cloud service
\
## 4.3 Database Management Issues
The database design evolved significantly to address several critical issues:
\
\
\
Race Conditions: Early implementations suffered from database corruption during concurrent operations
\

Solution: Implemented proper transaction handling and connection pooling
\
\
Metadata-Segment Mismatch: A critical bug in OLDMAIN.py allowed segments to be uploaded without properly recording their locations:
\
```python
# Problematic code from OLDMAIN.py that failed to update database
if upload_result["success"]:
    # Missing database update for cloud location
    print(f"✅ Uploaded encrypted segment: {segment_path} -> {upload_result['remote_path']}")
```
Solution: Added proper database transaction handling to ensure metadata consistency
\
\
Foreign Key Constraints: Initial schema lacked proper relationship constraints
\
Solution: Implemented foreign key relationships between tables to maintain referential integrity
\
## 4.4 Performance Optimizations
Performance testing revealed several bottlenecks that required optimization:
\
\
Sequential Cloud Uploads: Original implementation uploaded segments sequentially
\
Solution: Implemented concurrent uploads using Python's ThreadPoolExecutor
\
\
Memory Usage for Large Files: Processing large files caused memory exhaustion
\
Solution: Implemented streaming encryption that processes files in chunks without loading the entire file
\
\

Metadata Query Performance: Retrieving segment information became slow with many files (early iterations required manually pulling segments from a list)
\
Solution: Added proper indexing to the SQLite database and optimized query patterns. Now all relevant files can be grabbed by the program, and ordered.
\
# 5. Final Product Implementation
The final ByteScatter implementation delivers a security system with the following capabilities:
## 5.1 Key Features
Secure File Distribution: Files are split, encrypted, and distributed across multiple cloud services
\
Strong Encryption: AES-256-GCM and ChaCha20-Poly1305 provide state-of-the-art security
\
File Management: Interface for listing, retrieving, and deleting encrypted files
\
Cloud Integration: Support for Google Drive, Dropbox, and OneDrive (MORE ON THE WAY, the modular design is very flexible)
\
Availability Verification: Tools to check if all segments of a file are available for retrieval
\
Chunk Identification - Even if chunks are missing from the local machine, the DB will inform which chunks are needed to complete assembly, as well as if they are available on a cloud service
\
## 5.2 User Interface
The system offers a straightforward command-line interface as well as a GUI. For now we will explore the CLI:
```
=== ByteScatter Encryption Manager ===
1. View Settings
2. Update API Keys
3. Upload File (Local)
4. Upload File to Cloud
5. List Encrypted Files
6. Download File
7. Check File Availability
8. Delete Encrypted File
9. Run Encryption Test
10. Create Test File
11. List all files from dropbox
99. Exit
```
This interface provides all essential operations while maintaining security.
------
We also incorporpated a fully functional GUI:
[[media/screenshot1.png]]

\
We encourage you to check out our [Demo Video|www.youtube.com] where the features are on display
\
## 5.3 Security Properties
The final system achieves several important security properties:

- Zero-Knowledge Architecture: The system never stores encryption keys, only derivation parameters
- Authentication and Integrity: All encrypted segments include integrity verification
- Distribution Security: No single cloud provider has access to all segments
- Side-Channel Resistance: The implementation minimizes timing and other side-channel leaks
- Forward Secrecy: Each file uses a unique master key, limiting the impact of key compromise
\
## 5.4 Limitations and Future Work
Despite its near perfect design, ByteScatter has some limitations that could be addressed in future versions:
\
- Segment Redundancy: The current implementation lacks automatic redundancy for segments
- Cloud Provider Authentication: OAuth flows could be improved for smoother authentication
- Direct Sharing: No built-in mechanism for sharing encrypted files with other users
- UI Improvements: A graphical interface would improve accessibility (DONE)
- Multi-platform Support: Currently optimized for desktop platforms; mobile support could be added.
- Advanced Settings: Currently, the user has simple settings such as what providers to use, how many segments, and other option. 
    - We would like to add a more verbose set of options for advanced users where everything down to each individual segment can be routed however the user sees fit.
# 6. Conclusion
ByteScatter represents a significant advancement in secure cloud storage by combining strong encryption with physical distribution of data. The system's core innovation—spreading encrypted segments across multiple cloud providers—creates a security model where compromising a single cloud account or even the encryption algorithm alone is insufficient to access the protected data.
\
The development process revealed the challenges inherent in implementing cryptographic systems correctly, particularly when integrating with cloud APIs. Through careful implementation and testing, these challenges were overcome to create a robust, secure file protection system.
\
ByteScatter demonstrates that with proper cryptographic practices and thoughtful system design, it's possible to leverage cloud storage while maintaining strong security guarantees. This approach provides a valuable option for users and organizations with sensitive data who wish to utilize cloud services without fully trusting any single provider with their complete data.

# Your data is yours. Let’s keep it that way. 
