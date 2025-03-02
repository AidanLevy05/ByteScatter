import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import sys
import time
import shutil
import webbrowser
from tkinterdnd2 import DND_FILES, TkinterDnD


class EncryptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ByteScatter")
        self.center_window(600, 450)  # Made slightly taller for more buttons
        self.root.configure(bg="#f0f0f0")
        
        # Enable Drag and Drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_file_drop)

        self.file_path = None

        # Top Bar
        tk.Label(self.root, text="ByteScatter", font=("Arial", 18, "bold"), bg="#f0f0f0").place(x=20, y=10)

        # Settings button
        self.settings_button = tk.Button(self.root, text="⚙ Settings", font=("Arial", 10), 
                                       command=self.open_settings, bg="#d3d3d3", relief="flat")
        self.settings_button.place(x=500, y=10, width=80, height=30)

        # Help button
        self.help_button = tk.Button(self.root, text="❓ Help", font=("Arial", 10), 
                                   command=self.open_help, bg="#d3d3d3", relief="flat")
        self.help_button.place(x=500, y=50, width=80, height=30)

        # Drag and Drop Box
        self.drop_area = tk.Label(self.root, text="📂 Drop File Here or Click to Browse", 
                                font=("Arial", 14), fg="#404040", bg="#ffffff", relief="groove", 
                                width=40, height=6, cursor="hand2")
        self.drop_area.place(relx=0.5, rely=0.4, anchor="center")  # Moved up a bit
        self.drop_area.bind("<Button-1>", self.select_file)

        # Button Frame for all file-related buttons
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.place(relx=0.5, rely=0.75, anchor="center")

        # Uploaded Files Button
        self.uploaded_files_button = tk.Button(button_frame, text="📁 View Encrypted Files", 
                                            font=("Arial", 12), command=self.view_uploaded_files, 
                                            bg="#4CAF50", fg="white", relief="flat", width=25)
        self.uploaded_files_button.pack(pady=5, fill="x", expand=True, ipady=5)

        # Downloads Button
        self.downloads_button = tk.Button(button_frame, text="📥 View Downloads", 
                                        font=("Arial", 12), command=self.view_downloads, 
                                        bg="#2196F3", fg="white", relief="flat", width=25)
        self.downloads_button.pack(pady=5, fill="x", expand=True, ipady=5)

        # Cloud Status Button
        self.cloud_status_button = tk.Button(button_frame, text="☁️ Cloud Storage Status", 
                                          font=("Arial", 12), command=self.view_cloud_status, 
                                          bg="#FF9800", fg="white", relief="flat", width=25)
        self.cloud_status_button.pack(pady=5, fill="x", expand=True, ipady=5)
    
    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def select_file(self, event=None):
        """Opens file dialog for manual file selection."""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.clear_window()
            FileSelectionWindow(self.root, file_path)

    def on_file_drop(self, event):
        """Handles file drop event and transitions to FileSelectionWindow."""
        file_path = event.data.strip()
        if file_path.startswith("{") and file_path.endswith("}"): 
            file_path = file_path[1:-1]  # Fix path formatting if needed
        if os.path.isfile(file_path): 
            self.clear_window()
            FileSelectionWindow(self.root, file_path)
        else:
            messagebox.showerror("Error", "Invalid file dropped.")

    def open_settings(self):
        self.clear_window()
        SettingsWindow(self.root)

    def open_help(self):
        self.clear_window()
        HelpWindow(self.root)

    def view_uploaded_files(self):
        self.clear_window()
        UploadedFilesWindow(self.root)
    
    def view_downloads(self):
        """Open the uploads window with downloads tab active"""
        self.clear_window()
        upload_window = UploadedFilesWindow(self.root)
        # Select the downloads tab
        upload_window.notebook.select(1)  # Index 1 is the downloads tab

    def view_cloud_status(self):
        """View cloud storage status and connection information"""
        self.clear_window()
        CloudStatusWindow(self.root)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

class FileSelectionWindow:
    def __init__(self, root, file_path):
        self.root = root
        self.root.title("File Selection")
        self.center_window(500, 300)
        self.file_path = tk.StringVar(value=file_path)
        self.splits = tk.StringVar(value="2")
        self.password = tk.StringVar()
        self.show_password = False

        tk.Label(self.root, text="Edit File Path:", font=("Arial", 12)).pack(pady=5)
        self.file_entry = tk.Entry(self.root, textvariable=self.file_path, width=50)
        self.file_entry.pack(pady=5)

        tk.Label(self.root, text="Number of Splits:", font=("Arial", 12)).pack(pady=5)
        self.splits_entry = tk.Entry(self.root, textvariable=self.splits, width=10)
        self.splits_entry.pack(pady=5)

        tk.Label(self.root, text="Encryption Password:", font=("Arial", 12)).pack(pady=5)

        pass_frame = tk.Frame(self.root)
        pass_frame.pack(pady=5)

        self.pass_entry = tk.Entry(pass_frame, textvariable=self.password, width=30, show="*")
        self.pass_entry.pack(side="left", padx=5)

        self.toggle_pass_button = tk.Button(pass_frame, text="👁", command=self.toggle_password, width=3)
        self.toggle_pass_button.pack(side="left")

        # Navigation Buttons
        self.back_button = tk.Button(self.root, text="⬅ Back", command=self.go_back)
        self.back_button.place(x=20, y=250)

        self.split_button = tk.Button(self.root, text="Split ➡", command=self.next_window, bg="#4CAF50", fg="white")
        self.split_button.place(x=400, y=250)

    def toggle_password(self):
        self.show_password = not self.show_password
        self.pass_entry.config(show="" if self.show_password else "*")

    def go_back(self):
        self.clear_window()
        EncryptionApp(self.root)

    # Enhanced version of the next_window method in FileSelectionWindow
# that includes a progress bar for better user feedback

    def next_window(self):
        """Processes file splitting and encryption when the Split button is clicked"""
        file_path = self.file_path.get()
        try:
            # Validate inputs
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File not found: {file_path}")
                return
                
            num_splits = int(self.splits.get())
            if num_splits < 1:
                messagebox.showerror("Error", "Number of splits must be at least 1")
                return
                
            password = self.password.get()
            if not password:
                messagebox.showerror("Error", "Password is required")
                return
            
            # Ask if user wants to upload to cloud
            upload_to_cloud = messagebox.askyesno("Cloud Upload", 
                                                "Would you like to upload segments to Dropbox?")
            
            # Show a progress dialog with progress bar
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Processing")
            progress_window.geometry("300x150")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Make the progress window non-resizable
            progress_window.resizable(False, False)
            
            # Add description label
            desc_label = tk.Label(progress_window, text="Splitting and encrypting file...", 
                            font=("Arial", 12))
            desc_label.pack(pady=(15, 5))
            
            # Add status label that will be updated
            status_label = tk.Label(progress_window, text="Preparing...", 
                                font=("Arial", 10))
            status_label.pack(pady=5)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(progress_window, orient="horizontal", 
                                        length=250, mode="determinate")
            progress_bar.pack(pady=10, padx=20)
            
            # Add cancel button
            cancel_button = tk.Button(progress_window, text="Cancel", 
                                command=progress_window.destroy)
            cancel_button.pack(pady=5)
            
            # Update the UI to show we're working
            self.root.update()
            
            # Define progress callback function
            def update_progress(stage, progress, message):
                if progress_window.winfo_exists():  # Check if window still exists
                    if stage == "splitting":
                        desc_label.config(text="Splitting File...")
                    elif stage == "encrypting":
                        desc_label.config(text="Encrypting Segments...")
                    elif stage == "uploading":
                        desc_label.config(text="Uploading to Cloud...")
                    
                    status_label.config(text=message)
                    progress_bar["value"] = progress
                    self.root.update()
            
            # Call the upload function from main.py with progress callback
            from main import upload
            
            # Define a simple wrapper to add progress updates
            # Note: This assumes you've modified main.py's upload function to accept a progress_callback
            def run_with_progress():
                file_id = None
                encrypted_segments = None
                
                try:
                    # Initialize progress
                    update_progress("splitting", 0, "Analyzing file...")
                    
                    # Get file size for progress calculation
                    file_size = os.path.getsize(file_path)
                    
                    # Simulate progress updates (you'd need to modify main.py to actually call the callback)
                    update_progress("splitting", 10, f"Splitting {os.path.basename(file_path)}...")
                    
                    # Call the actual upload function
                    file_id, encrypted_segments = upload(file_path, num_splits, password, upload_to_cloud)
                    
                    # Final progress update
                    update_progress("encrypting", 100, "Completed!")
                    
                    return file_id, encrypted_segments
                except Exception as e:
                    if progress_window.winfo_exists():
                        messagebox.showerror("Error", f"Processing failed: {str(e)}")
                    return None, None
            
            # Run the processing
            file_id, encrypted_segments = run_with_progress()
            
            # Close progress window if it still exists
            if progress_window.winfo_exists():
                progress_window.destroy()
            
            if file_id and encrypted_segments:
                # Convert encrypted_segments to the format expected by SuccessWindow
                encrypted_files = []
                for segment in encrypted_segments:
                    encrypted_path = segment.get("encrypted_path")
                    metadata_path = segment.get("metadata_path")
                    if encrypted_path and metadata_path:
                        encrypted_files.append((encrypted_path, metadata_path))
                
                # Clear the window and show the success screen
                self.clear_window()
                SuccessWindow(self.root, file_path, encrypted_files, "output")
            else:
                if not progress_window.winfo_exists():  # If window was closed by user (cancelled)
                    return
                messagebox.showerror("Error", "Failed to encrypt and split the file.")
        except ValueError as e:
            if "invalid literal for int" in str(e):
                messagebox.showerror("Error", "Number of splits must be a valid number")
            else:
                messagebox.showerror("Error", f"Input error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error processing file: {str(e)}")
    ###
    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


