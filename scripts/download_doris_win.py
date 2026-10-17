import urllib.request
import os
import time
import sys

url = "https://apache-doris-releases.oss-accelerate.aliyuncs.com/apache-doris-2.1.7-bin-x64.tar.gz"
output_path = r"E:\ecom_ai\apache-doris-2.1.7-bin-x64.tar.gz"

print("正在下载 Apache Doris 2.1.7 ...")
print(f"保存到: {output_path}")
print()

start_time = time.time()
last_update = start_time
downloaded = 0
total_size = 2754 * 1024 * 1024  # 约 2754 MB

def progress_hook(block_num, block_size, total):
    global last_update, downloaded, total_size
    downloaded = block_num * block_size
    if total > 0:
        total_size = total

    now = time.time()
    if now - last_update >= 1.0:
        elapsed = now - start_time
        speed = downloaded / elapsed / 1024 / 1024 if elapsed > 0 else 0
        percent = downloaded / total_size * 100 if total_size > 0 else 0
        remaining = (total_size - downloaded) / (speed * 1024 * 1024) if speed > 0 else 0

        bar_len = 40
        filled = int(bar_len * percent / 100)
        bar = '=' * filled + '>' + '-' * (bar_len - filled - 1)

        sys.stdout.write(f'\r[{bar}] {percent:5.1f}%  {speed:.2f} MB/s  剩余 {remaining:.0f}s')
        sys.stdout.flush()
        last_update = now

try:
    urllib.request.urlretrieve(url, output_path, progress_hook)
    elapsed = time.time() - start_time
    actual_size = os.path.getsize(output_path)
    print(f'\n\n✅ 下载完成！')
    print(f'总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)')
    print(f'平均速度: {actual_size/1024/1024/elapsed:.2f} MB/s')
    print(f'文件大小: {actual_size/1024/1024:.1f} MB')
except Exception as e:
    print(f'\n\n❌ 下载失败: {e}')
    sys.exit(1)
