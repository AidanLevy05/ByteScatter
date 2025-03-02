import tkinter as tk
from tkinter import filedialog, messagebox
import os
from tkinterdnd2 import DND_FILES, TkinterDnD
import shutil
from main import split_binary_file, split_text_file, encrypt_segment
import encryption


class EncryptionApp:
   def __init__(self, root):
       self.root = root
       self.root.title("ByteScatter")
       self.center_window(600, 400)
       self.root.configure(bg="#e0e0e0")


       # Enable Drag and Drop
       self.root.drop_target_register(DND_FILES)
       self.root.dnd_bind("<<Drop>>", self.on_file_drop)


       self.file_path = None


       # Top Bar
       tk.Label(self.root, text="ByteScatter", font=("Arial", 18, "bold"), bg="#e0e0e0").place(x=20, y=10)


       self.settings_button = tk.Button(self.root, text="⚙ Settings", font=("Arial", 10), command=self.open_settings, bg="#d3d3d3", relief="flat")
       self.settings_button.place(x=500, y=10, width=80, height=30)


       self.help_button = tk.Button(self.root, text="❓ Help", font=("Arial", 10), command=self.open_help, bg="#d3d3d3", relief="flat")
       self.help_button.place(x=500, y=50, width=80, height=30)


       # Drag and Drop Box
       self.drop_area = tk.Label(self.root, text="📂 Drop File Here or Click to Browse", font=("Arial", 14), fg="#404040", bg="#ffffff", relief="groove", width=40, height=6, cursor="hand2")
       self.drop_area.place(relx=0.5, rely=0.5, anchor="center")
       self.drop_area.bind("<Button-1>", self.select_file)


       # Uploaded Files Button
       self.uploaded_files_button = tk.Button(self.root, text="📁 View Uploaded Files", font=("Arial", 12), command=self.view_uploaded_files, bg="#4CAF50", fg="white", relief="flat")
       self.uploaded_files_button.place(relx=0.5, rely=0.75, anchor="center", width=200, height=40)


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


   def next_window(self):
       self.clear_window()


       original_file = self.file_path.get()
       num_splits = int(self.splits.get())
       password = self.password.get().encode()  # Convert password to bytes


       try:
           # Determine the split method (binary or text file)
           if os.path.splitext(original_file)[1] != ".txt":
               segments = split_binary_file(original_file, num_splits)
           else:
               segments = split_text_file("split", original_file, num_splits, 50)


           encrypted_files = []


           for idx, segment in enumerate(segments):
               enc_file, meta_file = encrypt_segment(segment, "file_id", password, idx)
               encrypted_files.append((enc_file, meta_file))


           # Let the user select a directory to save the segmented files
           save_dir = filedialog.askdirectory(title="Select Save Location for Encrypted Segments")
           if save_dir:
               for enc_file, meta_file in encrypted_files:
                   shutil.move(enc_file, os.path.join(save_dir, os.path.basename(enc_file)))
                   shutil.move(meta_file, os.path.join(save_dir, os.path.basename(meta_file)))


           SuccessWindow(self.root, original_file, encrypted_files, save_dir)


       except Exception as e:
           messagebox.showerror("Error", f"Encryption failed: {str(e)}")
           self.go_back()


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
   def __init__(self, root, original_file, encrypted_files, save_dir):
       self.root = root
       self.root.title("Encryption Complete")
       self.center_window(600, 400)


       # Title Label
       tk.Label(self.root, text="Encryption Successful!", font=("Arial", 16, "bold"), fg="green").grid(row=0, column=0, columnspan=2, pady=10)


       # Original File Info
       tk.Label(self.root, text="Original File:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", padx=10)
       tk.Label(self.root, text=original_file, font=("Arial", 12), fg="gray").grid(row=2, column=0, sticky="w", padx=10)


       # Separator Line
       tk.Frame(self.root, height=2, width=580, bg="black").grid(row=3, column=0, columnspan=2, pady=5)


       # Save Location
       tk.Label(self.root, text="Saved At:", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky="w", padx=10)
       tk.Label(self.root, text=save_dir, font=("Arial", 12), fg="gray").grid(row=5, column=0, sticky="w", padx=10)


       # Output Files Label
       tk.Label(self.root, text="Generated Files:", font=("Arial", 12, "bold")).grid(row=6, column=0, sticky="w", padx=10)


       # Output Files List
       self.file_list = tk.Listbox(self.root, height=6, width=50)
       self.file_list.grid(row=7, column=0, padx=10, pady=5, sticky="w")


       for enc_file, meta_file in encrypted_files:
           self.file_list.insert(tk.END, f"Encrypted: {os.path.join(save_dir, os.path.basename(enc_file))}")
           self.file_list.insert(tk.END, f"Metadata: {os.path.join(save_dir, os.path.basename(meta_file))}")
           self.file_list.insert(tk.END, " ")  # Spacer for clarity


       # Exit Button
       self.exit_button = tk.Button(self.root, text="Exit", font=("Arial", 12), bg="red", fg="white", command=self.root.quit)
       self.exit_button.grid(row=7, column=1, padx=20, pady=5)


   def center_window(self, width, height):
       self.root.update_idletasks()
       screen_width = self.root.winfo_screenwidth()
       screen_height = self.root.winfo_screenheight()
       x = (screen_width // 2) - (width // 2)
       y = (screen_height // 2) - (height // 2)
       self.root.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
   root = TkinterDnD.Tk()  # Use TkinterDnD instead of standard Tk()
   app = EncryptionApp(root)
   root.mainloop()
