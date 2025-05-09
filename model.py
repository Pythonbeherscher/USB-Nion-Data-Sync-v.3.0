
import os
import time
import shutil
import psutil
import threading
from tkinter import *
from BackupManager import BackupManager

####################### ===== USBModel ===== #######################
class USBModel:
    def __init__(self):
        self.connected_devices = []
        self.observer_thread = None
        self.running = False
        self.last_check = 0
        self.backup_manager = BackupManager()
        
    def get_usb_devices(self):
        """Get list of connected USB storage devices with improved detection"""
        devices = []
        for partition in psutil.disk_partitions():
            # More reliable detection of removable devices
            if ('removable' in partition.opts.lower() or 
                ('fixed' not in partition.opts.lower() and not partition.device.startswith('/snap'))):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    if usage.total > 0:  # Ignore empty devices
                        devices.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'label': self.get_device_label(partition)
                        })
                except Exception as e:
                    # print(f"Error reading device {partition.device}: {e}")
                    continue
        return devices
    
    def get_device_label(self, partition):
        """Get human-readable device label"""
        if os.name == 'posix':
            return partition.device.split('/')[-1]
        else:
            # For Windows, we get the disk label
            try:
                drive = partition.device[:2]
                import ctypes
                kernel32 = ctypes.windll.kernel32
                volume_name = ctypes.create_unicode_buffer(1024)
                kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(drive),
                    volume_name,
                    ctypes.sizeof(volume_name),
                    None, None, None, None, 0)
                return volume_name.value or drive
            except:
                return partition.device
    
    def start_monitoring(self, callback):
        """Start monitoring USB devices with optimized refresh rate"""
        self.running = True
        
        def observer():
            last_state = []
            while self.running:
                current_time = time.time()
                # We check devices only once every 10 seconds
                if current_time - self.last_check > 10:
                    current_state = self.get_usb_devices()
                    if current_state != last_state:
                        last_state = current_state
                        self.last_check = current_time
                        callback(current_state)
                time.sleep(0.1)  # Short sleep to reduce stress
        
        self.observer_thread = threading.Thread(target=observer, daemon=True)
        self.observer_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring USB devices"""
        self.running = False
        if self.observer_thread:
            self.observer_thread.join(timeout=1)
    
    def transfer_data(self, source, targets, progress_callback):
        """Improved data transfer with better error handling"""
        total_files = 0
        copied_files = 0
        start_time = time.time()
        success_targets = []
        
        # Checking the availability of the source device
        if not os.path.exists(source):
            progress_callback(0, f"Source device {source} not accessible", 0)
            return []
        
        # Counting files with error handling
        try:
            for root, _, files in os.walk(source):
                total_files += len(files)
        except Exception as e:
            progress_callback(0, f"Cannot scan source: {str(e)}", 0)
            return []
        
        if total_files == 0:
            progress_callback(100, "No files to transfer", 0)
            return []
        
        # Copy to each target device
        for target in targets:
            try:
                # Checking the availability of the target device
                if not os.path.exists(target):
                    progress_callback(0, f"Target {target} not accessible", 0)
                    continue
                
                # Creating a target directory
                target_dir = os.path.join(target, os.path.basename(source.rstrip(os.sep)))
                
                # Copying files
                for root, dirs, files in os.walk(source):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(root, source)
                        dst_path = os.path.join(target_dir, rel_path, file)
                        
                        try:
                            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                            shutil.copy2(src_path, dst_path)
                            copied_files += 1
                            
                            # Progress update
                            progress = (copied_files / (total_files * len(targets))) * 100
                            elapsed = time.time() - start_time
                            remaining = (elapsed / max(1, progress)) * (100 - progress) if progress > 0 else 0
                            progress_callback(progress, f"Copying to  {os.path.basename(target)}...", remaining)
                            
                        except Exception as e:
                            print(f"Error copying {src_path} to {dst_path}: {e}")
                            continue
                
                success_targets.append(os.path.basename(target))
                
            except Exception as e:
                print(f"Error during transfer to {target}: {e}")
                continue
        
        return success_targets

    def sync_with_backup(self, source, targets, progress_callback):
        total_files = 0
        copied_files = 0
        start_time = time.time()
        success_targets = []
        
        if not os.path.exists(source):
            progress_callback(0, f"Source device {source} not accessible", 0)
            return []
        
        try:
            for root, _, files in os.walk(source):
                total_files += len(files)
        except Exception as e:
            progress_callback(0, f"Cannot scan source: {str(e)}", 0)
            return []
        
        if total_files == 0:
            progress_callback(100, "No files to synchronize", 0)
            return []
        
        for target in targets:
            try:
                if not os.path.exists(target):
                    progress_callback(0, f"Target {target} not accessible", 0)
                    continue
                
                backup_info = self.backup_manager.create_backup(source, target)
                if not backup_info:
                    progress_callback(0, f"Backup failed for {target}", 0)
                    continue
                
                target_dir = os.path.join(target, os.path.basename(source.rstrip(os.sep)))
                os.makedirs(target_dir, exist_ok=True)
                
                for root, dirs, files in os.walk(source):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(root, source)
                        dst_path = os.path.join(target_dir, rel_path, file)
                        
                        copy_needed = True
                        
                        if os.path.exists(dst_path):
                            src_stat = os.stat(src_path)
                            dst_stat = os.stat(dst_path)
                            
                            if (src_stat.st_size == dst_stat.st_size and 
                                src_stat.st_mtime <= dst_stat.st_mtime):
                                copy_needed = False
                        
                        if copy_needed:
                            try:
                                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                                shutil.copy2(src_path, dst_path)
                                copied_files += 1
                            except Exception as e:
                                print(f"Error copying {src_path} to {dst_path}: {e}")
                                continue
                        
                        progress = (copied_files / total_files) * 100
                        elapsed = time.time() - start_time
                        remaining = (elapsed / max(1, progress)) * (100 - progress) if progress > 0 else 0
                        status_msg = f"Syncing to {os.path.basename(target)}: {copied_files} files"
                        progress_callback(progress, status_msg, remaining)
                
                success_targets.append({
                    'target': os.path.basename(target),
                    'backup_info': backup_info
                })
                
            except Exception as e:
                print(f"Error during sync to {target}: {e}")
                continue
        
        return success_targets
