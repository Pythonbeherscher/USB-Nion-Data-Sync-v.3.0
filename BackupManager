import os
import json
import shutil
from datetime import datetime

####################### ===== BackupManager ===== #######################
class BackupManager:
    def __init__(self):
        self.backup_history = []
        self.load_history()
    
    def load_history(self):
        if os.path.exists('backup_history.json'):
            with open('backup_history.json', 'r') as f:
                self.backup_history = json.load(f)
    
    def save_history(self):
        with open('backup_history.json', 'w') as f:
            json.dump(self.backup_history, f, indent=2)
    
    def create_backup(self, source, target):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(target, f"USB_Backup_{timestamp}")
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            backed_up_files = []
            
            for root, _, files in os.walk(source):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, source)
                    dst_path = os.path.join(backup_dir, rel_path, file)
                    
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    backed_up_files.append(dst_path)
            
            backup_info = {
                'timestamp': timestamp,
                'source': source,
                'backup_location': backup_dir,
                'backed_up_files': backed_up_files,
                'original_files_count': len(backed_up_files)
            }
            
            self.backup_history.append(backup_info)
            self.save_history()
            return backup_info
            
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
