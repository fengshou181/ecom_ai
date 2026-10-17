import json
import urllib.request
import os
import time
import sys

# 从 PyPI 获取下载链接
url = 'https://pypi.org/pypi/pyspark/3.5.3/json'
print('正在获取 PySpark 下载链接...')
try:
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    
    download_url = None
    file_size = 0
    for f in data['urls']:
        if f['filename'].endswith('.tar.gz'):
            download_url = f['url']
            file_size = f['size']
            print(f'文件名: {f["filename"]}')
            print(f'大小: {file_size/1024/1024:.1f} MB')
            print(f'URL: {download_url}')
            break
except Exception as e:
    print(f'从 PyPI 获取失败: {e}')
    sys.exit(1)

# 下载文件
output_file = r'E:\ecom_ai\pyspark-3.5.3.tar.gz'
print(f'\n开始下载到: {output_file}')

start_time = time.time()
last_update = start_time
downloaded = 0

def progress_hook(block_num, block_size, total_size):
    global last_update, downloaded
    downloaded = block_num * block_size
    now = time.time()
    
    # 每秒更新一次
    if now - last_update >= 1.0:
        elapsed = now - start_time
        speed = downloaded / elapsed / 1024 / 1024 if elapsed > 0 else 0
        percent = downloaded / total_size * 100 if total_size > 0 else 0
        remaining = (total_size - downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
        
        bar_len = 30
        filled = int(bar_len * percent / 100)
        bar = '=' * filled + '>' + '-' * (bar_len - filled - 1)
        
        sys.stdout.write(f'\r[{bar}] {percent:5.1f}%  {speed:.2f} MB/s  剩余 {remaining:.0f}s')
        sys.stdout.flush()
        last_update = now

try:
    urllib.request.urlretrieve(download_url, output_file, progress_hook)
    elapsed = time.time() - start_time
    print(f'\n\n下载完成！')
    print(f'总耗时: {elapsed:.1f} 秒')
    print(f'平均速度: {file_size/1024/1024/elapsed:.2f} MB/s')
    print(f'文件大小: {os.path.getsize(output_file)/1024/1024:.1f} MB')
except Exception as e:
    print(f'\n下载失败: {e}')
    sys.exit(1)
