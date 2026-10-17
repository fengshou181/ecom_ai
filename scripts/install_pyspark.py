# -*- coding: utf-8 -*-
"""
PySpark 下载和安装脚本
带进度显示
"""
import os
import sys
import urllib.request
import subprocess
import time


def report_progress(block_num, block_size, total_size):
    """下载进度回调"""
    downloaded = block_num * block_size
    percent = downloaded / total_size * 100
    downloaded_mb = downloaded / (1024 * 1024)
    total_mb = total_size / (1024 * 1024)
    speed_mb_s = downloaded_mb / (time.time() - start_time) if start_time else 0

    bar_len = 40
    filled = int(bar_len * downloaded / total_size)
    bar = '█' * filled + '░' * (bar_len - filled)

    sys.stdout.write(f'\r下载中: |{bar}| {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB) {speed_mb_s:.2f} MB/s')
    sys.stdout.flush()


def get_pyspark_url(index_url, package_name, version):
    """从 PyPI 镜像获取包的下载 URL"""
    import json
    import urllib.request

    # 使用 JSON API 获取包信息
    pypi_url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    try:
        with urllib.request.urlopen(pypi_url, timeout=30) as resp:
            data = json.loads(resp.read().decode())

        # 找到源码包 (tar.gz)
        for file_info in data['urls']:
            if file_info['filename'].endswith('.tar.gz'):
                return file_info['url'], file_info['size']
    except Exception as e:
        print(f"从 PyPI 获取信息失败: {e}")

    return None, None


def main():
    global start_time

    package_name = "pyspark"
    version = "3.5.3"
    download_dir = r"E:\ecom_ai"
    python_exe = r"E:\HM\software\Anaconda\ancon\envs\pds\python.exe"

    os.makedirs(download_dir, exist_ok=True)
    output_file = os.path.join(download_dir, f"pyspark-{version}.tar.gz")

    print(f"正在获取 {package_name}=={version} 的下载链接...")
    url, total_size = get_pyspark_url("http://mirrors.aliyun.com/pypi/simple/", package_name, version)

    if not url:
        print("无法获取下载链接，使用备用 URL")
        url = f"https://files.pythonhosted.org/packages/source/p/pyspark/pyspark-{version}.tar.gz"
        total_size = 317 * 1024 * 1024  # 估计大小

    print(f"下载链接: {url}")
    print(f"文件大小: {total_size / (1024*1024):.1f} MB")
    print(f"保存到: {output_file}")
    print()

    # 下载
    start_time = time.time()
    try:
        urllib.request.urlretrieve(url, output_file, report_progress)
        print("\n\n下载完成！")
    except Exception as e:
        print(f"\n下载失败: {e}")
        print("尝试使用阿里云镜像...")
        # 备用方案：使用 pip 下载
        subprocess.run([
            python_exe, "-m", "pip", "download", f"{package_name}=={version}",
            "-d", download_dir,
            "-i", "http://mirrors.aliyun.com/pypi/simple/",
            "--trusted-host", "mirrors.aliyun.com",
            "--no-deps", "--default-timeout=600"
        ])

    # 验证文件
    if os.path.exists(output_file):
        actual_size = os.path.getsize(output_file)
        print(f"实际文件大小: {actual_size / (1024*1024):.1f} MB")

        # 安装
        print("\n开始安装 PySpark...")
        result = subprocess.run([
            python_exe, "-m", "pip", "install", output_file,
            "--default-timeout=600"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("安装成功！")
            # 验证
            verify_result = subprocess.run([
                python_exe, "-c", "import pyspark; print('PySpark version:', pyspark.__version__)"
            ], capture_output=True, text=True)
            print(verify_result.stdout.strip())
        else:
            print("安装失败！")
            print(result.stderr)
    else:
        print("文件不存在，安装失败")


if __name__ == "__main__":
    main()
