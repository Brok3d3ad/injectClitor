import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import psutil
import subprocess
import os
import shutil
from datetime import datetime
import time
import sys
import tempfile
import atexit
import glob
from pathlib import Path

class SimpleInjector:
    def __init__(self, root):
        self.root = root
        self.root.title("MechsEarth DLL Injector")
        self.root.geometry("400x600")
        
        # Store temp directory path if we're running from PyInstaller
        if getattr(sys, 'frozen', False):
            self.temp_dir = getattr(sys, '_MEIPASS', None)
        else:
            self.temp_dir = None
            
        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Optional: Set minimum window size
        self.root.minsize(400, 600)
        
        # Make sure window is in front when launched
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)

        # Create main frame
        self.frame = ttk.Frame(root, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Add logo
        try:
            # Get the directory where the script/exe is located
            if getattr(sys, 'frozen', False):
                # If running as compiled exe
                application_path = sys._MEIPASS
            else:
                # If running as script
                application_path = os.path.dirname(os.path.abspath(__file__))
                
            logo_path = os.path.join(application_path, "logo.png")
            logo_image = Image.open(logo_path)
            # Resize image if needed (e.g., to 200x200)
            logo_image = logo_image.resize((200, 200), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)
            
            # Create label and display image
            logo_label = ttk.Label(self.frame, image=logo_photo)
            logo_label.image = logo_photo  # Keep a reference!
            logo_label.pack(pady=10)
        except Exception as e:
            print(f"Could not load logo: {e}")

        # Create listbox for PIDs with disabled state
        self.pid_list = tk.Listbox(self.frame, state='disabled', font=('Courier', 10))
        self.pid_list.pack(fill=tk.BOTH, expand=True, pady=5)

        # Buttons
        ttk.Button(self.frame, text="Refresh PIDs", command=self.refresh_pids).pack(fill=tk.X, pady=5)
        ttk.Button(self.frame, text="Inject All", command=self.inject_all).pack(fill=tk.X, pady=5)
        ttk.Button(self.frame, text="Clear Cache", command=self.clear_cache).pack(fill=tk.X, pady=5)

        # Initial PID list population
        self.refresh_pids()

        # Add this after creating the root window
        try:
            if getattr(sys, 'frozen', False):
                # If running as compiled exe
                application_path = sys._MEIPASS
            else:
                # If running as script
                application_path = os.path.dirname(os.path.abspath(__file__))
                
            icon_path = os.path.join(application_path, "logo.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set window icon: {e}")

    def refresh_pids(self):
        self.pid_list.config(state='normal')  # Temporarily enable to update
        self.pid_list.delete(0, tk.END)
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == 'mechsearth.exe':
                    # Get more detailed process info
                    process = psutil.Process(proc.info['pid'])
                    create_time = datetime.fromtimestamp(process.create_time()).strftime('%H:%M:%S')
                    entry = f"PID: {proc.info['pid']} | {proc.info['name']} | Started: {create_time}"
                    self.pid_list.insert(tk.END, entry)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        self.pid_list.config(state='disabled')  # Disable after updating

    def inject_all(self):
        if self.pid_list.size() == 0:
            messagebox.showerror("Error", "No MechsEarth processes found.\nPlease make sure the game is running and click 'Refresh PIDs'.")
            return

        # Get the correct directory whether running as exe or script
        try:
            if getattr(sys, 'frozen', False):
                # If running as compiled exe
                current_dir = sys._MEIPASS
            else:
                # If running as script
                current_dir = os.path.dirname(os.path.abspath(__file__))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get current directory:\n{str(e)}")
            return

        # Build paths for required files
        injector_path = os.path.join(current_dir, "injector.exe")
        dll_path = os.path.join(current_dir, "active_window.dll")

        # Debug info
        print(f"Looking for files in: {current_dir}")
        print(f"Injector path: {injector_path}")
        print(f"DLL path: {dll_path}")

        # Check if files exist
        missing_files = []
        if not os.path.exists(injector_path):
            missing_files.append(f"injector.exe (looked in {current_dir})")
        if not os.path.exists(dll_path):
            missing_files.append(f"active_window.dll (looked in {current_dir})")
            
        if missing_files:
            error_msg = "Required files not found:\n"
            error_msg += "\n".join(missing_files)
            error_msg += "\n\nPlease ensure all files are in the same directory as the application."
            messagebox.showerror("Error", error_msg)
            return

        success_count = 0
        fail_count = 0
        error_details = []

        for i in range(self.pid_list.size()):
            # Extract PID from the format "PID: XXXXX | MechsEarth.exe | Started: HH:MM:SS"
            entry = self.pid_list.get(i)
            try:
                pid = int(entry.split("|")[0].split(":")[1].strip())
            except Exception as e:
                error_details.append(f"Failed to parse PID from entry: {entry}\nError: {str(e)}")
                fail_count += 1
                continue
            
            command = [injector_path, str(pid), dll_path]
            
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=10  # 10 second timeout
                )
                
                if result.returncode == 0:
                    success_count += 1
                else:
                    fail_count += 1
                    error_msg = f"Failed - PID {pid}\nError: {result.stderr if result.stderr else result.stdout}"
                    error_details.append(error_msg)
                
                # Add 2-second delay between injections
                if i < self.pid_list.size() - 1:  # Don't wait after the last injection
                    self.root.update()  # Update GUI
                    time.sleep(2)
                
            except subprocess.TimeoutExpired:
                fail_count += 1
                error_details.append(f"Timeout - PID {pid}\nInjection took too long to complete")
            except Exception as e:
                fail_count += 1
                error_details.append(f"Exception while injecting PID {pid}:\n{str(e)}")

        # Show detailed results
        result_message = f"Injection completed\n\nSuccesses: {success_count}\nFailures: {fail_count}"
        
        if error_details:
            result_message += "\n\nError Details:"
            for error in error_details:
                result_message += f"\n\n{error}"
                
        if fail_count > 0:
            messagebox.showerror("Injection Results", result_message)
        else:
            messagebox.showinfo("Success", result_message)

    def clear_cache(self):
        """Clear PyInstaller temporary folders from the temp directory"""
        temp_dir = Path(tempfile.gettempdir())
        mei_folders = list(temp_dir.glob("_MEI*"))
        
        if not mei_folders:
            messagebox.showinfo("Cache Clear", "No cache folders found to clear.")
            return
            
        cleared = []
        failed = []
        
        for folder in mei_folders:
            try:
                shutil.rmtree(folder, ignore_errors=True)
                cleared.append(folder.name)
            except Exception as e:
                failed.append(f"{folder.name}: {str(e)}")
        
        # Prepare result message
        message = "Cache Clearing Results:\n\n"
        
        if cleared:
            message += "Successfully cleared:\n"
            message += "\n".join(f"- {folder}" for folder in cleared)
            message += f"\n\nTotal cleared: {len(cleared)}"
        
        if failed:
            message += "\n\nFailed to clear:\n"
            message += "\n".join(f"- {error}" for error in failed)
            message += f"\n\nTotal failed: {len(failed)}"
            
        if cleared:
            messagebox.showinfo("Cache Clear", message)
        else:
            messagebox.showerror("Cache Clear", message)

    def on_closing(self):
        try:
            # Disable all cleanup of pkg_resources
            if 'pkg_resources' in sys.modules:
                sys.modules['pkg_resources'].cleanup_resources = lambda *args, **kwargs: None
                
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            sys.exit(0)

def main():
    root = tk.Tk()
    app = SimpleInjector(root)
    root.mainloop()

if __name__ == "__main__":
    main()