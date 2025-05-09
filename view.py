import os
import sys
import sv_ttk
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

####################### ===== USBView ===== #######################
class USBView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Neon Data Sync v3.0")
        self.root.geometry("1000x700")
        self.root.minsize(1000, 830)  # Minimum window dimensions
        self.root.iconbitmap("usb.ico")
        # self.icon = tk.PhotoImage(file="icon.png")
        # self.root.iconphoto(False, self.icon)

        self.style = ttk.Style()
            # Style for regular buttons
        self.style.configure('TButton', 
                        font=('Courier New', 10, 'bold'),
                        padding=6,
                        cursor='hand2')  # add the "hand" cursor
                        
        # Expanded window (maximized)
        self.root.state('zoomed')  # for Windows

        # Setting up a grid for a responsive interface
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        sv_ttk.use_dark_theme()
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#0a0a12')
        self.style.configure('TLabel', background='#0a0a12', foreground='#00ff99', font=('Courier New', 10))
        self.style.configure('TButton', font=('Courier New', 10, 'bold'), padding=6)
        self.style.configure('TProgressbar', thickness=20, troughcolor='#1a1a2e', background='#00ff99')
        
        # Main container с grid layout
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Setting up the main frame grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=0)  # Header
        main_frame.grid_rowconfigure(1, weight=1)  # Devices
        main_frame.grid_rowconfigure(2, weight=0)  # Backup controls
        main_frame.grid_rowconfigure(3, weight=0)  # Progress
        main_frame.grid_rowconfigure(4, weight=0)  # Buttons
        main_frame.grid_rowconfigure(5, weight=1)  # Terminal
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        self.title_label = ttk.Label(header_frame, text="USB SYNC", font=('Courier New', 20, 'bold'))
        self.title_label.grid(row=0, column=0, sticky="w")
        
        # Device lists - we use grid for adaptability
        devices_container = ttk.Frame(main_frame)
        devices_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        devices_container.grid_columnconfigure(0, weight=1)
        devices_container.grid_columnconfigure(1, weight=1)
        devices_container.grid_rowconfigure(0, weight=1)
        
        # Source device frame
        source_frame = ttk.LabelFrame(devices_container, text=" Source Device ", padding=10)
        source_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        source_frame.grid_columnconfigure(0, weight=1)
        source_frame.grid_rowconfigure(0, weight=1)
        
        self.source_tree = ttk.Treeview(source_frame, columns=('size', 'free', 'type'), selectmode='browse')
        self.source_tree.heading('#0', text='Device')
        self.source_tree.heading('size', text='Size')
        self.source_tree.heading('free', text='Free')
        self.source_tree.heading('type', text='Type')
        self.source_tree.grid(row=0, column=0, sticky="nsew")
        self.source_tree.column('#0', stretch=tk.YES)  # Allow stretching
        self.source_tree.bind("<Double-1>", self.on_device_double_click)  # Double click handler

        # Target devices frame
        targets_frame = ttk.LabelFrame(devices_container, text=" Target Devices ", padding=10)
        targets_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        targets_frame.grid_columnconfigure(0, weight=1)
        targets_frame.grid_rowconfigure(0, weight=1)
        
        self.targets_tree = ttk.Treeview(targets_frame, columns=('size', 'free', 'type'), selectmode='extended')
        self.targets_tree.heading('#0', text='Device')
        self.targets_tree.heading('size', text='Size')
        self.targets_tree.heading('free', text='Free')
        self.targets_tree.heading('type', text='Type')
        self.targets_tree.grid(row=0, column=0, sticky="nsew")
        self.targets_tree.column('#0', stretch=tk.YES)
        self.targets_tree.bind("<Double-1>", self.on_device_double_click)  
        
        # Adding Scrollbars to Treeview
        for tree in [self.source_tree, self.targets_tree]:
            scroll_y = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
            scroll_x = ttk.Scrollbar(tree, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")
        
        # Backup controls
        backup_frame = ttk.LabelFrame(main_frame, text=" Backup Management ", padding=10)
        backup_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        backup_frame.grid_columnconfigure(0, weight=1)
        backup_frame.grid_columnconfigure(1, weight=0)

        self.show_backups_btn = ttk.Button(
            backup_frame,
            text="View Backups",
            command=self.controller.show_backup_history,
            cursor='hand2'
        )
        self.show_backups_btn.grid(row=0, column=0, sticky="w", padx=5)

        self.sync_btn = ttk.Button(
            backup_frame, 
            text="Start Sync with Backup", 
            command=self.controller.start_sync_with_backup,
            cursor='hand2'
        )
        self.sync_btn.grid(row=0, column=1, sticky="e", padx=5)

        self.backup_btn = ttk.Button(
            backup_frame, 
            text="Start Backup", 
            command=self.controller.start_backup,
            cursor='hand2'
        )
        self.backup_btn.grid(row=0, column=0, sticky="e", padx=5)

        # Progress area - we divide into two sections
        progress_frame = ttk.LabelFrame(main_frame, text=" Operation Progress ", padding=10)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Section for the main operation
        transfer_frame = ttk.Frame(progress_frame)
        transfer_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.transfer_label = ttk.Label(transfer_frame, text="Waiting for operation...")
        self.transfer_label.pack(fill="x", pady=(0, 3))
        
        self.transfer_progress = ttk.Progressbar(transfer_frame, mode='determinate')
        self.transfer_progress.pack(fill="x")
        
        self.transfer_time = ttk.Label(transfer_frame, text="Estimated time remaining: --")
        self.transfer_time.pack(fill="x")
        
        # Backup section
        backup_frame = ttk.Frame(progress_frame)
        backup_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        self.backup_label = ttk.Label(backup_frame, text="Backup progress: not started")
        self.backup_label.pack(fill="x", pady=(0, 3))
        
        self.backup_progress = ttk.Progressbar(backup_frame, mode='determinate')
        self.backup_progress.pack(fill="x")
        
        self.backup_time = ttk.Label(backup_frame, text="Backup time remaining: --")
        self.backup_time.pack(fill="x")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=0)
        
        self.refresh_btn = ttk.Button(
            button_frame,
            text="Refresh Devices",
            command=self.controller.manual_refresh,
            cursor='hand2'
            
        )
        self.refresh_btn.grid(row=0, column=0, sticky="w", padx=5)
        
        btn_container = ttk.Frame(button_frame)
        btn_container.grid(row=0, column=1, sticky="e")
        
        self.transfer_btn = ttk.Button(
            btn_container, 
            text="Start Transfer", 
            command=self.controller.start_transfer,
            cursor='hand2'
        )
        self.transfer_btn.pack(side="left", padx=5)


        # Terminal - reduced version
        terminal_frame = ttk.LabelFrame(main_frame, text=" System Log ", padding=10)
        terminal_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 10))  # Add some padding at the bottom
        terminal_frame.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(0, weight=1)

        # Reduce the height of the text field (rows=10 sets the height to approximately 10 rows)
        self.terminal = tk.Text(
            terminal_frame, 
            bg='#1a1a2e', 
            fg='#00ff99', 
            insertbackground='#00ff99',
            font=('Courier New', 8), 
            wrap=tk.WORD,
            height=10  # Set a fixed number of visible lines
        )
        self.terminal.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(terminal_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.terminal.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.terminal.yview)

        # Clear button System Log
        self.clear_terminal_btn = ttk.Button(terminal_frame, text="Clear Log", command=self.clear_terminal)
        self.clear_terminal_btn.grid(row=1, column=0, sticky="e", pady=(15, 0))

    def clear_terminal(self):
        self.terminal.delete(1.0, tk.END)

    def log_message(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.log_widget.insert(tk.END, timestamp + message + '\n')
        self.log_widget.see(tk.END)

    def clear_log(self):
        self.log_widget.delete(1.0, tk.END) 

    def setup_treeview_columns(self, tree):
        """Sets up speakers Treeview"""
        tree.heading('#0', text='Device', anchor='w')
        tree.heading('size', text='Size', anchor='w')
        tree.heading('free', text='Free', anchor='w')
        tree.heading('type', text='Type', anchor='w')
        
        tree.column('#0', width=200, anchor='w', stretch=True)
        tree.column('size', width=100, anchor='e', stretch=False)
        tree.column('free', width=100, anchor='e', stretch=False)
        tree.column('type', width=100, anchor='center', stretch=False)

    def on_device_double_click(self, event):
        """Device double click handler"""
        tree = event.widget
        item = tree.identify_row(event.y)
        
        if item:  # If the click was on the line with the device
            device_name = tree.item(item, "text")
            device_info = self.get_device_info(device_name)
            
            if device_info:
                self.open_device_in_explorer(device_info)
    
    def get_device_info(self, device_name):
        """Gets information about a device by its name"""
        devices = self.controller.model.get_usb_devices()
        for device in devices:
            if device['label'] == device_name:
                return device
        return None
    
    def open_device_in_explorer(self, device_info):
        """Opens USB drive in Explorer"""
        mount_point = device_info['mountpoint']
        try:
            if os.name == 'nt':  # Windows
                os.startfile(mount_point)
            elif os.name == 'posix':  # Linux/Mac
                if sys.platform == 'darwin':
                    subprocess.run(['open', mount_point])
                else:
                    subprocess.run(['xdg-open', mount_point])
            
            self.log_message(f"Opened USB device: {device_info['label']} at {mount_point}")
        except Exception as e:
            error_msg = f"Failed to open device {device_info['label']}: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("Error", error_msg)

    def update_device_lists(self, devices):
        current_source = self.get_selected_source()
        current_targets = self.get_selected_targets()
        
        self.source_tree.delete(*self.source_tree.get_children())
        self.targets_tree.delete(*self.targets_tree.get_children())
        
        for device in devices:
            total_gb = device['total'] / (1024**3)
            free_gb = device['free'] / (1024**3)
            
            item = self.source_tree.insert('', 'end', text=device['label'],
                                  values=(f"{total_gb:.2f} GB", f"{free_gb:.2f} GB", device['fstype']))
            
            target_item = self.targets_tree.insert('', 'end', text=device['label'],
                                  values=(f"{total_gb:.2f} GB", f"{free_gb:.2f} GB", device['fstype']))
            
            # Restore the previous selection
            if device['label'] == current_source:
                self.source_tree.selection_set(item)
            
            if device['label'] in current_targets:
                self.targets_tree.selection_add(target_item)
        
        self.log_message(f"Devices list updated")
    
    def update_progress(self, progress, message, remaining_time, operation_type='transfer'):
        """Updates progress depending on the type of operation"""
        if operation_type == 'backup':
            self.backup_progress['value'] = progress
            self.backup_label.config(text=message)
            if remaining_time > 0:
                mins, secs = divmod(int(remaining_time), 60)
                self.backup_time.config(text=f"Backup time remaining: {mins:02d}:{secs:02d}")
            else:
                if progress >= 100:
                    self.backup_time.config(text="Backup completed")
                else:
                    self.backup_time.config(text="Backup time remaining: --")
        else:
            self.transfer_progress['value'] = progress
            self.transfer_label.config(text=message)
            if remaining_time > 0:
                mins, secs = divmod(int(remaining_time), 60)
                self.transfer_time.config(text=f"Transfer time remaining: {mins:02d}:{secs:02d}")
            else:
                self.transfer_time.config(text="Transfer time remaining: --")
        
        self.root.update_idletasks()

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(tk.END, f"[{timestamp}] {message}\n")
        self.terminal.see(tk.END)
        # self.terminal.delete()

    def show_notification(self, title, message):
        messagebox.showinfo(title, message)
    
    def get_selected_source(self):
        selection = self.source_tree.selection()
        if selection:
            item = self.source_tree.item(selection[0])
            return item['text']
        return None
    
    def get_selected_targets(self):
        selections = self.targets_tree.selection()
        targets = []
        for selection in selections:
            item = self.targets_tree.item(selection)
            targets.append(item['text'])
        return targets


