import base64
import re

import requests
import threading
import os
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from queue import Queue
from urllib.parse import urljoin

from tqdm import tqdm


class M3U8Downloader:
    def __init__(self, m3u8_url, sign, output_file, num_threads=4):
        self.m3u8_url = m3u8_url
        self.output_file = output_file
        self.num_threads = num_threads
        self.queue = Queue()
        self.ts_files = []
        self.IV = None
        self.sign = sign
        self.cryptor = None
        self.progress_bar = None
        self.base_url = os.path.dirname(m3u8_url) + '/'
        if not os.path.exists('tmp/'):
            os.mkdir('tmp/')
        self.delete_files_in_folder('tmp/')

    def fetch_m3u8(self):
        response = requests.get(self.m3u8_url)
        response.raise_for_status()
        try:
            if self.IV is None:
                self.IV = bytes.fromhex(re.findall('IV=0x(.*)', response.text)[0])
                self.creat_aes()
        except Exception as e:
            print(e)
        return response.text

    def creat_aes(self):
        self.cryptor = AES.new(self.decrypt_sign(self.sign), AES.MODE_CBC, self.IV)

    def parse_m3u8(self, m3u8_content):
        lines = m3u8_content.splitlines()
        for line in lines:
            if line and not line.startswith("#"):
                ts_url = urljoin(self.base_url, line)
                self.ts_files.append(ts_url)
                self.queue.put(ts_url)

    def download_ts(self, max_retries=5, retry_delay=5):
        while not self.queue.empty():
            ts_url = self.queue.get()
            ts_filename = ts_url.split("/")[-1].split('&')[0].replace('?', '_')
            retries = 0

            while retries < max_retries:
                try:
                    # 下载文件
                    response = requests.get(ts_url, timeout=10)
                    response.raise_for_status()  # 如果状态码不是200，则抛出异常
                    
                    # 解密内容
                    cont = self.cryptor.decrypt(response.content)

                    # 检查 tmp/ 目录是否存在，不存在则创建
                    if not os.path.exists('tmp'):
                        os.makedirs('tmp')

                    # 写入解密后的内容到文件
                    with open('tmp/' + ts_filename, 'wb') as f:
                        f.write(cont)

                    # 完成当前任务，退出重试循环
                    self.queue.task_done()
                    
                    # 更新进度条
                    if self.progress_bar:
                        self.progress_bar.update(1)
                    
                    break  # 成功下载后退出重试循环
                
                except requests.exceptions.RequestException as e:
                    retries += 1
                    print(f"下载 {ts_filename} 时发生错误: {e}，正在重试 {retries}/{max_retries}...")
                    if retries >= max_retries:
                        print(f"重试次数已达最大，放弃下载 {ts_filename}")
                        self.queue.task_done()  # 标记任务已完成，防止任务卡住
                        break
                    time.sleep(retry_delay)  # 等待一段时间后再重试

    def merge_ts(self):
        with open(self.output_file, 'wb') as output_file:
            for ts_url in self.ts_files:
                ts_filename = ts_url.split("/")[-1].split('&')[0].replace('?', '_')

                with open('tmp/' + ts_filename, 'rb') as ts_file:
                    output_file.write(ts_file.read())
                os.remove('tmp/' + ts_filename)

    def delete_files_in_folder(self, folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def decrypt_sign(self, sign):
        key = sign[0:32]
        iv = sign[-16:]
        cipher_text = sign[32:-16]

        key = bytes(key, 'ascii')
        iv = bytes(iv, 'ascii')
        ciphertext = ""
        for pos in range(0, len(cipher_text), 2):
            char = int(cipher_text[pos:pos + 2], 16)
            ciphertext += chr(char)
        ciphertext = ciphertext.encode('iso-8859-1')

        encrypted_data = pad(ciphertext, 16)
        # 创建AES CBC解密器
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # 使用解密器解密密文
        plaintext = cipher.decrypt(encrypted_data)
        key_decrypt = base64.b64decode(plaintext)
        return key_decrypt

    def run(self):
        m3u8_content = self.fetch_m3u8()
        self.parse_m3u8(m3u8_content)
        self.progress_bar = tqdm(total=len(self.ts_files), desc=f"Downloading ${self.output_file}")

        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.download_ts)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
        self.progress_bar.close()

        self.merge_ts()
        print(f"Download completed: {self.output_file}")
