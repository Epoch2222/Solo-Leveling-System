import requests
import pandas as pd
from packaging import version
import zipfile
import os
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import json

# --- UI CONFIGURATION ---
root = tk.Tk()
root.title("System Updater")
root.geometry("500x200")
canvas = tk.Canvas(root)
canvas.place(relwidth=1, relheight=1)
status_label = tk.Label(canvas, text="Starting update...", anchor="center", font=("Segoe UI", 11))
status_label.place(relx=0.5, rely=0.2, anchor="center")
progress = ttk.Progressbar(canvas, orient="horizontal", mode="determinate", length=300)
progress.place(relx=0.5, rely=0.5, anchor="center")
progress["maximum"] = 100
progress["value"] = 0
close_btn = tk.Button(canvas, text="Close", command=root.destroy)
close_btn.place(relx=0.5, rely=0.75, anchor="center")
close_btn.lower()

def log(msg):
    status_label.config(text=msg)
    root.update_idletasks()
    print(msg)

def finish_update():
    progress["value"] = 100
    close_btn.lift()

# --- SCRIPT CONFIGURATION ---
# URL to the JSON file that describes the patches
patches_manifest_url = "https://raw.githubusercontent.com/Epoch2222/Solo-Leveling-System/main/patches.json" # <-- Make sure this URL is correct!
local_csv_path = "version.csv"
target_directory = "."

# --- CORE FUNCTIONS ---
def create_backup(source_dir, backup_dir="Update Backup"):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")
    log(f"Creating backup at: {backup_path}")

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root_dir, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', backup_dir]]
            for file in files:
                zipf.write(os.path.join(root_dir, file), os.path.relpath(os.path.join(root_dir, file), source_dir))
    log("Backup complete.")

def get_remote_manifest(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"Error fetching remote manifest: {e}")
        return None

def get_local_version(local_path):
    try:
        df = pd.read_csv(local_path, header=None)
        return str(df.iloc[0, 0]).strip()
    except Exception:
        return "0.0.0" # Default to a base version if file doesn't exist

def download_file_with_progress(url, output_path):
    log("Downloading patch...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                percent = (downloaded / total) * 100 if total else 0
                progress["value"] = percent
                log(f"Downloading... {int(percent)}%")
    log("Download complete.")

def download_and_apply_patch(patch_url, destination):
    temp_patch_file = "__temp_patch__.diff"
    try:
        download_file_with_progress(patch_url, temp_patch_file)
        log("Applying patch...")
        patch_set = patch.fromfile(temp_patch_file)
        if patch_set and patch_set.apply(root=destination):
            log("Patch applied successfully.")
            progress["value"] = 100
            return True
        else:
            log("Failed to apply patch.")
            return False
    except Exception as e:
        log(f"An error occurred during patching: {e}")
        return False
    finally:
        if os.path.exists(temp_patch_file):
            os.remove(temp_patch_file)

def run_update_thread():
    try:
        manifest = get_remote_manifest(patches_manifest_url)
        local_ver = get_local_version(local_csv_path)
        if not manifest:
            log("Could not check for updates.")
            finish_update()
            return

        remote_ver = manifest.get("latest")
        log(f"Local version: {local_ver} | Remote version: {remote_ver}")

        if version.parse(remote_ver) > version.parse(local_ver):
            log("Newer version found.")
            patch_to_apply = next((p for p in manifest.get("patches", []) if p.get("from") == local_ver and p.get("to") == remote_ver), None)
            
            if not patch_to_apply:
                log(f"No direct patch from {local_ver} to {remote_ver}.")
                finish_update()
                return

            create_backup(target_directory)
            if download_and_apply_patch(patch_to_apply["url"], target_directory):
                with open(local_csv_path, "w") as f:
                    f.write(remote_ver)
                log("Update complete!")
            else:
                log("Update failed. Please check backup folder.")
        else:
            log("You already have the latest version.")
        
        finish_update()
    except Exception as e:
        log(f"[Update Thread] Error: {e}")
        finish_update()

if __name__ == "__main__":
    # Ensure you have the required library installed
    try:
        import patch_ng as patch
    except ImportError:
        log("Error: 'patch-ng' library not found.")
        log("Please run: pip install patch-ng")
        time.sleep(5)
        root.destroy()
    else:
        threading.Thread(target=run_update_thread, daemon=True).start()
        root.mainloop()