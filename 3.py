import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 目录与分类配置
extensions = {
    'Images': ['jpeg', 'jpg', 'png'],
    'PDFs': ['pdf'],
    'Datasets': ['csv', 'xlsx', 'json','xls'],
    'Videos': ['mp4']
}

# 生成所有扩展名元组
all_extensions = []
for ext_list in extensions.values():
    all_extensions.extend(ext_list)
suffixes = tuple('.' + ext for ext in all_extensions)  # 生成 ('.jpeg', '.jpg', ...)

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(suffixes):
            classify_file(event.src_path, directory)

# 初始化目录结构
def init_directories(base_path):
    for cat in extensions.keys():
        os.makedirs(os.path.join(base_path, cat), exist_ok=True)

def classify_file(src_path, base_dir):
    """文件分类逻辑"""
    filename = os.path.basename(src_path)
    # 处理没有扩展名的情况
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    for category, ext_list in extensions.items():
        if ext in ext_list:
            dest_dir = os.path.join(base_dir, category)
            base_name, ext_with_dot = os.path.splitext(filename)
            dest_filename = filename
            counter = 0
            
            # 处理文件名冲突
            while os.path.exists(os.path.join(dest_dir, dest_filename)):
                dest_filename = f"{base_name}_{counter}{ext_with_dot}"
                counter += 1
            
            try:
                os.rename(src_path, os.path.join(dest_dir, dest_filename))
                print(f"Moved {filename} to {category} as {dest_filename}")
            except OSError as e:
                print(f"移动失败 {filename}: {str(e)}")
            return

def process_existing_files(base_dir):
    """处理程序启动前已存在的文件"""
    print("\n[🔍] 开始处理现有文件...")
    processed_count = 0
    
    for filename in os.listdir(base_dir):
        file_path = os.path.join(base_dir, filename)
        
        # 跳过目录和隐藏文件
        if os.path.isdir(file_path) or filename.startswith('.'):
            continue
            
        # 只处理目标扩展名的文件
        if file_path.endswith(suffixes):
            classify_file(file_path, base_dir)
            processed_count += 1
    
    print(f"[✅] 已完成 {processed_count} 个现有文件的分类\n")

def get_user_directory():
    """获取用户输入的目录路径"""
    while True:
        path = input("请输入要监控的目录路径（例如 ~/下载）: ").strip()
        expanded_path = os.path.expanduser(path)  # 扩展 ~ 符号
        
        if os.path.exists(expanded_path):
            return expanded_path
        else:
            print(f"[❌] 目录不存在，请重新输入！")

if __name__ == "__main__":
    # 获取用户输入的目录
    directory = get_user_directory()
    print(f"[✅] 监控目录：{directory}")
    
    # 创建分类目录
    init_directories(directory)
    
    # 处理程序启动前已存在的文件
    process_existing_files(directory)
    
    # 显示初始目录状态
    if os.listdir(directory):
        print(f"[🔎] 当前目录内容:")
        for f in os.listdir(directory):
            if not f.startswith('.'):
                print(f" - {f}")
    else:
        print("[📂] 当前目录为空")
    
    # 启动文件监控
    print("\n[👁️] 启动文件监控...")
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] 停止监控...")
        observer.stop()
    observer.join()
    print("[👋] 程序已退出")

