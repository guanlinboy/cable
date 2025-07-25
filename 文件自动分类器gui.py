import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 目录与分类配置 (可以考虑让用户在GUI中自定义，但这里为简化先固定)
CONFIG_EXTENSIONS = {
    'Images': ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'webp'],
    'PDFs': ['pdf'],
    'Datasets': ['csv', 'xlsx', 'json', 'xls', 'tsv', 'xml', 'sql'],
    'Videos': ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv'],
    'Audio': ['mp3', 'wav', 'aac', 'flac', 'ogg'],
    'Documents': ['doc', 'docx', 'txt', 'rtf', 'odt', 'ppt', 'pptx', 'xls', 'xlsx'],
    'Archives': ['zip', 'rar', '7z', 'tar', 'gz'],
    'Executables': ['exe', 'msi', 'dmg', 'app'],
    'Code': ['py', 'java', 'c', 'cpp', 'js', 'html', 'css', 'php', 'rb', 'go']
}

# 生成所有扩展名元组
ALL_SUFFIXES = tuple('.' + ext for ext_list in CONFIG_EXTENSIONS.values() for ext in ext_list)

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("文件自动分类器")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window closing

        self.monitor_directory = tk.StringVar()
        self.observer = None
        self.is_monitoring = False
        self.event_handler = None

        self._create_widgets()

    def _create_widgets(self):
        # Frame for directory selection
        dir_frame = tk.Frame(self.root, padx=10, pady=10)
        dir_frame.pack(fill=tk.X)

        tk.Label(dir_frame, text="监控目录:").pack(side=tk.LEFT, padx=5)
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.monitor_directory, width=60, state='readonly')
        self.dir_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.select_dir_button = tk.Button(dir_frame, text="选择目录", command=self.select_directory)
        self.select_dir_button.pack(side=tk.LEFT, padx=5)

        # Frame for control buttons
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=tk.X)

        self.start_button = tk.Button(control_frame, text="启动监控", command=self.start_monitoring, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.stop_button = tk.Button(control_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.process_existing_button = tk.Button(control_frame, text="处理现有文件", command=self.process_existing_files_threaded, state=tk.DISABLED)
        self.process_existing_button.pack(side=tk.LEFT, padx=10, pady=5)

        # Log Text Area
        log_frame = tk.LabelFrame(self.root, text="日志", padx=10, pady=10)
        log_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, state='disabled', wrap=tk.WORD)
        self.log_text.pack(expand=True, fill=tk.BOTH)

        self.log_message("[✅] 欢迎使用文件自动分类器！请选择要监控的目录。")

    def log_message(self, message):
        """Append a message to the log text area."""
        global root # Ensure root is accessible for after()
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # Scroll to the end
        self.log_text.config(state='disabled')
        self.root.update_idletasks() # Force update the GUI

    def select_directory(self):
        initial_dir = os.path.expanduser('~') # Default to user's home directory
        directory = filedialog.askdirectory(initialdir=initial_dir)
        if directory:
            self.monitor_directory.set(directory)
            self.log_message(f"[✅] 已选择监控目录: {directory}")
            self.start_button.config(state=tk.NORMAL)
            self.process_existing_button.config(state=tk.NORMAL)
        else:
            self.log_message("[❌] 未选择目录。")
            self.start_button.config(state=tk.DISABLED)
            self.process_existing_button.config(state=tk.DISABLED)

    def _init_directories(self, base_path):
        """Initialize category directories."""
        for cat in CONFIG_EXTENSIONS.keys():
            path = os.path.join(base_path, cat)
            try:
                os.makedirs(path, exist_ok=True)
                self.log_message(f"  - 确保目录存在: {cat}")
            except OSError as e:
                self.log_message(f"[❌] 无法创建目录 {path}: {e}")

    def _classify_file(self, src_path, base_dir):
        """File classification logic."""
        filename = os.path.basename(src_path)
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        for category, ext_list in CONFIG_EXTENSIONS.items():
            if ext in ext_list:
                dest_dir = os.path.join(base_dir, category)
                base_name, ext_with_dot = os.path.splitext(filename)
                dest_filename = filename
                counter = 0
                
                # Handle filename conflict
                while os.path.exists(os.path.join(dest_dir, dest_filename)):
                    dest_filename = f"{base_name}_{counter}{ext_with_dot}"
                    counter += 1
                
                try:
                    os.rename(src_path, os.path.join(dest_dir, dest_filename))
                    self.root.after(0, self.log_message, f"[✔️] 移动 {filename} 到 {category} (as {dest_filename})")
                except OSError as e:
                    self.root.after(0, self.log_message, f"[❌] 移动失败 {filename}: {str(e)}")
                return # File classified, exit

        # If loop finishes, file was not classified
        self.root.after(0, self.log_message, f"[ℹ️] 文件 {filename} 未找到匹配的分类规则。")


    def process_existing_files_threaded(self):
        """Start processing existing files in a new thread."""
        monitor_dir = self.monitor_directory.get()
        if not monitor_dir:
            self.log_message("[⚠️] 请先选择监控目录。")
            return
        
        self.log_message("\n[🔍] 开始处理现有文件...")
        # Disable buttons during processing to prevent re-triggering
        self.process_existing_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

        thread = threading.Thread(target=self._process_existing_files_task, args=(monitor_dir,))
        thread.daemon = True # Allow the program to exit even if this thread is running
        thread.start()

    def _process_existing_files_task(self, base_dir):
        """Task to process existing files (runs in a separate thread)."""
        processed_count = 0
        try:
            for filename in os.listdir(base_dir):
                file_path = os.path.join(base_dir, filename)
                
                if os.path.isdir(file_path): # Skip directories
                    continue
                
                # Only process files with a recognized suffix and that are NOT in a category directory
                if file_path.lower().endswith(ALL_SUFFIXES):
                    # Check if the file is already in a category directory
                    is_in_category_dir = False
                    for category in CONFIG_EXTENSIONS.keys():
                        if os.path.dirname(file_path) == os.path.join(base_dir, category):
                            is_in_category_dir = True
                            break
                    
                    if not is_in_category_dir:
                        self._classify_file(file_path, base_dir)
                        processed_count += 1
        except Exception as e:
            self.root.after(0, self.log_message, f"[❌] 处理现有文件时发生错误: {e}")
        finally:
            self.root.after(0, self.log_message, f"[✅] 已完成 {processed_count} 个现有文件的分类。")
            # Restore button states based on current monitoring status
            current_monitor_dir = self.monitor_directory.get()
            if current_monitor_dir and not self.is_monitoring:
                self.start_button.config(state=tk.NORMAL)
                self.process_existing_button.config(state=tk.NORMAL)
            if self.is_monitoring:
                self.stop_button.config(state=tk.NORMAL)


    def start_monitoring(self):
        monitor_dir = self.monitor_directory.get()
        if not monitor_dir:
            messagebox.showwarning("警告", "请先选择要监控的目录！")
            return

        if self.is_monitoring:
            self.log_message("[ℹ️] 监控已在运行中。")
            return

        self.log_message("\n[🔄] 正在启动监控...")
        self._init_directories(monitor_dir) # Ensure categories exist

        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_created = lambda event: self._on_fs_event(event, monitor_dir)
        
        self.observer = Observer()
        self.observer.schedule(self.event_handler, monitor_dir, recursive=True)

        try:
            self.observer.start()
            self.is_monitoring = True
            self.log_message(f"[👁️] 成功启动监控目录: {monitor_dir}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.select_dir_button.config(state=tk.DISABLED)
            self.process_existing_button.config(state=tk.DISABLED)
        except Exception as e:
            self.log_message(f"[❌] 启动监控失败: {e}")
            self.stop_monitoring() # Clean up
            messagebox.showerror("错误", f"无法启动监控服务: {e}\n请检查目录权限或是否已被其他程序占用。")
            
    def _on_fs_event(self, event, base_dir):
        """Internal callback for watchdog events."""
        if not event.is_directory and event.src_path.lower().endswith(ALL_SUFFIXES):
            # Use root.after to run _classify_file in the main thread
            # This is safer for GUI updates and potential file system operations
            # Note: _classify_file itself will then use root.after for its logs
            self.root.after(100, lambda: self._classify_file(event.src_path, base_dir))


    def stop_monitoring(self):
        if not self.is_monitoring:
            self.log_message("[ℹ️] 监控未在运行。")
            return

        self.log_message("[🛑] 正在停止监控...")
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5) # Wait for thread to finish, with a timeout
            if self.observer.is_alive():
                self.log_message("[⚠️] 观察者线程未能正常停止，可能需要手动终止程序。")
            self.observer = None
        self.is_monitoring = False
        self.log_message("[👋] 监控已停止。")
        self.start_button.config(state=tk.NORMAL if self.monitor_directory.get() else tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.select_dir_button.config(state=tk.NORMAL)
        self.process_existing_button.config(state=tk.NORMAL if self.monitor_directory.get() else tk.DISABLED)

    def on_closing(self):
        """Handle window closing event."""
        if self.is_monitoring:
            if messagebox.askyesno("退出确认", "监控正在运行。确定要停止并退出吗？"):
                self.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()
