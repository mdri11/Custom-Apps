import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import threading
from pathlib import Path

class FileOrganizerApp:
    def __init__(self, master):
        self.master = master
        self.keyword_rows = []
        self.operation_cancelled = False
        self.operation_running = False
        self.help_visible = False
        self.setup_ui()

    def setup_ui(self):
        self.master.title("File Organizer Pro")
        
        # Set window size
        window_width = 550
        window_height = 670
        
        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        # Calculate center position
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        
        # Set geometry with center position
        self.master.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.master.resizable(False, False)

        # Main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)

        current_row = 0

        # Source folder
        ttk.Label(main_frame, text="Source Folder").grid(row=current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        current_row += 1
        self.source_entry = ttk.Entry(main_frame)
        self.source_entry.grid(row=current_row, column=0, sticky="ew", padx=5, pady=2)
        ttk.Button(main_frame, text="Browse", command=lambda: self.browse_folder(self.source_entry)).grid(row=current_row, column=1, sticky="ew", padx=5, pady=2)
        current_row += 1

        # Target folder
        ttk.Label(main_frame, text="Target Folder (optional - defaults to source)").grid(row=current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        current_row += 1
        self.target_entry = ttk.Entry(main_frame)
        self.target_entry.grid(row=current_row, column=0, sticky="ew", padx=5, pady=2)
        ttk.Button(main_frame, text="Browse", command=lambda: self.browse_folder(self.target_entry)).grid(row=current_row, column=1, sticky="ew", padx=5, pady=2)
        current_row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        current_row += 1

        # Operation mode
        ttk.Label(main_frame, text="Operation Mode").grid(row=current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        current_row += 1
        self.operation_mode = tk.StringVar(value="copy")
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="Copy Files (Safe)", variable=self.operation_mode, value="copy").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Move Files", variable=self.operation_mode, value="move").pack(side=tk.LEFT, padx=5)
        current_row += 1
        
        # Search depth option
        self.include_subfolders = tk.BooleanVar(value=True)
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        ttk.Checkbutton(search_frame, text="Include subfolders (search recursively)", 
                       variable=self.include_subfolders).pack(side=tk.LEFT, padx=5)
        current_row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        current_row += 1

        # Collapsible Help Section
        help_header_frame = ttk.Frame(main_frame)
        help_header_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        self.help_toggle_btn = ttk.Button(help_header_frame, text="▶ Show Keyword Help", command=self.toggle_help)
        self.help_toggle_btn.pack(side=tk.LEFT)
        current_row += 1
        
        # Help window will be created as separate Toplevel when needed
        self.help_window = None

        # Keywords section header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Label(header_frame, text="Keywords", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Folder Name", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=150)
        current_row += 1

        # Scrollable frame for keyword rows
        scroll_container = ttk.Frame(main_frame)
        scroll_container.grid(row=current_row, column=0, columnspan=2, sticky="nsew", padx=5, pady=2)
        
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(scroll_container, height=87, bg="white", highlightthickness=1, highlightbackground="#cccccc")
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        self.keyword_container = ttk.Frame(self.canvas)
        
        self.keyword_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.keyword_container, anchor="nw", width=500)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel for scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.keyword_container.bind("<MouseWheel>", self._on_mousewheel)
        
        current_row += 1

        # Create initial 3 rows
        for i in range(3):
            self.add_keyword_row()

        # Add row button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Button(button_frame, text="+ Add Row", command=self.add_keyword_row).pack(side=tk.LEFT, padx=5)
        current_row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        current_row += 1

        # Preview and Execute buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.preview_button = tk.Button(action_frame, text="Preview", command=self.preview_operation, 
                                       bg="#003d82", fg="white", height=2, font=('Arial', 10, 'bold'))
        self.preview_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.execute_button = tk.Button(action_frame, text="Execute", command=self.execute, 
                                       bg="green", fg="white", height=2, font=('Arial', 10, 'bold'))
        self.execute_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.cancel_button = tk.Button(action_frame, text="Cancel", command=self.cancel_operation, 
                                      bg="#ffeb3b", fg="black", height=2, font=('Arial', 10, 'bold'), state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        current_row += 1

        # Reset button
        self.reset_button = tk.Button(main_frame, text="Reset All", command=self.soft_reset, 
                                     bg="red", fg="white", height=2, font=('Arial', 10, 'bold'))
        self.reset_button.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        current_row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        current_row += 1

        # Progress section
        self.progress_label = ttk.Label(main_frame, text="Ready")
        self.progress_label.grid(row=current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        current_row += 1
        
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        current_row += 1
        
        self.progress_percent = ttk.Label(main_frame, text="0%")
        self.progress_percent.grid(row=current_row, column=0, columnspan=2)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling for keyword canvas"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def toggle_help(self):
        """Toggle help section visibility as separate window"""
        if self.help_visible:
            if self.help_window:
                self.help_window.destroy()
                self.help_window = None
            self.help_toggle_btn.config(text="▶ Show Keyword Help")
            self.help_visible = False
        else:
            # Create separate popup window
            self.help_window = tk.Toplevel(self.master)
            self.help_window.title("Keyword Help")
            self.help_window.geometry("540x310")
            self.help_window.resizable(False, False)
            
            # Position near main window
            x = self.master.winfo_x() + 50
            y = self.master.winfo_y() + 100
            self.help_window.geometry(f"+{x}+{y}")
            
            # Help content
            help_text = scrolledtext.ScrolledText(self.help_window, wrap=tk.WORD, bg="#f0f0f0", 
                                                 relief=tk.FLAT, font=('Arial', 9), 
                                                 borderwidth=0, padx=10, pady=10, fg="black")
            help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            help_content = """Keyword Operators:

• Simple keyword: "apple" - matches any file containing "apple"

• AND operator (*): "apple * red" - matches files with BOTH "apple" AND "red"

• OR operator (|): "apple | orange" - matches files with EITHER "apple" OR "orange"  

• NOT operator (!): "apple ! red" - matches files with "apple" but NOT "red"

Examples:
  "photo * 2024" → matches "vacation_photo_2024.jpg"
  "jpg | png" → matches both .jpg and .png files
  "report ! draft" → matches "final_report.pdf" but not "draft_report.pdf"

You can combine operators in your keywords to create powerful search patterns. The matching is case-insensitive and works on both the filename and file extension.
"""
            help_text.insert("1.0", help_content)
            help_text.config(state=tk.DISABLED)
            
            # Handle window close button
            self.help_window.protocol("WM_DELETE_WINDOW", self.toggle_help)
            
            self.help_toggle_btn.config(text="▼ Hide Keyword Help")
            self.help_visible = True

    def bind_mousewheel_to_row(self, row):
        """Bind mousewheel to all widgets in a row"""
        row['frame'].bind("<MouseWheel>", self._on_mousewheel)
        row['keyword'].bind("<MouseWheel>", self._on_mousewheel)
        row['folder'].bind("<MouseWheel>", self._on_mousewheel)
        row['remove_btn'].bind("<MouseWheel>", self._on_mousewheel)

    def add_keyword_row(self):
        """Add a new keyword/folder row - NO LIMIT"""
        row_frame = ttk.Frame(self.keyword_container)
        row_frame.pack(fill=tk.X, pady=2, padx=5)
        
        keyword_entry = ttk.Entry(row_frame, width=35)
        keyword_entry.pack(side=tk.LEFT, padx=2)
        keyword_entry.insert(0, "e.g., photo * 2024")
        keyword_entry.config(foreground='grey')
        keyword_entry.bind("<FocusIn>", lambda e: self.on_entry_click(keyword_entry, "e.g., photo * 2024"))
        keyword_entry.bind("<FocusOut>", lambda e: self.on_focusout(keyword_entry, "e.g., photo * 2024"))
        
        folder_entry = ttk.Entry(row_frame, width=33)
        folder_entry.pack(side=tk.LEFT, padx=2)
        folder_entry.insert(0, "Folder name")
        folder_entry.config(foreground='grey')
        folder_entry.bind("<FocusIn>", lambda e: self.on_entry_click(folder_entry, "Folder name"))
        folder_entry.bind("<FocusOut>", lambda e: self.on_focusout(folder_entry, "Folder name"))
        
        remove_btn = ttk.Button(row_frame, text="Remove", width=8, 
                               command=lambda: self.remove_keyword_row(row_frame))
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        self.keyword_rows.append({
            'frame': row_frame,
            'keyword': keyword_entry,
            'folder': folder_entry,
            'remove_btn': remove_btn
        })
        
        # Bind mousewheel to row widgets
        self.bind_mousewheel_to_row(self.keyword_rows[-1])
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_entry_click(self, entry, placeholder):
        """Clear placeholder on focus"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(foreground='black')

    def on_focusout(self, entry, placeholder):
        """Restore placeholder if empty"""
        if entry.get() == '':
            entry.insert(0, placeholder)
            entry.config(foreground='grey')

    def remove_keyword_row(self, frame):
        """Remove a keyword row"""
        if len(self.keyword_rows) <= 1:
            messagebox.showwarning("Warning", "At least one row must remain")
            return
        
        for row in self.keyword_rows:
            if row['frame'] == frame:
                row['frame'].destroy()
                self.keyword_rows.remove(row)
                break
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def browse_folder(self, entry_widget):
        """Browse for folder"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder_path)

    def soft_reset(self):
        """Properly reset the application without restarting"""
        if self.operation_running:
            messagebox.showwarning("Warning", "Cannot reset while operation is running. Please cancel first.")
            return
        
        # Clear source and target
        self.source_entry.delete(0, tk.END)
        self.target_entry.delete(0, tk.END)
        
        # Reset operation mode
        self.operation_mode.set("copy")
        
        # Clear all keyword rows
        for row in self.keyword_rows[:]:
            row['frame'].destroy()
        self.keyword_rows.clear()
        
        # Create fresh 3 rows
        for i in range(3):
            self.add_keyword_row()
        
        # Reset progress
        self.progress['value'] = 0
        self.progress_percent['text'] = "0%"
        self.progress_label['text'] = "Ready"
        
        # Reset flags
        self.operation_cancelled = False
        self.operation_running = False
        
        # Enable buttons
        self.execute_button.config(state=tk.NORMAL)
        self.preview_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def match_keyword(self, filename, keyword):
        """
        Match filename against keyword with operators
        * = AND
        | = OR
        ! = NOT
        """
        filename_lower = filename.lower()
        keyword_lower = keyword.lower()
        
        # Handle NOT operator (!)
        if '!' in keyword_lower:
            parts = keyword_lower.split('!')
            if len(parts) == 2:
                must_have = parts[0].strip()
                must_not_have = parts[1].strip()
                return must_have in filename_lower and must_not_have not in filename_lower
        
        # Handle OR operator (|)
        if '|' in keyword_lower:
            parts = keyword_lower.split('|')
            return any(part.strip() in filename_lower for part in parts)
        
        # Handle AND operator (*)
        if '*' in keyword_lower:
            parts = keyword_lower.split('*')
            return all(part.strip() in filename_lower for part in parts)
        
        # Simple keyword match
        return keyword_lower in filename_lower

    def validate_inputs(self):
        """Validate user inputs before operation"""
        source_path = self.source_entry.get().strip()
        
        if not source_path:
            messagebox.showerror("Error", "Please select a source folder")
            return None
        
        if not os.path.exists(source_path):
            messagebox.showerror("Error", f"Source folder does not exist:\n{source_path}")
            return None
        
        if not os.path.isdir(source_path):
            messagebox.showerror("Error", "Source path must be a directory")
            return None
        
        target_path = self.target_entry.get().strip()
        if not target_path:
            target_path = source_path
        
        # Get valid keyword/folder pairs (skip placeholders)
        valid_pairs = []
        for row in self.keyword_rows:
            keyword = row['keyword'].get().strip()
            folder = row['folder'].get().strip()
            
            # Skip if empty or still has placeholder text
            if keyword and folder and keyword != "e.g., photo * 2024" and folder != "Folder name":
                valid_pairs.append((keyword, folder))
        
        if not valid_pairs:
            messagebox.showerror("Error", "Please enter at least one keyword and folder name pair")
            return None
        
        return {
            'source': source_path,
            'target': target_path,
            'pairs': valid_pairs,
            'mode': self.operation_mode.get(),
            'include_subfolders': self.include_subfolders.get()
        }

    def preview_operation(self):
        """Show preview of what files will be moved/copied"""
        config = self.validate_inputs()
        if not config:
            return
        
        preview_window = tk.Toplevel(self.master)
        preview_window.title("Preview - File Operations")
        preview_window.geometry("600x400")
        
        ttk.Label(preview_window, text=f"Operation: {config['mode'].upper()}", 
                 font=('Arial', 10, 'bold')).pack(pady=5)
        
        text_area = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD, width=70, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Scan files
        file_matches = {}
        unmatched_files = []
        
        try:
            if config['include_subfolders']:
                # Search recursively in all subfolders
                for root, _, files in os.walk(config['source']):
                    for filename in files:
                        matched = False
                        for keyword, folder_name in config['pairs']:
                            if self.match_keyword(filename, keyword):
                                if folder_name not in file_matches:
                                    file_matches[folder_name] = []
                                file_matches[folder_name].append(filename)
                                matched = True
                                break
                        
                        if not matched:
                            unmatched_files.append(filename)
            else:
                # Search only in the source folder (not subfolders)
                try:
                    files = [f for f in os.listdir(config['source']) 
                            if os.path.isfile(os.path.join(config['source'], f))]
                    for filename in files:
                        matched = False
                        for keyword, folder_name in config['pairs']:
                            if self.match_keyword(filename, keyword):
                                if folder_name not in file_matches:
                                    file_matches[folder_name] = []
                                file_matches[folder_name].append(filename)
                                matched = True
                                break
                        
                        if not matched:
                            unmatched_files.append(filename)
                except Exception as e:
                    messagebox.showerror("Error", f"Error reading source folder:\n{str(e)}")
                    preview_window.destroy()
                    return
            
            # Display results
            if file_matches:
                for folder_name, files in file_matches.items():
                    text_area.insert(tk.END, f"\n📁 {folder_name} ({len(files)} files):\n", 'header')
                    for f in files[:10]:
                        text_area.insert(tk.END, f"   • {f}\n")
                    if len(files) > 10:
                        text_area.insert(tk.END, f"   ... and {len(files) - 10} more files\n")
            else:
                text_area.insert(tk.END, "No files match the given keywords.\n")
            
            if unmatched_files:
                text_area.insert(tk.END, f"\n⚠️  {len(unmatched_files)} files won't be processed (no keyword match)\n")
            
            text_area.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error during preview:\n{str(e)}")
            preview_window.destroy()

    def cancel_operation(self):
        """Cancel ongoing operation"""
        self.operation_cancelled = True
        self.progress_label['text'] = "Cancelling..."

    def execute(self):
        """Execute file organization in a separate thread"""
        config = self.validate_inputs()
        if not config:
            return
        
        # Disable buttons during operation
        self.execute_button.config(state=tk.DISABLED)
        self.preview_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        self.operation_running = True
        self.operation_cancelled = False
        
        # Run in thread
        thread = threading.Thread(target=self.perform_file_operations, args=(config,))
        thread.daemon = True
        thread.start()

    def perform_file_operations(self, config):
        """Perform the actual file operations"""
        operation_log = {
            'success': {},
            'errors': [],
            'skipped': [],
            'total_processed': 0
        }
        
        try:
            # Collect all matching files first
            files_to_process = []
            
            if config['include_subfolders']:
                # Search recursively in all subfolders
                for root, _, files in os.walk(config['source']):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        
                        for keyword, folder_name in config['pairs']:
                            if self.match_keyword(filename, keyword):
                                files_to_process.append((file_path, filename, folder_name))
                                break
            else:
                # Search only in the source folder (not subfolders)
                try:
                    files = [f for f in os.listdir(config['source']) 
                            if os.path.isfile(os.path.join(config['source'], f))]
                    for filename in files:
                        file_path = os.path.join(config['source'], filename)
                        
                        for keyword, folder_name in config['pairs']:
                            if self.match_keyword(filename, keyword):
                                files_to_process.append((file_path, filename, folder_name))
                                break
                except Exception as e:
                    self.master.after(0, lambda: messagebox.showerror("Error", f"Error reading source folder:\n{str(e)}"))
                    self.master.after(0, self.reset_ui_after_operation)
                    return
            
            total_files = len(files_to_process)
            
            if total_files == 0:
                self.master.after(0, lambda: messagebox.showinfo("No Matches", "No files matched the given keywords."))
                self.master.after(0, self.reset_ui_after_operation)
                return
            
            # Process files
            for idx, (file_path, filename, folder_name) in enumerate(files_to_process):
                if self.operation_cancelled:
                    self.master.after(0, lambda: messagebox.showinfo("Cancelled", "Operation cancelled by user."))
                    self.master.after(0, self.reset_ui_after_operation)
                    return
                
                try:
                    # Create destination folder (auto-create if doesn't exist)
                    dest_folder = os.path.join(config['target'], folder_name)
                    os.makedirs(dest_folder, exist_ok=True)
                    
                    dest_path = os.path.join(dest_folder, filename)
                    
                    # Handle duplicate filenames
                    if os.path.exists(dest_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(dest_path):
                            new_filename = f"{base}_{counter}{ext}"
                            dest_path = os.path.join(dest_folder, new_filename)
                            counter += 1
                    
                    # Perform operation
                    if config['mode'] == 'copy':
                        shutil.copy2(file_path, dest_path)
                    else:
                        shutil.move(file_path, dest_path)
                    
                    # Log success
                    if folder_name not in operation_log['success']:
                        operation_log['success'][folder_name] = 0
                    operation_log['success'][folder_name] += 1
                    operation_log['total_processed'] += 1
                    
                except Exception as e:
                    operation_log['errors'].append(f"{filename}: {str(e)}")
                
                # Update progress
                progress = int(((idx + 1) / total_files) * 100)
                self.master.after(0, lambda p=progress, f=filename: self.update_progress(p, f))
            
            # Show summary
            self.master.after(0, lambda: self.show_summary(operation_log, config['mode']))
            
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"Operation failed:\n{str(e)}"))
        
        finally:
            self.master.after(0, self.reset_ui_after_operation)

    def update_progress(self, percent, filename):
        """Update progress bar and label"""
        self.progress['value'] = percent
        self.progress_percent['text'] = f"{percent}%"
        self.progress_label['text'] = f"Processing: {filename[:40]}..."

    def reset_ui_after_operation(self):
        """Reset UI state after operation completes"""
        self.operation_running = False
        self.execute_button.config(state=tk.NORMAL)
        self.preview_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def show_summary(self, log, mode):
        """Show operation summary"""
        summary_window = tk.Toplevel(self.master)
        summary_window.title("Operation Summary")
        summary_window.geometry("500x400")
        
        ttk.Label(summary_window, text=f"Operation Complete - {mode.upper()}", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD, width=60, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        text_area.insert(tk.END, f"✅ Total files processed: {log['total_processed']}\n\n")
        
        if log['success']:
            text_area.insert(tk.END, "Files organized by folder:\n")
            for folder, count in log['success'].items():
                text_area.insert(tk.END, f"  📁 {folder}: {count} files\n")
        
        if log['errors']:
            text_area.insert(tk.END, f"\n❌ Errors ({len(log['errors'])}):\n")
            for error in log['errors'][:10]:
                text_area.insert(tk.END, f"  • {error}\n")
            if len(log['errors']) > 10:
                text_area.insert(tk.END, f"  ... and {len(log['errors']) - 10} more errors\n")
        
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(summary_window, text="Close", command=summary_window.destroy).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()