class SuccessWindow:
    def __init__(self, root, original_file, encrypted_files, save_dir="output"):
        self.root = root
        self.root.title("Encryption Complete")
        self.center_window(690, 400)
        
        # Title Label
        tk.Label(self.root, text="Encryption Successful!", font=("Arial", 16, "bold"), fg="green").grid(row=0, column=0, columnspan=2, pady=10)

        # Original File Info
        tk.Label(self.root, text="Original File:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", padx=10)
        tk.Label(self.root, text=original_file, font=("Arial", 12), fg="gray").grid(row=2, column=0, sticky="w", padx=10)

        # File ID Info (if available from metadata)
        if len(encrypted_files) > 0:
            # Extract the file ID from the encrypted filename (assuming format like "abc123_split_0_filename.ext")
            enc_filename = os.path.basename(encrypted_files[0][0])
            file_id_prefix = enc_filename.split('_')[0] if '_' in enc_filename else "N/A"
            
            tk.Label(self.root, text="File ID:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky="w", padx=10)
            tk.Label(self.root, text=file_id_prefix, font=("Arial", 12), fg="blue").grid(row=4, column=0, sticky="w", padx=10)

        # Separator Line
        tk.Frame(self.root, height=2, width=580, bg="black").grid(row=5, column=0, columnspan=2, pady=5)

        # Save Location
        tk.Label(self.root, text="Saved At:", font=("Arial", 12, "bold")).grid(row=6, column=0, sticky="w", padx=10)
        tk.Label(self.root, text=os.path.abspath(save_dir), font=("Arial", 12), fg="gray").grid(row=7, column=0, sticky="w", padx=10)

        # Output Files Label
        tk.Label(self.root, text="Generated Files:", font=("Arial", 12, "bold")).grid(row=8, column=0, sticky="w", padx=10)

        # Output Files List (scrollable)
        frame = tk.Frame(self.root)
        frame.grid(row=9, column=0, padx=10, pady=5, sticky="w")
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_list = tk.Listbox(frame, height=6, width=50, yscrollcommand=scrollbar.set)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.file_list.yview)

        for enc_file, meta_file in encrypted_files:
            self.file_list.insert(tk.END, f"Encrypted: {os.path.basename(enc_file)}")
            self.file_list.insert(tk.END, f"Metadata: {os.path.basename(meta_file)}")
            self.file_list.insert(tk.END, " ")  # Spacer for clarity

        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=9, column=1, padx=20)

        # Cloud & Local Buttons
        # if not any("_cloud_" in f[0] for f in encrypted_files):  # Check if already uploaded to cloud
        #     self.cloud_button = tk.Button(button_frame, text="☁ Upload to Cloud", font=("Arial", 12), 
        #                                 bg="#2196F3", fg="white", command=self.upload_to_cloud)
        #     self.cloud_button.pack(pady=5, fill="x")

        # Open output folder button
        self.open_folder_button = tk.Button(button_frame, text="📂 Open Folder", font=("Arial", 12),
                                        bg="#4CAF50", fg="white", command=lambda: self.open_folder(save_dir))
        self.open_folder_button.pack(pady=5, fill="x")
        
        # Home button
        self.home_button = tk.Button(self.root, text="🏠 Return to Home", font=("Arial", 12), 
                                 bg="#FFA500", fg="white", command=self.return_to_home)
        self.home_button.grid(row=10, column=0, columnspan=2, pady=20)

    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def upload_to_cloud(self):
        """Upload files to cloud if not already uploaded"""
        # You can implement this to call the cloud upload function from main.py
        messagebox.showinfo("Cloud Upload", "Starting cloud upload...")
        # Call your cloud upload function here
        
    def open_folder(self, folder_path):
        """Open the folder containing the encrypted files"""
        try:
            abs_path = os.path.abspath(folder_path)
            if os.path.exists(abs_path):
                # Open file explorer to the folder
                if os.name == 'nt':  # Windows
                    os.startfile(abs_path)
                elif os.name == 'posix':  # macOS or Linux
                    import subprocess
                    subprocess.Popen(['open', abs_path] if sys.platform == 'darwin' else ['xdg-open', abs_path])
            else:
                messagebox.showerror("Error", f"Folder not found: {abs_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
    
    def return_to_home(self):
        """Return to main screen"""
        self.root.destroy()
        root = TkinterDnD.Tk()
        app = EncryptionApp(root)
        root.mainloop()

class CloudStatusWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Cloud Storage Status")
        self.center_window(700, 500)
        self.root.configure(bg="#f0f0f0")
        
        # Load settings to get API keys
        from main import load_settings
        self.settings = load_settings()
        
        # Header
        header_frame = tk.Frame(self.root, bg="#333333", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="Cloud Storage Status", font=("Arial", 16, "bold"), 
                 fg="white", bg="#333333").pack(pady=15)
        
        # Back button
        self.back_button = tk.Button(self.root, text="← Back", font=("Arial", 10), 
                                    command=self.go_back, bg="#d3d3d3")
        self.back_button.place(x=20, y=15, width=80, height=30)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#f0f0f0")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Connection status
        status_frame = tk.LabelFrame(content_frame, text="Connection Status", 
                                   font=("Arial", 12, "bold"), bg="#f0f0f0", padx=15, pady=15)
        status_frame.pack(fill="x", pady=10)
        
        # Dropbox status
        dropbox_frame = tk.Frame(status_frame, bg="#f0f0f0")
        dropbox_frame.pack(fill="x", pady=5)
        
        dropbox_icon = tk.Label(dropbox_frame, text="Dropbox:", font=("Arial", 12), 
                              bg="#f0f0f0", width=15, anchor="w")
        dropbox_icon.pack(side="left")
        
        dropbox_status = "Configured" if self.settings.get("Dropbox") and self.settings.get("Dropbox") != "000" else "Not Configured"
        dropbox_color = "green" if dropbox_status == "Configured" else "red"
        
        dropbox_status_label = tk.Label(dropbox_frame, text=dropbox_status, font=("Arial", 12), 
                                      fg=dropbox_color, bg="#f0f0f0")
        dropbox_status_label.pack(side="left", padx=10)
        
        # Google Drive status
        gdrive_frame = tk.Frame(status_frame, bg="#f0f0f0")
        gdrive_frame.pack(fill="x", pady=5)
        
        gdrive_icon = tk.Label(gdrive_frame, text="Google Drive:", font=("Arial", 12), 
                             bg="#f0f0f0", width=15, anchor="w")
        gdrive_icon.pack(side="left")
        
        gdrive_status = "Configured" if self.settings.get("GoogleDrive") and self.settings.get("GoogleDrive") != "000" else "Not Configured"
        gdrive_color = "green" if gdrive_status == "Configured" else "red"
        
        gdrive_status_label = tk.Label(gdrive_frame, text=gdrive_status, font=("Arial", 12), 
                                     fg=gdrive_color, bg="#f0f0f0")
        gdrive_status_label.pack(side="left", padx=10)
        
        # OneDrive status
        onedrive_frame = tk.Frame(status_frame, bg="#f0f0f0")
        onedrive_frame.pack(fill="x", pady=5)
        
        onedrive_icon = tk.Label(onedrive_frame, text="OneDrive:", font=("Arial", 12), 
                               bg="#f0f0f0", width=15, anchor="w")
        onedrive_icon.pack(side="left")
        
        onedrive_status = "Configured" if self.settings.get("OneDrive") and self.settings.get("OneDrive") != "000" else "Not Configured"
        onedrive_color = "green" if onedrive_status == "Configured" else "red"
        
        onedrive_status_label = tk.Label(onedrive_frame, text=onedrive_status, font=("Arial", 12), 
                                       fg=onedrive_color, bg="#f0f0f0")
        onedrive_status_label.pack(side="left", padx=10)
        
        # File statistics
        stats_frame = tk.LabelFrame(content_frame, text="File Statistics", 
                                  font=("Arial", 12, "bold"), bg="#f0f0f0", padx=15, pady=15)
        stats_frame.pack(fill="x", pady=10)
        
        # Get file statistics
        from main import list_encrypted_files
        files = list_encrypted_files()
        
        total_files = len(files)
        total_segments = sum(file.get('segment_count', 0) for file in files)
        
        # Calculate segments per service (this would need to be implemented in main.py)
        segments_per_service = self.get_segments_per_service()
        
        # Display statistics
        tk.Label(stats_frame, text=f"Total Files: {total_files}", font=("Arial", 12), 
               bg="#f0f0f0").pack(anchor="w", pady=2)
        tk.Label(stats_frame, text=f"Total Segments: {total_segments}", font=("Arial", 12), 
               bg="#f0f0f0").pack(anchor="w", pady=2)
        
        # Services breakdown
        if segments_per_service:
            service_frame = tk.Frame(stats_frame, bg="#f0f0f0")
            service_frame.pack(fill="x", pady=5)
            
            tk.Label(service_frame, text="Segments per Service:", font=("Arial", 12), 
                   bg="#f0f0f0").pack(anchor="w", pady=2)
            
            for service, count in segments_per_service.items():
                tk.Label(service_frame, text=f"  - {service}: {count}", font=("Arial", 12), 
                       bg="#f0f0f0").pack(anchor="w", pady=2)
        
        # Actions frame
        actions_frame = tk.LabelFrame(content_frame, text="Actions", 
                                    font=("Arial", 12, "bold"), bg="#f0f0f0", padx=15, pady=15)
        actions_frame.pack(fill="x", pady=10)
        
        # Action buttons
        buttons_frame = tk.Frame(actions_frame, bg="#f0f0f0")
        buttons_frame.pack(fill="x", pady=5)
        
        # Test connections button
        test_conn_btn = tk.Button(buttons_frame, text="Test Cloud Connections", font=("Arial", 11),
                                bg="#2196F3", fg="white", command=self.test_connections)
        test_conn_btn.pack(side="left", padx=5, pady=5)
        
        # Configure API keys button
        configure_btn = tk.Button(buttons_frame, text="Configure API Keys", font=("Arial", 11),
                                bg="#FF9800", fg="white", command=self.open_settings)
        configure_btn.pack(side="left", padx=5, pady=5)
        
        # View Dropbox files button (only if configured)
        if dropbox_status == "Configured":
            view_dropbox_btn = tk.Button(buttons_frame, text="View Dropbox Files", font=("Arial", 11),
                                      bg="#4CAF50", fg="white", command=self.view_dropbox_files)
            view_dropbox_btn.pack(side="left", padx=5, pady=5)
    
    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def get_segments_per_service(self):
        """Calculate how many segments are stored on each service"""
        # This is a stub - in a real implementation you would query 
        # the database to count segments per service
        try:
            # Connect to the database
            import sqlite3
            conn = sqlite3.connect("keys.db")
            cursor = conn.cursor()
            
            # Check if the segment_cloud_locations table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='segment_cloud_locations'
            """)
            
            if cursor.fetchone() is None:
                return {}
            
            # Count segments by cloud service
            cursor.execute("""
                SELECT cloud_service, COUNT(*) as count 
                FROM segment_cloud_locations 
                GROUP BY cloud_service
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            return {service: count for service, count in results}
        except Exception as e:
            print(f"Error getting segments per service: {e}")
            return {}
    
    def test_connections(self):
        """Test connections to cloud services"""
        # Create progress dialog
        progress = tk.Toplevel(self.root)
        progress.title("Testing Cloud Connectivity")
        progress.geometry("300x200")
        progress.transient(self.root)
        progress.grab_set()
        
        tk.Label(progress, text="Testing cloud connections...", 
                font=("Arial", 12)).pack(pady=10)
        
        results_frame = tk.Frame(progress)
        results_frame.pack(fill="x", padx=20, pady=10)
        
        # Initialize status labels
        dropbox_label = tk.Label(results_frame, text="Dropbox: Testing...", 
                               font=("Arial", 11))
        dropbox_label.grid(row=0, column=0, sticky="w", pady=5)
        
        google_label = tk.Label(results_frame, text="Google Drive: Testing...", 
                              font=("Arial", 11))
        google_label.grid(row=1, column=0, sticky="w", pady=5)
        
        onedrive_label = tk.Label(results_frame, text="OneDrive: Testing...", 
                                font=("Arial", 11))
        onedrive_label.grid(row=2, column=0, sticky="w", pady=5)
        
        # Update the UI
        self.root.update()
        
        # Test each service
        # Dropbox
        try:
            dropbox_key = self.settings.get("Dropbox", "")
            if dropbox_key and dropbox_key != "000":
                # Import the needed function to test Dropbox
                from dropbox_helper import list_files
                # If we get any result (even empty list), connection works
                files = list_files()
                if files is not None:
                    dropbox_label.config(text="Dropbox: ✓ Connected", fg="green")
                else:
                    dropbox_label.config(text="Dropbox: ✗ Connection failed", fg="red")
            else:
                dropbox_label.config(text="Dropbox: Not configured", fg="gray")
        except Exception as e:
            dropbox_label.config(text=f"Dropbox: ✗ Error: {str(e)[:30]}", fg="red")
        
        self.root.update()
        
        # Google Drive - simulation since we don't have full implementation
        google_key = self.settings.get("GoogleDrive", "")
        if google_key and google_key != "000":
            # Here you would test actual Google Drive connection
            # For now, just show as not implemented
            google_label.config(text="Google Drive: ⚠ Not implemented", fg="#FFA500")
        else:
            google_label.config(text="Google Drive: Not configured", fg="gray")
        
        self.root.update()
        
        # OneDrive - simulation since we don't have full implementation
        onedrive_key = self.settings.get("OneDrive", "")
        if onedrive_key and onedrive_key != "000":
            # Here you would test actual OneDrive connection
            # For now, just show as not implemented
            onedrive_label.config(text="OneDrive: ⚠ Not implemented", fg="#FFA500")
        else:
            onedrive_label.config(text="OneDrive: Not configured", fg="gray")
        
        # Add close button
        tk.Button(progress, text="Close", command=progress.destroy).pack(pady=10)
    
    def view_dropbox_files(self):
        """Show files currently in Dropbox"""
        try:
            from dropbox_helper import list_files
            files = list_files()
            
            if not files:
                messagebox.showinfo("Dropbox Files", "No files found in Dropbox.")
                return
            
            # Create a window to display files
            files_window = tk.Toplevel(self.root)
            files_window.title("Dropbox Files")
            files_window.geometry("500x400")
            files_window.transient(self.root)
            
            tk.Label(files_window, text="Files in Dropbox", font=("Arial", 14, "bold")).pack(pady=10)
            
            # Create a listbox for files
            list_frame = tk.Frame(files_window)
            list_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            
            file_list = tk.Listbox(list_frame, height=15, width=50, yscrollcommand=scrollbar.set, font=("Arial", 11))
            file_list.pack(side="left", fill="both", expand=True, pady=10)
            scrollbar.config(command=file_list.yview)
            
            # Add files to the list
            for i, file in enumerate(files, 1):
                file_list.insert(tk.END, f"{i}. {file.name}")
            
            # Add button to download selected file
            def download_selected():
                selected = file_list.curselection()
                if not selected:
                    messagebox.showinfo("Selection Required", "Please select a file to download.")
                    return
                
                idx = selected[0]
                selected_file = files[idx]
                
                # Ask where to save
                save_path = filedialog.asksaveasfilename(
                    initialfile=selected_file.name,
                    title="Save File As",
                    filetypes=[("All Files", "*.*")]
                )
                
                if not save_path:
                    return  # User cancelled
                
                # Show download progress
                progress_window = tk.Toplevel(files_window)
                progress_window.title("Downloading")
                progress_window.geometry("300x150")
                progress_window.transient(files_window)
                progress_window.grab_set()
                
                tk.Label(progress_window, text=f"Downloading {selected_file.name}...", 
                        font=("Arial", 12)).pack(pady=10)
                
                progress_text = tk.Label(progress_window, text="Please wait...", 
                                      font=("Arial", 10))
                progress_text.pack(pady=5)
                
                # Update UI
                self.root.update()
                
                try:
                    # Import the download function
                    from dropbox_helper import download_and_delete_file
                    
                    # Ask if user wants to delete after download
                    delete_after = messagebox.askyesno("Delete After Download", 
                                                     "Do you want to delete the file from Dropbox after downloading?")
                    
                    if delete_after:
                        # Download and delete
                        download_and_delete_file(selected_file.name, save_path)
                        progress_text.config(text="Downloaded and deleted from Dropbox.")
                    else:
                        # Just download (would need to be implemented in dropbox_helper)
                        # This is a workaround using the existing function but not ideal
                        # In a real implementation, you'd have a separate download function
                        temp_path = save_path + ".temp"
                        download_and_delete_file(selected_file.name, temp_path)
                        
                        # Copy the file to the desired location
                        import shutil
                        shutil.copy2(temp_path, save_path)
                        
                        # Re-upload the file to Dropbox
                        from dropbox_helper import upload_file
                        upload_file(temp_path)
                        
                        # Delete the temp file
                        os.remove(temp_path)
                        
                        progress_text.config(text="Downloaded successfully.")
                    
                    # Add a close button
                    tk.Button(progress_window, text="Close", 
                            command=progress_window.destroy).pack(pady=10)
                    
                    # Refresh the file list
                    files_window.destroy()
                    self.view_dropbox_files()
                    
                except Exception as e:
                    progress_window.destroy()
                    messagebox.showerror("Error", f"Error downloading file: {str(e)}")
            
            # Buttons frame
            buttons_frame = tk.Frame(files_window)
            buttons_frame.pack(pady=10)
            
            tk.Button(buttons_frame, text="Download Selected", 
                    command=download_selected, bg="#4CAF50", fg="white").pack(side="left", padx=5)
            
            tk.Button(buttons_frame, text="Close", 
                    command=files_window.destroy).pack(side="left", padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error listing Dropbox files: {str(e)}")
    
    def open_settings(self):
        """Open the settings window"""
        self.root.destroy()
        root = TkinterDnD.Tk()
        settings_window = SettingsWindow(root)
        root.mainloop()

    def go_back(self):
        """Return to the main screen"""
        self.root.destroy()
        root = TkinterDnD.Tk()
        app = EncryptionApp(root)
        root.mainloop()

class UploadedFilesWindow:

    ###
    def create_tabs(self):
        """Create tabs for Files, Downloads, and Settings"""
        # Create a notebook for the tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create the files tab
        self.files_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        self.downloads_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        
        # Add the tabs to the notebook
        self.notebook.add(self.files_tab, text="Encrypted Files")
        self.notebook.add(self.downloads_tab, text="Downloads")
        
        # Populate the tabs
        self.populate_files_tab()
        self.populate_downloads_tab()
        
    def populate_files_tab(self):
        """Populate the encrypted files tab"""
        if not self.files:
            self.show_no_files_screen(self.files_tab)
        else:
            self.show_file_list(self.files_tab)
            
    def populate_downloads_tab(self):
        """Populate the downloads tab with restored files"""
        # Create a frame for the downloads list
        downloads_frame = tk.Frame(self.downloads_tab, bg="#f0f0f0")
        downloads_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Look for restored files in the current directory
        restored_files = [f for f in os.listdir() if f.startswith("restored_")]
        
        if not restored_files:
            # Show message if no restored files found
            tk.Label(downloads_frame, text="No downloaded files found", 
                    font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            
            tk.Label(downloads_frame, text="Downloaded files will appear here after restoration", 
                    font=("Arial", 12), fg="#555555", bg="#f0f0f0").pack(pady=5)
        else:
            # Create a heading
            tk.Label(downloads_frame, text="Downloaded Files", 
                    font=("Arial", 14, "bold"), bg="#f0f0f0").pack(anchor="w", pady=(0, 10))
            
            # Create a scrollable list
            list_frame = tk.Frame(downloads_frame, bg="#f0f0f0")
            list_frame.pack(fill="both", expand=True)
            
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            
            downloads_list = tk.Listbox(list_frame, height=15, width=50, 
                                    yscrollcommand=scrollbar.set, font=("Arial", 11))
            downloads_list.pack(side="left", fill="both", expand=True, pady=10)
            scrollbar.config(command=downloads_list.yview)
            
            # Add header to the list
            downloads_list.insert(tk.END, f"{'Filename':<40} {'Size':<10} {'Date Modified':<20}")
            downloads_list.insert(tk.END, "-" * 70)
            
            # Add each file to the list
            for file in restored_files:
                file_path = os.path.join(os.getcwd(), file)
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size/1024/1024:.2f} MB" if file_size > 1024*1024 else f"{file_size/1024:.2f} KB"
                mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                
                downloads_list.insert(tk.END, f"{file:<40} {size_str:<10} {mod_time:<20}")
            
            # Add buttons for file operations
            btn_frame = tk.Frame(downloads_frame, bg="#f0f0f0")
            btn_frame.pack(fill="x", pady=10)
            
            def open_selected_file():
                selected = downloads_list.curselection()
                if selected:
                    idx = selected[0]
                    if idx <= 1:  # Skip header and separator
                        return
                        
                    file_name = restored_files[idx - 2]  # Adjust for header and separator
                    file_path = os.path.join(os.getcwd(), file_name)
                    
                    try:
                        # Open file with default system application
                        if os.name == 'nt':  # Windows
                            os.startfile(file_path)
                        elif os.name == 'posix':  # macOS or Linux
                            import subprocess
                            subprocess.Popen(['open', file_path] if sys.platform == 'darwin' else ['xdg-open', file_path])
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not open file: {str(e)}")
            
            def open_folder():
                try:
                    # Open file explorer to the current directory
                    if os.name == 'nt':  # Windows
                        os.startfile(os.getcwd())
                    elif os.name == 'posix':  # macOS or Linux
                        import subprocess
                        subprocess.Popen(['open', os.getcwd()] if sys.platform == 'darwin' else ['xdg-open', os.getcwd()])
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open folder: {str(e)}")
            
            def delete_selected_file():
                selected = downloads_list.curselection()
                if selected:
                    idx = selected[0]
                    if idx <= 1:  # Skip header and separator
                        return
                        
                    file_name = restored_files[idx - 2]  # Adjust for header and separator
                    
                    confirm = messagebox.askyesno("Delete File", 
                                            f"Are you sure you want to delete {file_name}?")
                    if confirm:
                        try:
                            os.remove(os.path.join(os.getcwd(), file_name))
                            messagebox.showinfo("Success", f"{file_name} has been deleted.")
                            # Refresh the downloads tab
                            for widget in self.downloads_tab.winfo_children():
                                widget.destroy()
                            self.populate_downloads_tab()
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not delete file: {str(e)}")
            
            # Create buttons
            tk.Button(btn_frame, text="Open Selected", command=open_selected_file, 
                    bg="#4CAF50", fg="white").pack(side="left", padx=5)
                    
            tk.Button(btn_frame, text="Open Folder", command=open_folder, 
                    bg="#2196F3", fg="white").pack(side="left", padx=5)
                    
            tk.Button(btn_frame, text="Delete Selected", command=delete_selected_file, 
                    bg="#f44336", fg="white").pack(side="left", padx=5)

    ###
    def __init__(self, root):
        self.root = root
        self.root.title("Uploaded Files")
        self.root.configure(bg="#f0f0f0")
        self.center_window(700, 500)
        
        # Get the list of encrypted files from main.py
        from main import list_encrypted_files
        self.files = list_encrypted_files()

        # Header
        header_frame = tk.Frame(self.root, bg="#333333", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="ByteScatter - File Manager", font=("Arial", 16, "bold"), 
                fg="white", bg="#333333").pack(pady=15)
        
        # Back button
        self.back_button = tk.Button(self.root, text="← Back", font=("Arial", 10), 
                                    command=self.return_to_home, bg="#d3d3d3")
        self.back_button.place(x=20, y=15, width=80, height=30)
        
        # Main content area
        self.content_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs for different functions
        self.create_tabs()
# This implementation shows how to use threading to prevent the GUI from freezing
# during lengthy operations like file encryption and cloud uploads
    
import threading
import queue

class BackgroundProcessor:
    """
    A utility class to handle background processing tasks while keeping the GUI responsive.
    This class manages a thread pool and task queue for processing operations.
    """
    
    def __init__(self, max_workers=3):
        """Initialize the background processor with a maximum number of worker threads"""
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.max_workers = max_workers
        self.workers = []
        self.running = False
    
    def start(self):
        """Start the background processing workers"""
        if self.running:
            return
        
        self.running = True
        
        # Create and start worker threads
        for _ in range(self.max_workers):
            thread = threading.Thread(target=self._worker_thread, daemon=True)
            thread.start()
            self.workers.append(thread)
    
    def stop(self):
        """Stop all background processing"""
        self.running = False
        # Clear the queue
        with self.task_queue.mutex:
            self.task_queue.queue.clear()
    
    def _worker_thread(self):
        """Worker thread that processes tasks from the queue"""
        while self.running:
            try:
                # Get a task from the queue with a timeout (allows checking running flag)
                task, args, kwargs, task_id = self.task_queue.get(timeout=0.5)
                
                try:
                    # Execute the task
                    result = task(*args, **kwargs)
                    self.result_queue.put((task_id, True, result))
                except Exception as e:
                    # If task fails, put the exception in the result queue
                    self.result_queue.put((task_id, False, e))
                finally:
                    # Mark the task as done
                    self.task_queue.task_done()
            
            except queue.Empty:
                # Queue is empty, just continue the loop
                continue
    
    def add_task(self, task, task_id, *args, **kwargs):
        """
        Add a task to the processing queue
        
        Args:
            task: The function to execute
            task_id: A unique identifier for the task (used for result tracking)
            *args, **kwargs: Arguments to pass to the task function
        """
        self.task_queue.put((task, args, kwargs, task_id))
    
    def check_results(self):
        """
        Check for completed tasks and return their results
        
        Returns:
            List of (task_id, success, result) tuples for completed tasks
        """
        results = []
        
        # Get all available results without blocking
        while True:
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
                self.result_queue.task_done()
            except queue.Empty:
                # No more results
                break
        
        return results


# Example of how to use the BackgroundProcessor in your GUI application:

# class UploadedFilesWindow:
#     def __init__(self, root):
#         # Initialize other attributes...
#         self.processor = BackgroundProcessor(max_workers=3)
#         self.processor.start()
        
#         # Set up a timer to check for completed background tasks
#         self.check_tasks()
    
#     def check_tasks(self):
#         """Periodically check for completed background tasks"""
#         # Process any completed tasks
#         results = self.processor.check_results()
#         for task_id, success, result in results:
#             self.handle_task_completion(task_id, success, result)
        
#         # Schedule the next check
#         self.root.after(100, self.check_tasks)
    
#     def handle_task_completion(self, task_id, success, result):
#         """Handle a completed background task"""
#         if task_id.startswith("download_"):
#             # Handle download completion
#             if success:
#                 file_id = task_id.replace("download_", "")
#                 messagebox.showinfo("Success", f"File downloaded and decrypted successfully!")
                
#                 # Update UI if needed
#                 # ...
#             else:
#                 # result contains the exception
#                 messagebox.showerror("Error", f"Failed to download file: {str(result)}")
        
#         elif task_id.startswith("upload_"):
#             # Handle upload completion
#             if success:
#                 messagebox.showinfo("Success", "File uploaded successfully!")
#             else:
#                 messagebox.showerror("Error", f"Failed to upload file: {str(result)}")
    
#     def download_file(self, file):
#         """Initiate a file download in the background"""
#         # Ask for password as before...
#         password = tk.simpledialog.askstring("Password Required", 
#                                            f"Enter password to decrypt {file['original_filename']}:", 
#                                            show="*")
#         if not password:
#             return
        
#         # Ask for save location as before...
#         output_path = filedialog.asksaveasfilename(...)
#         if not output_path:
#             return
        
#         # Show progress dialog
#         progress_window = tk.Toplevel(self.root)
#         # Configure progress window...
        
#         # Define download function
#         def download_task(file_id, password, output_path):
#             from main import decrypt_file_segments
#             return decrypt_file_segments(file_id, password, output_path, download_from_cloud=True)
        
#         # Add task to background processor
#         self.processor.add_task(
#             download_task, 
#             f"download_{file['file_id']}", 
#             file["file_id"], 
#             password, 
#             output_path
#         )
        
#         # Update progress bar periodically
#         def update_progress():
#             if not progress_window.winfo_exists():
#                 return
            
#             # Update progress - for a real implementation, you would need to
#             # modify decrypt_file_segments to report progress
#             progress_window.after(500, update_progress)
        
#         update_progress()
    
#     def cleanup(self):
        """Stop the background processor when the window is closed"""
        self.processor.stop()
###

class UploadedFilesWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("File Manager")
        self.root.configure(bg="#f0f0f0")
        self.center_window(770, 500)
        
        # Get the list of encrypted files from main.py
        from main import list_encrypted_files
        self.files = list_encrypted_files()

        # Header
        header_frame = tk.Frame(self.root, bg="#333333", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="ByteScatter - File Manager", font=("Arial", 16, "bold"), 
                 fg="white", bg="#333333").pack(pady=15)
        
        # Back button
        self.back_button = tk.Button(self.root, text="← Back", font=("Arial", 10), 
                                    command=self.return_to_home, bg="#d3d3d3")
        self.back_button.place(x=20, y=15, width=80, height=30)
        
        # Main content area
        self.content_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs for different functions
        self.create_tabs()

    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_tabs(self):
        """Create tabs for Files, Downloads, and Settings"""
        # Create a notebook for the tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create the files tab
        self.files_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        self.downloads_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        
        # Add the tabs to the notebook
        self.notebook.add(self.files_tab, text="Encrypted Files")
        self.notebook.add(self.downloads_tab, text="Downloads")
        
        # Populate the tabs
        self.populate_files_tab()
        self.populate_downloads_tab()
    
    def populate_files_tab(self):
        """Populate the encrypted files tab"""
        if not self.files:
            self.show_no_files_screen(self.files_tab)
        else:
            self.show_file_list(self.files_tab)
    
    def show_no_files_screen(self, parent_frame):
        """Display a screen if no files are present."""
        # Clear the frame
        for widget in parent_frame.winfo_children():
            widget.destroy()

        # No files message
        message_frame = tk.Frame(parent_frame, bg="#f0f0f0")
        message_frame.pack(expand=True, fill="both")
        
        tk.Label(message_frame, text="No encrypted files found", 
                font=("Arial", 14), bg="#f0f0f0").pack(pady=10)
        
        tk.Label(message_frame, text="Upload a file to get started", 
                font=("Arial", 12), fg="#555555", bg="#f0f0f0").pack(pady=5)
        
        # Upload button
        upload_button = tk.Button(message_frame, text="Upload a File", 
                                font=("Arial", 12), bg="#4CAF50", fg="white",
                                command=self.return_to_home)
        upload_button.pack(pady=20)
    
    def show_file_list(self, parent_frame):
        """Display the list of encrypted files with download and delete buttons."""
        # Clear the frame
        for widget in parent_frame.winfo_children():
            widget.destroy()

        # Create a canvas with scrollbar for the file list
        list_frame = tk.Frame(parent_frame, bg="#f0f0f0")
        list_frame.pack(fill="both", expand=True)
        
        # Add header for the list
        header = tk.Frame(list_frame, bg="#e0e0e0", height=40)
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(header, text="Filename", font=("Arial", 12, "bold"), 
                bg="#e0e0e0", width=25, anchor="w").pack(side="left", padx=10, pady=8)
        tk.Label(header, text="Date", font=("Arial", 12, "bold"), 
                bg="#e0e0e0", width=15, anchor="w").pack(side="left", padx=10, pady=8)
        tk.Label(header, text="Segments", font=("Arial", 12, "bold"), 
                bg="#e0e0e0", width=8, anchor="w").pack(side="left", padx=10, pady=8)
        
        # Canvas and scrollbar for file list
        canvas_frame = tk.Frame(list_frame)
        canvas_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        files_frame = tk.Frame(canvas, bg="#f0f0f0")
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.create_window((0, 0), window=files_frame, anchor="nw")
        files_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        for i, file in enumerate(self.files):
            row_bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            file_frame = tk.Frame(files_frame, bg=row_bg, height=50)
            file_frame.pack(fill="x", pady=1)
            
            # Extract date from creation_date (just date part)
            date_str = file['creation_date'].split(' ')[0] if 'creation_date' in file else "N/A"
            
            # File info
            tk.Label(file_frame, text=file['original_filename'], 
                    font=("Arial", 11), bg=row_bg, width=25, anchor="w").pack(side="left", padx=10, pady=12)
            tk.Label(file_frame, text=date_str, 
                    font=("Arial", 11), bg=row_bg, width=15, anchor="w").pack(side="left", padx=10, pady=12)
            tk.Label(file_frame, text=str(file['segment_count']), 
                    font=("Arial", 11), bg=row_bg, width=8, anchor="w").pack(side="left", padx=10, pady=12)
            
            # Action buttons
            download_btn = tk.Button(file_frame, text="Download", bg="#2196F3", fg="white", 
                                    command=lambda f=file: self.download_file(f))
            download_btn.pack(side="right", padx=5, pady=5)
            
            delete_btn = tk.Button(file_frame, text="Delete", bg="#f44336", fg="white",
                                command=lambda f=file: self.delete_file(f))
            delete_btn.pack(side="right", padx=5, pady=5)
            
            # Add info button
            info_btn = tk.Button(file_frame, text="Info", bg="#FF9800", fg="white",
                               command=lambda f=file: self.show_file_info(f))
            info_btn.pack(side="right", padx=5, pady=5)
    
    def populate_downloads_tab(self):
        """Populate the downloads tab with restored files"""
        # Create a frame for the downloads list
        downloads_frame = tk.Frame(self.downloads_tab, bg="#f0f0f0")
        downloads_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Look for restored files in the current directory
        restored_files = [f for f in os.listdir() if f.startswith("restored_")]
        
        if not restored_files:
            # Show message if no restored files found
            tk.Label(downloads_frame, text="No downloaded files found", 
                    font=("Arial", 14), bg="#f0f0f0").pack(pady=20)
            
            tk.Label(downloads_frame, text="Downloaded files will appear here after restoration", 
                    font=("Arial", 12), fg="#555555", bg="#f0f0f0").pack(pady=5)
        else:
            # Create a heading
            tk.Label(downloads_frame, text="Downloaded Files", 
                    font=("Arial", 14, "bold"), bg="#f0f0f0").pack(anchor="w", pady=(0, 10))
            
            # Create a scrollable list
            list_frame = tk.Frame(downloads_frame, bg="#f0f0f0")
            list_frame.pack(fill="both", expand=True)
            
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            
            downloads_list = tk.Listbox(list_frame, height=15, width=50, 
                                    yscrollcommand=scrollbar.set, font=("Arial", 11))
            downloads_list.pack(side="left", fill="both", expand=True, pady=10)
            scrollbar.config(command=downloads_list.yview)
            
            # Add header to the list
            downloads_list.insert(tk.END, f"{'Filename':<40} {'Size':<10} {'Date Modified':<20}")
            downloads_list.insert(tk.END, "-" * 70)
            
            # Add each file to the list
            for file in restored_files:
                file_path = os.path.join(os.getcwd(), file)
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size/1024/1024:.2f} MB" if file_size > 1024*1024 else f"{file_size/1024:.2f} KB"
                mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                
                downloads_list.insert(tk.END, f"{file:<40} {size_str:<10} {mod_time:<20}")
            
            # Add buttons for file operations
            btn_frame = tk.Frame(downloads_frame, bg="#f0f0f0")
            btn_frame.pack(fill="x", pady=10)
            
            def open_selected_file():
                selected = downloads_list.curselection()
                if selected:
                    idx = selected[0]
                    if idx <= 1:  # Skip header and separator
                        return
                        
                    file_name = restored_files[idx - 2]  # Adjust for header and separator
                    file_path = os.path.join(os.getcwd(), file_name)
                    
                    try:
                        # Open file with default system application
                        if os.name == 'nt':  # Windows
                            os.startfile(file_path)
                        elif os.name == 'posix':  # macOS or Linux
                            import subprocess
                            subprocess.Popen(['open', file_path] if sys.platform == 'darwin' else ['xdg-open', file_path])
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not open file: {str(e)}")
            
            def open_folder():
                try:
                    # Open file explorer to the current directory
                    if os.name == 'nt':  # Windows
                        os.startfile(os.getcwd())
                    elif os.name == 'posix':  # macOS or Linux
                        import subprocess
                        subprocess.Popen(['open', os.getcwd()] if sys.platform == 'darwin' else ['xdg-open', os.getcwd()])
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open folder: {str(e)}")
            
            def delete_selected_file():
                selected = downloads_list.curselection()
                if selected:
                    idx = selected[0]
                    if idx <= 1:  # Skip header and separator
                        return
                        
                    file_name = restored_files[idx - 2]  # Adjust for header and separator
                    
                    confirm = messagebox.askyesno("Delete File", 
                                               f"Are you sure you want to delete {file_name}?")
                    if confirm:
                        try:
                            os.remove(os.path.join(os.getcwd(), file_name))
                            messagebox.showinfo("Success", f"{file_name} has been deleted.")
                            # Refresh the downloads tab
                            for widget in self.downloads_tab.winfo_children():
                                widget.destroy()
                            self.populate_downloads_tab()
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not delete file: {str(e)}")
            
            # Create buttons
            tk.Button(btn_frame, text="Open Selected", command=open_selected_file, 
                    bg="#4CAF50", fg="white").pack(side="left", padx=5)
                    
            tk.Button(btn_frame, text="Open Folder", command=open_folder, 
                    bg="#2196F3", fg="white").pack(side="left", padx=5)
                    
            tk.Button(btn_frame, text="Delete Selected", command=delete_selected_file, 
                    bg="#f44336", fg="white").pack(side="left", padx=5)
    
    def download_file(self, file):
        """Trigger the download process with password prompt and output location selection."""
        # Ask for password
        password = tk.simpledialog.askstring("Password Required", 
                                           f"Enter password to decrypt {file['original_filename']}:", 
                                           show="*")
        if not password:
            return  # User cancelled
        
        # Ask for download location
        default_filename = f"restored_{file['original_filename']}"
        output_path = filedialog.asksaveasfilename(
            title="Save Restored File As",
            initialfile=default_filename,
            filetypes=[("All Files", "*.*")]
        )
        
        if not output_path:
            return  # User cancelled
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Downloading")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(progress_window, text="Downloading and decrypting...", 
                font=("Arial", 12)).pack(pady=10)
        
        progress_text = tk.Label(progress_window, text="Please wait...", 
                               font=("Arial", 10))
        progress_text.pack(pady=5)
        
        # Update UI
        self.root.update()
        
        # Start download and decryption
        try:
            from main import decrypt_file_segments
            success = decrypt_file_segments(file["file_id"], password, output_path, download_from_cloud=True)
            
            # Close progress window
            progress_window.destroy()
            
            if success:
                messagebox.showinfo("Success", 
                                  f"{file['original_filename']} has been successfully restored to:\n{output_path}")
                
                # Refresh the downloads tab
                for widget in self.downloads_tab.winfo_children():
                    widget.destroy()
                self.populate_downloads_tab()
            else:
                messagebox.showerror("Error", 
                                   "Failed to download and decrypt the file. Please check your password and try again.")
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Error", f"An error occurred during download: {str(e)}")

    def delete_file(self, file):
        """Delete a file after confirmation."""
        confirm = messagebox.askyesno("Delete File", 
                                    f"Are you sure you want to delete {file['original_filename']}?\n\nThis action cannot be undone.")
        if confirm:
            try:
                from main import delete_encrypted_file
                success = delete_encrypted_file(file["file_id"])
                
                if success:
                    messagebox.showinfo("Success", f"{file['original_filename']} has been deleted.")
                    # Refresh the file list
                    from main import list_encrypted_files
                    self.files = list_encrypted_files()
                    if self.files:
                        self.populate_files_tab()
                    else:
                        self.show_no_files_screen(self.files_tab)
                else:
                    messagebox.showerror("Error", "Failed to delete the file completely.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting: {str(e)}")
    
    def show_file_info(self, file):
        """Display detailed information about the file and its segments."""
        info_window = tk.Toplevel(self.root)
        info_window.title(f"File Information: {file['original_filename']}")
        info_window.geometry("600x400")
        info_window.transient(self.root)
        
        # Header
        tk.Label(info_window, text="File Details", font=("Arial", 14, "bold")).pack(pady=10)
        
        # File info frame
        info_frame = tk.Frame(info_window)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        # Add file details
        tk.Label(info_frame, text="File ID:", font=("Arial", 11, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(info_frame, text=file['file_id'], font=("Arial", 11)).grid(row=0, column=1, sticky="w", pady=5)
        
        tk.Label(info_frame, text="Original Filename:", font=("Arial", 11, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(info_frame, text=file['original_filename'], font=("Arial", 11)).grid(row=1, column=1, sticky="w", pady=5)
        
        tk.Label(info_frame, text="Number of Segments:", font=("Arial", 11, "bold"), anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        tk.Label(info_frame, text=str(file['segment_count']), font=("Arial", 11)).grid(row=2, column=1, sticky="w", pady=5)
        
        tk.Label(info_frame, text="Created:", font=("Arial", 11, "bold"), anchor="w").grid(row=3, column=0, sticky="w", pady=5)
        tk.Label(info_frame, text=file['creation_date'], font=("Arial", 11)).grid(row=3, column=1, sticky="w", pady=5)
        
        # Check file availability
        try:
            from main import verify_file_availability
            status = verify_file_availability(file['file_id'])
            
            # Segment availability info
            tk.Label(info_window, text="Segment Availability", font=("Arial", 12, "bold")).pack(pady=(20, 10))
            
            availability_frame = tk.Frame(info_window)
            availability_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Create a canvas with scrollbar
            canvas = tk.Canvas(availability_frame)
            scrollbar = tk.Scrollbar(availability_frame, orient="vertical", command=canvas.yview)
            segments_frame = tk.Frame(canvas)
            
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.create_window((0, 0), window=segments_frame, anchor="nw")
            segments_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            # Status heading
            tk.Label(segments_frame, text=f"Status: {status['status'].capitalize()}", 
                   font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=5)
            
            if 'segments' in status:
                # Column headers
                tk.Label(segments_frame, text="Segment", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5)
                tk.Label(segments_frame, text="Local", font=("Arial", 10, "bold")).grid(row=1, column=1, padx=5, pady=5)
                tk.Label(segments_frame, text="Cloud", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=5, pady=5)
                
                # Add segment rows
                for i, segment in enumerate(status['segments']):
                    row = i + 2
                    tk.Label(segments_frame, text=f"Segment {segment['segment_index']}").grid(row=row, column=0, padx=5, pady=2)
                    
                    # Local availability
                    local_text = "✓" if segment['local_available'] else "✗"
                    local_color = "green" if segment['local_available'] else "red"
                    tk.Label(segments_frame, text=local_text, fg=local_color).grid(row=row, column=1, padx=5, pady=2)
                    
                    # Cloud availability
                    cloud_text = "✓" if segment['cloud_available'] else "✗"
                    cloud_color = "green" if segment['cloud_available'] else "red"
                    cloud_services = ", ".join(segment['cloud_services']) if segment['cloud_available'] else "None"
                    tk.Label(segments_frame, text=f"{cloud_text} ({cloud_services})", fg=cloud_color).grid(row=row, column=2, padx=5, pady=2)
        
        except Exception as e:
            tk.Label(info_window, text=f"Error retrieving segment info: {str(e)}", 
                   fg="red").pack(pady=10)
        
        # Close button
        tk.Button(info_window, text="Close", command=info_window.destroy).pack(pady=20)
    
    def return_to_home(self):
        """Return to the main screen."""
        self.root.destroy()
        root = TkinterDnD.Tk()
        app = EncryptionApp(root)
        root.mainloop()

###
class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("ByteScatter Settings")
        self.center_window(670, 400)
        self.root.configure(bg="#f0f0f0")
        
        # Load current settings
        from main import load_settings
        self.settings = load_settings()
        
        # Header
        header_frame = tk.Frame(self.root, bg="#333333", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="Settings", font=("Arial", 16, "bold"), 
                 fg="white", bg="#333333").pack(pady=15)
        
        # Back button
        self.back_button = tk.Button(self.root, text="← Back", font=("Arial", 10), 
                                    command=self.go_back, bg="#d3d3d3")
        self.back_button.place(x=20, y=15, width=80, height=30)
        
        # Main content frame
        self.content_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        self.content_frame.pack(fill="both", expand=True)
        
        # API Key Settings
        api_frame = tk.LabelFrame(self.content_frame, text="Cloud Storage API Keys", 
                                 font=("Arial", 12, "bold"), bg="#f0f0f0", padx=15, pady=15)
        api_frame.pack(fill="x", pady=10)
        
        # Dropbox API Key
        tk.Label(api_frame, text="Dropbox API Key:", font=("Arial", 11), 
                bg="#f0f0f0", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        
        self.dropbox_var = tk.StringVar()
        self.dropbox_var.set(self.mask_api_key(self.settings.get("Dropbox", "")))
        
        dropbox_entry = tk.Entry(api_frame, textvariable=self.dropbox_var, width=30, show="•")
        dropbox_entry.grid(row=0, column=1, padx=10, pady=5)
        
        show_dropbox_btn = tk.Button(api_frame, text="👁", width=3, 
                                    command=lambda: self.toggle_show_hide(dropbox_entry))
        show_dropbox_btn.grid(row=0, column=2, padx=5, pady=5)
        
        edit_dropbox_btn = tk.Button(api_frame, text="Edit", width=6, 
                                    command=lambda: self.edit_api_key("Dropbox"))
        edit_dropbox_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Google Drive API Key
        tk.Label(api_frame, text="Google Drive API Key:", font=("Arial", 11), 
                bg="#f0f0f0", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        
        self.google_var = tk.StringVar()
        self.google_var.set(self.mask_api_key(self.settings.get("GoogleDrive", "")))
        
        google_entry = tk.Entry(api_frame, textvariable=self.google_var, width=30, show="•")
        google_entry.grid(row=1, column=1, padx=10, pady=5)
        
        show_google_btn = tk.Button(api_frame, text="👁", width=3, 
                                   command=lambda: self.toggle_show_hide(google_entry))
        show_google_btn.grid(row=1, column=2, padx=5, pady=5)
        
        edit_google_btn = tk.Button(api_frame, text="Edit", width=6, 
                                   command=lambda: self.edit_api_key("GoogleDrive"))
        edit_google_btn.grid(row=1, column=3, padx=5, pady=5)
        
        # OneDrive API Key
        tk.Label(api_frame, text="OneDrive API Key:", font=("Arial", 11), 
                bg="#f0f0f0", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        
        self.onedrive_var = tk.StringVar()
        self.onedrive_var.set(self.mask_api_key(self.settings.get("OneDrive", "")))
        
        onedrive_entry = tk.Entry(api_frame, textvariable=self.onedrive_var, width=30, show="•")
        onedrive_entry.grid(row=2, column=1, padx=10, pady=5)
        
        show_onedrive_btn = tk.Button(api_frame, text="👁", width=3, 
                                     command=lambda: self.toggle_show_hide(onedrive_entry))
        show_onedrive_btn.grid(row=2, column=2, padx=5, pady=5)
        
        edit_onedrive_btn = tk.Button(api_frame, text="Edit", width=6, 
                                     command=lambda: self.edit_api_key("OneDrive"))
        edit_onedrive_btn.grid(row=2, column=3, padx=5, pady=5)
        
        # Advanced settings section
        adv_frame = tk.LabelFrame(self.content_frame, text="Advanced Settings", 
                                 font=("Arial", 12, "bold"), bg="#f0f0f0", padx=15, pady=15)
        adv_frame.pack(fill="x", pady=10)
        
        # Output directory setting
        tk.Label(adv_frame, text="Default Output Directory:", font=("Arial", 11), 
                bg="#f0f0f0", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        
        # Default value is "output" in the current working directory
        self.output_dir_var = tk.StringVar()
        self.output_dir_var.set(os.path.abspath("output"))
        
        output_entry = tk.Entry(adv_frame, textvariable=self.output_dir_var, width=30)
        output_entry.grid(row=0, column=1, padx=10, pady=5)
        
        browse_btn = tk.Button(adv_frame, text="Browse", width=6, 
                              command=self.browse_output_dir)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Test connectivity button
        test_conn_btn = tk.Button(self.content_frame, text="Test Cloud Connectivity", font=("Arial", 11),
                                 bg="#2196F3", fg="white", command=self.test_connectivity)
        test_conn_btn.pack(pady=15)
        
        # Save settings button
        save_btn = tk.Button(self.content_frame, text="Save Settings", font=("Arial", 11),
                           bg="#4CAF50", fg="white", command=self.save_settings)
        save_btn.pack(pady=5)
    
    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def mask_api_key(self, key):
        """Mask API key for display in UI"""
        if not key or key == "000":
            return "Not set"
        if len(key) <= 6:
            return "*" * len(key)
        return key[:3] + "*" * (len(key) - 6) + key[-3:]
    
    def toggle_show_hide(self, entry_widget):
        """Toggle between showing and hiding the entry text"""
        if entry_widget.cget('show') == '•':
            entry_widget.config(show='')
        else:
            entry_widget.config(show='•')
    
    def edit_api_key(self, service_name):
        """Open a dialog to edit the API key for a service"""
        current_value = self.settings.get(service_name, "")
        
        # If the value is masked, clear it for editing
        if service_name == "Dropbox" and self.dropbox_var.get().startswith("*"):
            current_value = current_value if current_value != "000" else ""
        elif service_name == "GoogleDrive" and self.google_var.get().startswith("*"):
            current_value = current_value if current_value != "000" else ""
        elif service_name == "OneDrive" and self.onedrive_var.get().startswith("*"):
            current_value = current_value if current_value != "000" else ""
        
        # Create a dialog for editing
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title(f"Edit {service_name} API Key")
        edit_dialog.geometry("400x180")
        edit_dialog.transient(self.root)
        edit_dialog.grab_set()
        
        tk.Label(edit_dialog, text=f"Enter {service_name} API Key:", 
                font=("Arial", 12)).pack(pady=(20, 10))
        
        api_var = tk.StringVar()
        api_var.set(current_value)
        
        entry_frame = tk.Frame(edit_dialog)
        entry_frame.pack(pady=10)
        
        api_entry = tk.Entry(entry_frame, textvariable=api_var, width=40, show="•")
        api_entry.pack(side="left", padx=5)
        
        show_btn = tk.Button(entry_frame, text="👁", width=3, 
                           command=lambda: self.toggle_show_hide(api_entry))
        show_btn.pack(side="left")
        
        info_text = "Leave empty or enter '000' to disable this service."
        tk.Label(edit_dialog, text=info_text, fg="gray").pack(pady=5)
        
        # Buttons frame
        btn_frame = tk.Frame(edit_dialog)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="Cancel", command=edit_dialog.destroy, width=10).pack(side="left", padx=10)
        
        def save_key():
            new_value = api_var.get().strip()
            # Use "000" as a marker for disabled service
            if not new_value:
                new_value = "000"
            
            self.settings[service_name] = new_value
            
            # Update displayed values
            if service_name == "Dropbox":
                self.dropbox_var.set(self.mask_api_key(new_value))
            elif service_name == "GoogleDrive":
                self.google_var.set(self.mask_api_key(new_value))
            elif service_name == "OneDrive":
                self.onedrive_var.set(self.mask_api_key(new_value))
            
            edit_dialog.destroy()
        
        tk.Button(btn_frame, text="Save", command=save_key, width=10, 
                 bg="#4CAF50", fg="white").pack(side="left")
    
    def browse_output_dir(self):
        """Open a dialog to select the output directory"""
        current_dir = self.output_dir_var.get()
        dir_name = filedialog.askdirectory(
            initialdir=current_dir if os.path.exists(current_dir) else os.getcwd(),
            title="Select Output Directory"
        )
        if dir_name:
            self.output_dir_var.set(dir_name)
    
    def test_connectivity(self):
        """Test connectivity to cloud services"""
        # Create progress dialog
        progress = tk.Toplevel(self.root)
        progress.title("Testing Cloud Connectivity")
        progress.geometry("300x200")
        progress.transient(self.root)
        progress.grab_set()
        
        tk.Label(progress, text="Testing cloud connections...", 
                font=("Arial", 12)).pack(pady=10)
        
        results_frame = tk.Frame(progress)
        results_frame.pack(fill="x", padx=20, pady=10)
        
        # Initialize status labels
        dropbox_label = tk.Label(results_frame, text="Dropbox: Testing...", 
                               font=("Arial", 11))
        dropbox_label.grid(row=0, column=0, sticky="w", pady=5)
        
        google_label = tk.Label(results_frame, text="Google Drive: Testing...", 
                              font=("Arial", 11))
        google_label.grid(row=1, column=0, sticky="w", pady=5)
        
        onedrive_label = tk.Label(results_frame, text="OneDrive: Testing...", 
                                font=("Arial", 11))
        onedrive_label.grid(row=2, column=0, sticky="w", pady=5)
        
        # Update the UI
        self.root.update()
        
        # Test each service
        # Dropbox
        try:
            dropbox_key = self.settings.get("Dropbox", "")
            if dropbox_key and dropbox_key != "000":
                # Import the needed function to test Dropbox
                from dropbox_helper import list_files
                # If we get any result (even empty list), connection works
                files = list_files()
                if files is not None:
                    dropbox_label.config(text="Dropbox: ✓ Connected", fg="green")
                else:
                    dropbox_label.config(text="Dropbox: ✗ Connection failed", fg="red")
            else:
                dropbox_label.config(text="Dropbox: Not configured", fg="gray")
        except Exception as e:
            dropbox_label.config(text=f"Dropbox: ✗ Error: {str(e)[:30]}", fg="red")
        
        self.root.update()
        
        # Google Drive - simulation since we don't have full implementation
        google_key = self.settings.get("GoogleDrive", "")
        if google_key and google_key != "000":
            # Here you would test actual Google Drive connection
            # For now, just show as not implemented
            google_label.config(text="Google Drive: ⚠ Not implemented", fg="#FFA500")
        else:
            google_label.config(text="Google Drive: Not configured", fg="gray")
        
        self.root.update()
        
        # OneDrive - simulation since we don't have full implementation
        onedrive_key = self.settings.get("OneDrive", "")
        if onedrive_key and onedrive_key != "000":
            # Here you would test actual OneDrive connection
            # For now, just show as not implemented
            onedrive_label.config(text="OneDrive: ⚠ Not implemented", fg="#FFA500")
        else:
            onedrive_label.config(text="OneDrive: Not configured", fg="gray")
        
        # Add close button
        tk.Button(progress, text="Close", command=progress.destroy).pack(pady=10)
    
    def save_settings(self):
        """Save the current settings"""
        try:
            # Import the save function from main
            from main import save_settings
            save_settings(self.settings)
            
            # Create output directory if it doesn't exist
            output_dir = self.output_dir_var.get()
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def go_back(self):
        """Return to the main screen"""
        self.root.destroy()
        root = TkinterDnD.Tk()
        app = EncryptionApp(root)
        root.mainloop()



class HelpWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("ByteScatter Help")
        self.center_window(700, 500)
        self.root.configure(bg="#f0f0f0")
        
        # Header
        header_frame = tk.Frame(self.root, bg="#333333", height=60)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="ByteScatter Help Guide", font=("Arial", 16, "bold"), 
                 fg="white", bg="#333333").pack(pady=15)
        
        # Back button
        self.back_button = tk.Button(self.root, text="← Back", font=("Arial", 10), 
                                    command=self.go_back, bg="#d3d3d3")
        self.back_button.place(x=20, y=15, width=80, height=30)
        
        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs
        overview_tab = tk.Frame(notebook, bg="#f9f9f9")
        usage_tab = tk.Frame(notebook, bg="#f9f9f9")
        cloud_tab = tk.Frame(notebook, bg="#f9f9f9")
        troubleshooting_tab = tk.Frame(notebook, bg="#f9f9f9")
        about_tab = tk.Frame(notebook, bg="#f9f9f9")
        
        notebook.add(overview_tab, text="Overview")
        notebook.add(usage_tab, text="Usage Guide")
        notebook.add(cloud_tab, text="Cloud Storage")
        notebook.add(troubleshooting_tab, text="Troubleshooting")
        notebook.add(about_tab, text="About")
        
        # Overview tab content
        self.create_overview_tab(overview_tab)
        
        # Usage Guide tab content
        self.create_usage_tab(usage_tab)
        
        # Cloud Storage tab content
        self.create_cloud_tab(cloud_tab)
        
        # Troubleshooting tab content
        self.create_troubleshooting_tab(troubleshooting_tab)
        
        # About tab content
        self.create_about_tab(about_tab)
    
    def center_window(self, width, height):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_overview_tab(self, tab):
        # Create a frame with scrollbar
        frame = tk.Frame(tab, bg="#f9f9f9")
        frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(frame, bg="#f9f9f9")
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="#f9f9f9", padx=15, pady=15)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Add content
        tk.Label(content_frame, text="What is ByteScatter?", font=("Arial", 14, "bold"), 
                bg="#f9f9f9").pack(anchor="w", pady=(0, 10))
        
        description = (
            "ByteScatter is a secure file management tool that splits your files into multiple "
            "encrypted segments and distributes them across different cloud storage services. "
            "This approach provides several security benefits:\n\n"
            "• No single cloud provider has your complete file\n"
            "• All segments are encrypted using strong encryption\n"
            "• Your file remains accessible even if one cloud service is down\n"
            "• You control the encryption keys, not the cloud providers\n\n"
            "ByteScatter is ideal for sensitive documents, backup storage, and any scenario "
            "where you want to enhance the security and availability of your files."
        )
        
        text_widget = tk.Text(content_frame, wrap="word", height=10, width=70, 
                            bg="#f9f9f9", bd=0, padx=5, pady=5)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", description)
        text_widget.config(state="disabled")  # Make read-only
        
        # Key features section
        tk.Label(content_frame, text="Key Features", font=("Arial", 14, "bold"), 
                bg="#f9f9f9").pack(anchor="w", pady=(10, 10))
        
        features_frame = tk.Frame(content_frame, bg="#f9f9f9")
        features_frame.pack(fill="x", pady=5)
        
        features = [
            "File Splitting: Divide files into multiple segments",
            "Strong Encryption: Protect each segment with AES-256 encryption",
            "Cloud Distribution: Spread segments across multiple cloud services",
            "Easy Recovery: Combine segments to restore your original file",
            "Secure Deletion: Securely remove files when no longer needed",
            "User-Friendly Interface: Simple drag-and-drop functionality"
        ]
        
        for i, feature in enumerate(features):
            feature_frame = tk.Frame(features_frame, bg="#f9f9f9")
            feature_frame.pack(fill="x", pady=3)
            
            tk.Label(feature_frame, text="•", font=("Arial", 12), 
                    bg="#f9f9f9").pack(side="left", padx=(5, 2))
            tk.Label(feature_frame, text=feature, font=("Arial", 11), 
                    bg="#f9f9f9", justify="left", anchor="w").pack(side="left", fill="x")
    
    def create_usage_tab(self, tab):
        # Create a frame with scrollbar
        frame = tk.Frame(tab, bg="#f9f9f9")
        frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(frame, bg="#f9f9f9")
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="#f9f9f9", padx=15, pady=15)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Add content - Step by step guides
        tk.Label(content_frame, text="How to Use ByteScatter", font=("Arial", 14, "bold"), 
                bg="#f9f9f9").pack(anchor="w", pady=(0, 10))
        
        # Uploading a file
        section_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        section_frame.pack(fill="x", pady=5)
        
        tk.Label(section_frame, text="Uploading and Encrypting a File", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        steps = [
            "1. From the main screen, drag and drop your file onto the drop area, or click to browse",
            "2. Enter the number of segments you want to split the file into (2 or more recommended)",
            "3. Create a strong password to encrypt your file - REMEMBER THIS PASSWORD!",
            "4. Click 'Split' to process your file",
            "5. Choose whether to upload segments to cloud services or keep them locally",
            "6. When complete, you'll see a success screen with segment information"
        ]
        
        for step in steps:
            tk.Label(section_frame, text=step, font=("Arial", 11), 
                    bg="#f1f1f1", justify="left", anchor="w").pack(anchor="w", pady=2)
        
        # Downloading a file
        section_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        section_frame.pack(fill="x", pady=10)
        
        tk.Label(section_frame, text="Retrieving and Decrypting a File", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        steps = [
            "1. Click 'View Encrypted Files' from the main screen",
            "2. Find your file in the list and click 'Download'",
            "3. Enter the password you used to encrypt the file",
            "4. Choose where to save the restored file",
            "5. Wait for the download and decryption to complete",
            "6. Your original file will be saved to the location you specified"
        ]
        
        for step in steps:
            tk.Label(section_frame, text=step, font=("Arial", 11), 
                    bg="#f1f1f1", justify="left", anchor="w").pack(anchor="w", pady=2)
        
        # Password guidelines
        section_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        section_frame.pack(fill="x", pady=10)
        
        tk.Label(section_frame, text="Password Guidelines", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        password_text = (
            "Your password is critical for security and cannot be recovered if lost. "
            "For maximum security:\n"
            "• Use at least 12 characters\n"
            "• Include uppercase, lowercase, numbers, and symbols\n"
            "• Don't use easily guessable information\n"
            "• Store your password in a secure password manager\n"
            "• IMPORTANT: If you lose your password, your file CANNOT be recovered!"
        )
        
        password_widget = tk.Text(section_frame, wrap="word", height=6, width=60, 
                                bg="#f1f1f1", bd=0, padx=5, pady=5)
        password_widget.pack(fill="x")
        password_widget.insert("1.0", password_text)
        password_widget.config(state="disabled")  # Make read-only
    
    def create_cloud_tab(self, tab):
        # Create a frame with scrollbar
        frame = tk.Frame(tab, bg="#f9f9f9")
        frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(frame, bg="#f9f9f9")
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="#f9f9f9", padx=15, pady=15)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Add content
        tk.Label(content_frame, text="Cloud Storage Integration", font=("Arial", 14, "bold"), 
                bg="#f9f9f9").pack(anchor="w", pady=(0, 10))
        
        cloud_text = (
            "ByteScatter can distribute your encrypted file segments across multiple cloud "
            "storage services. This provides redundancy and ensures no single service has "
            "your complete file. To use cloud storage, you'll need to configure API keys "
            "in the Settings."
        )
        
        text_widget = tk.Text(content_frame, wrap="word", height=4, width=70, 
                            bg="#f9f9f9", bd=0, padx=5, pady=5)
        text_widget.pack(fill="x")
        text_widget.insert("1.0", cloud_text)
        text_widget.config(state="disabled")  # Make read-only
        
        # Dropbox section
        service_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        service_frame.pack(fill="x", pady=10)
        
        tk.Label(service_frame, text="Dropbox Integration", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        dropbox_text = (
            "ByteScatter uses Dropbox's API to securely store and retrieve file segments.\n\n"
            "To set up Dropbox integration:\n"
            "1. Go to Settings → Cloud Storage API Keys\n"
            "2. Click 'Edit' next to Dropbox API Key\n"
            "3. Enter your Dropbox API key\n"
            "4. Click 'Save Settings'\n\n"
            "You can obtain a Dropbox API key by creating an app in the Dropbox Developer Console."
        )
        
        dropbox_widget = tk.Text(service_frame, wrap="word", height=8, width=60, 
                                bg="#f1f1f1", bd=0, padx=5, pady=5)
        dropbox_widget.pack(fill="x")
        dropbox_widget.insert("1.0", dropbox_text)
        dropbox_widget.config(state="disabled")  # Make read-only
        
        # Future Integrations
        service_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        service_frame.pack(fill="x", pady=10)
        
        tk.Label(service_frame, text="Other Cloud Services", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        other_text = (
            "ByteScatter is designed to support multiple cloud services. While Dropbox "
            "integration is fully implemented, Google Drive and OneDrive integration are "
            "planned for future releases.\n\n"
            "When multiple services are configured, ByteScatter will distribute file segments "
            "evenly across all available services."
        )
        
        other_widget = tk.Text(service_frame, wrap="word", height=5, width=60, 
                            bg="#f1f1f1", bd=0, padx=5, pady=5)
        other_widget.pack(fill="x")
        other_widget.insert("1.0", other_text)
        other_widget.config(state="disabled")  # Make read-only
    
    def create_troubleshooting_tab(self, tab):
        # Create a frame with scrollbar
        frame = tk.Frame(tab, bg="#f9f9f9")
        frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(frame, bg="#f9f9f9")
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="#f9f9f9", padx=15, pady=15)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Add content - Common issues and solutions
        tk.Label(content_frame, text="Troubleshooting Guide", font=("Arial", 14, "bold"), 
                bg="#f9f9f9").pack(anchor="w", pady=(0, 10))
        
        # Common issues section
        issues = [
            {
                "title": "Unable to Decrypt File",
                "description": (
                    "If you can't decrypt your file, check:\n"
                    "• Verify you're using the correct password\n"
                    "• Ensure all file segments are available (check File Info)\n"
                    "• Try downloading from cloud if local segments are missing\n"
                    "• Check if any segments are corrupted\n\n"
                    "Note: If you've forgotten your password, there is NO way to recover the file."
                )
            },
            {
                "title": "Cloud Upload/Download Issues",
                "description": (
                    "If you're having issues with cloud storage:\n"
                    "• Verify your API keys are correctly entered\n"
                    "• Check your internet connection\n"
                    "• Test cloud connectivity in Settings\n"
                    "• Ensure your cloud account has sufficient storage space\n"
                    "• Verify the cloud service is operational\n\n"
                    "You can try the 'Info' button on a file to check segment availability."
                )
            },
            {
                "title": "Application Performance Issues",
                "description": (
                    "If ByteScatter is running slowly:\n"
                    "• Avoid processing extremely large files on systems with limited memory\n"
                    "• For large files, use fewer segments (large number of splits increases overhead)\n"
                    "• Close other memory-intensive applications\n"
                    "• Ensure your computer meets the minimum system requirements\n"
                    "• Check that you have sufficient disk space for temporary files"
                )
            },
            {
                "title": "Missing or Corrupt Segments",
                "description": (
                    "If segments are missing or corrupted:\n"
                    "• Use the 'Info' button to check segment status\n"
                    "• If segments are in the cloud but not locally, try downloading the file again\n"
                    "• If segments are corrupt, you may need to restore from a backup\n"
                    "• If using multiple cloud services, check if any service is down\n\n"
                    "ByteScatter stores segment information in a database. If this database is damaged, file recovery may be difficult."
                )
            }
        ]
        
        for issue in issues:
            issue_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
            issue_frame.pack(fill="x", pady=10)
            
            tk.Label(issue_frame, text=issue["title"], font=("Arial", 12, "bold"), 
                    bg="#f1f1f1").pack(anchor="w")
            
            issue_widget = tk.Text(issue_frame, wrap="word", height=7, width=60, 
                                bg="#f1f1f1", bd=0, padx=5, pady=5)
            issue_widget.pack(fill="x")
            issue_widget.insert("1.0", issue["description"])
            issue_widget.config(state="disabled")  # Make read-only
    
    def create_about_tab(self, tab):
        # Create a frame with scrollbar
        frame = tk.Frame(tab, bg="#f9f9f9")
        frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(frame, bg="#f9f9f9")
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="#f9f9f9", padx=15, pady=15)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Add content
        tk.Label(content_frame, text="About ByteScatter", font=("Arial", 14, "bold"), 
                bg="#f9f9f9").pack(anchor="w", pady=(0, 10))
        
        about_text = (
            "ByteScatter is a secure file management application designed to enhance the "
            "privacy and security of your important files through encryption and distribution "
            "across multiple storage locations.\n\n"
            "Version: 1.0.0\n"
            "License: MIT License\n\n"
            "ByteScatter uses strong AES-256 encryption and follows best practices for secure "
            "file handling. All encryption is done locally on your device - your encryption keys "
            "are never sent to cloud services."
        )
        
        text_widget = tk.Text(content_frame, wrap="word", height=8, width=70, 
                            bg="#f9f9f9", bd=0, padx=5, pady=5)
        text_widget.pack(fill="x")
        text_widget.insert("1.0", about_text)
        text_widget.config(state="disabled")  # Make read-only
        
        # Credits section
        credits_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        credits_frame.pack(fill="x", pady=10)
        
        tk.Label(credits_frame, text="Technologies Used", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        tech_text = (
            "• Python - Programming language\n"
            "• Tkinter - GUI framework\n"
            "• TkinterDnD - Drag and drop functionality\n"
            "• PyCryptodome - Encryption library\n"
            "• SQLite - Local database storage\n"
            "• Dropbox API - Cloud storage integration"
        )
        
        tech_widget = tk.Text(credits_frame, wrap="word", height=6, width=60, 
                            bg="#f1f1f1", bd=0, padx=5, pady=5)
        tech_widget.pack(fill="x")
        tech_widget.insert("1.0", tech_text)
        tech_widget.config(state="disabled")  # Make read-only
        
        # Import the needed modules for button creation
        import webbrowser
        
        # Contact section with GitHub link
        contact_frame = tk.Frame(content_frame, bg="#f1f1f1", padx=10, pady=10)
        contact_frame.pack(fill="x", pady=10)
        
        tk.Label(contact_frame, text="Contact & Support", font=("Arial", 12, "bold"), 
                bg="#f1f1f1").pack(anchor="w")
        
        contact_text = (
            "For support, bug reports, or feature requests, please visit the project repository:"
        )
        
        contact_widget = tk.Text(contact_frame, wrap="word", height=1, width=60, 
                                bg="#f1f1f1", bd=0, padx=5, pady=5)
        contact_widget.pack(fill="x")
        contact_widget.insert("1.0", contact_text)
        contact_widget.config(state="disabled")  # Make read-only
        
        # GitHub button (dummy link, replace with actual repo URL)
        def open_github():
            # Replace with your actual GitHub repository URL
            webbrowser.open("https://github.com/yourusername/bytescatter")
        
        github_button = tk.Button(contact_frame, text="Visit GitHub Repository", 
                                command=open_github, bg="#333", fg="white")
        github_button.pack(pady=10)
    
    def go_back(self):
        """Return to the main screen"""
        self.root.destroy()
        root = TkinterDnD.Tk()
        app = EncryptionApp(root)
        root.mainloop()

if __name__ == "__main__":
    # Handle the GUI imports
    try:
        # Make sure Output directory exists
        if not os.path.exists("output"):
            os.makedirs("output")
            
        # Import the gui module for intro
        from gui import introMenu
        introMenu()  # Show intro screen
        
        # Initialize the main app
        root = TkinterDnD.Tk()
        app = EncryptionApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")