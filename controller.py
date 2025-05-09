import os
import time
import shutil
import threading
import tkinter as tk
from tkinter import ttk
from view import USBView
from model import USBModel
from datetime import datetime

####################### ===== USBController ===== #######################
class USBController:
    def __init__(self, root):
        self.model = USBModel()
        self.view = USBView(root, self)
        self.last_sync_info = None
        self.model.start_monitoring(self.view.update_device_lists)
        self.view.log_message("System initialized with backup support")
        
        # First explanation
        self.manual_refresh()
        
        # It takes 1 second to reach the end, but the device is not yet there
        root.after(1000, self.manual_refresh)
        
        # Monitoring with optimized interval
        self.model.start_monitoring(self.view.update_device_lists)
        
        # root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.view.log_message("System initialized. Ready for transfers.")

    def manual_refresh(self):
        """Manual refresh of device list"""
        devices = self.model.get_usb_devices()
        self.view.update_device_lists(devices)
        self.view.log_message("Manual refresh completed")
    
    def start_transfer(self):
        """Start transfer from selected source to selected targets"""
        source = self.view.get_selected_source()
        targets = self.view.get_selected_targets()
        
        if not source:
            self.view.show_notification("Error", "No source device selected")
            return
            
        if not targets:
            self.view.show_notification("Error", "No target devices selected")
            return
            
        devices = self.model.get_usb_devices()
        source_device = next((d for d in devices if d['label'] == source), None)
        target_mountpoints = [d['mountpoint'] for d in devices if d['label'] in targets]
        
        if not source_device:
            self.view.show_notification("Error", "Source device not found")
            return
            
        # Проверка, что источник не выбран как цель
        if source in targets:
            self.view.show_notification("Error", "Source cannot be a target")
            return
            
        self.view.log_message(f"Starting transfer from {source} to {len(targets)} targets")
        
        # Disable UI during transfer
        self.view.transfer_btn.config(state=tk.DISABLED)
        self.view.refresh_btn.config(state=tk.DISABLED)
        
        # We start the transmission in a separate thread
        transfer_thread = threading.Thread(
            target=self._perform_transfer,
            args=(source_device['mountpoint'], target_mountpoints),
            daemon=True
        )
        transfer_thread.start()

    def _perform_transfer(self, source, targets):
        def progress_callback(progress, message, remaining):
            self.view.update_progress(progress, message, remaining)
        
        success_targets = self.model.transfer_data(
            source, targets, progress_callback
        )
        
        # Turn the UI back on
        self.view.transfer_btn.config(state=tk.NORMAL)
        self.view.refresh_btn.config(state=tk.NORMAL)
        
        # Showing results
        if success_targets:
            target_info = [f"{label} ({os.path.join(target, os.path.basename(source))})"
            for label, target in zip(success_targets, targets)]
            targets_str = "\n".join(target_info)
            self.view.log_message("Transfer completed to:\n" + targets_str)
            self.view.show_notification(
                "Transfer Complete",
targets_str = "\n".join(target_info)
)
        else:
            self.view.log_message("Transfer failed - check device accessibility")
            self.view.show_notification(
                "Transfer Failed",
                "No data was transferred. Check if devices are accessible and have enough space."
            )
        
        self.view.update_progress(0, "Ready for next transfer", 0)

    def start_backup(self):
        source = self.view.get_selected_source()
        targets = self.view.get_selected_targets()
        
        if not source:
            self.view.show_notification("Error", "No source device selected")
            return
            
        if not targets:
            self.view.show_notification("Error", "No target devices selected")
            return
            
        devices = self.model.get_usb_devices()  
        source_device = next((d for d in devices if d['label'] == source), None)
        target_devices = [d for d in devices if d['label'] in targets]
        
        if not source_device:
            self.view.show_notification("Error", "Source device not found")
            return
            
        if source in targets:
            self.view.show_notification("Error", "Source cannot be a target")
            return
            
        self.view.log_message(f"Starting backup from {source} to {len(targets)} targets")
        
        # Setting the initial state
        self.view.update_progress(0, "Backup starting...", 0, 'backup')
        
        # Disabling buttons
        self.view.sync_btn.config(state=tk.DISABLED)
        self.view.refresh_btn.config(state=tk.DISABLED)
        self.view.backup_btn.config(state=tk.DISABLED)
        
        backup_thread = threading.Thread(
            target=self._perform_backup,
            args=(source_device, target_devices),
            daemon=True
        )
        backup_thread.start()

    def _perform_backup(self, source_device, target_devices):
        try:
            source_path = source_device['mountpoint']
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Setting the initial status
            self.view.update_progress(0, "Backup in progress...", 0, 'backup')
            
            # Counting the total number of files
            total_files = 0
            for root, _, files in os.walk(source_path):
                total_files += len(files)
            
            if total_files == 0:
                self.view.update_progress(100, "Backup complete: 0 files", 0, 'backup')
                self.view.log_message("No files found for backup")
                return
                
            for target in target_devices:
                target_path = target['mountpoint']
                backup_dir = os.path.join(target_path, f"backup_{timestamp}")
                
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                copied_files = 0
                start_time = time.time()
                
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        src_file = os.path.join(root, file)
                        rel_path = os.path.relpath(src_file, source_path)
                        dst_file = os.path.join(backup_dir, rel_path)
                        
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        copied_files += 1
                        
                        progress = (copied_files / total_files) * 100
                        elapsed = time.time() - start_time
                        remaining = (elapsed / max(1, progress)) * (100 - progress) if progress > 0 else 0
                        status_msg = f"Backup to {target['label']}: {copied_files}/{total_files} files"
                        self.view.update_progress(progress, status_msg, remaining, 'backup')
                
                self.view.log_message(f"Backup to {target['label']} completed")
            
            # Setting the final status
            self.view.update_progress(100, "Backup completed successfully", 0, 'backup')
            self.view.show_notification("Success", "Backup completed successfully")
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            self.view.update_progress(0, error_msg, 0, 'backup')
            self.view.log_message(error_msg)
            self.view.show_notification("Error", error_msg)
        
        finally:
            # Restoring buttons
            self.view.sync_btn.config(state=tk.NORMAL)
            self.view.refresh_btn.config(state=tk.NORMAL)
            self.view.backup_btn.config(state=tk.NORMAL)
            
            # After 5 seconds we reset the status
            self.view.root.after(5000, lambda: self.view.update_progress(
                0, "Backup progress: not started", 0, 'backup'))

    def start_sync_with_backup(self):
        source = self.view.get_selected_source()
        targets = self.view.get_selected_targets()
        
        if not source:
            self.view.show_notification("Error", "No source device selected")
            return
            
        if not targets:
            self.view.show_notification("Error", "No target devices selected")
            return
            
        devices = self.model.get_usb_devices()
        source_device = next((d for d in devices if d['label'] == source), None)
        target_mountpoints = [d['mountpoint'] for d in devices if d['label'] in targets]
        
        if not source_device:
            self.view.show_notification("Error", "Source device not found")
            return
            
        if source in targets:
            self.view.show_notification("Error", "Source cannot be a target")
            return
            
        self.view.log_message(f"Starting sync with backup from {source} to {len(targets)} targets")
        
        self.view.sync_btn.config(state=tk.DISABLED)
        self.view.refresh_btn.config(state=tk.DISABLED)
        
        sync_thread = threading.Thread(
            target=self._perform_sync_with_backup,
            args=(source_device['mountpoint'], target_mountpoints),
            daemon=True
        )
        sync_thread.start()

    def _perform_sync_with_backup(self, source, targets):
        def progress_callback(progress, message, remaining):
            self.view.update_progress(progress, message, remaining)
        
        self.last_sync_info = self.model.sync_with_backup(
            source, targets, progress_callback
        )
        
        self.view.sync_btn.config(state=tk.NORMAL)
        self.view.refresh_btn.config(state=tk.NORMAL)

        if self.last_sync_info:
            targets_str = ", ".join([info['target'] for info in self.last_sync_info])
            self.view.log_message(f"Sync with backup completed to: {targets_str}")
            self.view.show_notification(
                "Sync Complete",
                f"Data successfully synchronized to: {targets_str}\nBackups created on target devices."
            )
        else:
            self.view.log_message("Sync failed - check device accessibility")
            self.view.show_notification(
                "Sync Failed",
                "No data was synchronized. Check if devices are accessible."
            )
        
        self.view.update_progress(0, "Ready for next operation", 0)
    
    def show_backup_history(self):
        history = self.model.backup_manager.backup_history
        if not history:
            self.view.show_notification("Info", "No backup history available")
            return
            
        history_window = tk.Toplevel(self.view.root)
        history_window.title("Backup History")
        history_window.geometry("800x500")
        
        tree = ttk.Treeview(history_window, columns=('source', 'backup_location', 'timestamp'))
        tree.heading('#0', text='#')
        tree.heading('source', text='Source')
        tree.heading('backup_location', text='Backup Location')
        tree.heading('timestamp', text='Timestamp')
        
        tree.column('#0', width=50)
        tree.column('source', width=200)
        tree.column('backup_location', width=300)
        tree.column('timestamp', width=150)
        
        for i, backup in enumerate(reversed(history), 1):
            tree.insert('', 'end', text=str(i), 
                      values=(backup['source'], backup['backup_location'], backup['timestamp']))
        
        tree.pack(fill=tk.BOTH, expand=True)

        def on_select(event):
            selected_item = tree.focus()
            if selected_item:
                item_data = tree.item(selected_item)
                backup_info = history[len(history) - int(item_data['text'])]
                
                detail_window = tk.Toplevel(history_window)
                detail_window.title(f"Backup Details #{item_data['text']}")
                
                text = tk.Text(detail_window, wrap=tk.WORD)
                text.pack(fill=tk.BOTH, expand=True)
                
                text.insert(tk.END, f"Timestamp: {backup_info['timestamp']}\n")
                text.insert(tk.END, f"Source: {backup_info['source']}\n")
                text.insert(tk.END, f"Backup Location: {backup_info['backup_location']}\n")
                text.insert(tk.END, f"\nFiles backed up ({backup_info['original_files_count']}):\n\n")
                
                for file in backup_info['backed_up_files'][:50]:
                    text.insert(tk.END, f"{file}\n")
                
                if len(backup_info['backed_up_files']) > 50:
                    text.insert(tk.END, f"\n...and {len(backup_info['backed_up_files']) - 50} more files")
        
        tree.bind('<<TreeviewSelect>>', on_select)
    
    def on_close(self):
        self.model.stop_monitoring()
        self.view.log_message("System shutdown")
