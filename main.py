import configparser
import os.path

from tqdm import tqdm

from download_manager import M3U8Downloader
from tencent_request import TencentRequest, clarityResolution

config = configparser.ConfigParser()
config.read('config.conf')


class TencentClassDownloader(object):
    def __init__(self):
        self.cid = None
        self.term_id = None
        self.qq = None
        self.process_num = 4
        self.clarity = clarityResolution.HIGH
        self.save_path = None
        self.download_list = []
        self.parser_conf()

    def parser_conf(self):
        self.qq = config['QQ']['number']
        self.process_num = int(config['process']['process_num'])
        self.save_path = config['output']['save_path']
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        clarity = config['clarity']['clarity']
        if clarity == '3':
            self.clarity = clarityResolution.LOW
        elif clarity == '2':
            self.clarity = clarityResolution.MID
        else:
            self.clarity = clarityResolution.HIGH

        url = config['url']['url']
        url = url.split('/')
        self.cid = url[-2]
        self.term_id = url[-1].split('#')[0]

    def creat_download_info(self):
        cid = self.cid
        term_id_list = self.term_id
        t = TencentRequest(cid, term_id_list)
        chapter_list = t.get_course_list()

        for chapter_info in chapter_list:
            for term_info in chapter_info:
                task_info = term_info['task_info']
                for course in task_info:
                    if 'resid_list' in course:
                        course_name = course['name']
                        resid_list = course['resid_list']
                        if isinstance(resid_list, str):
                            video_id = resid_list
                            m3u8_url, sign = t.get_course_info(cid, term_id_list, video_id, self.qq, self.clarity)
                            if m3u8_url is None or sign is None:
                                continue
                            download_info = {
                                'course_name': course_name,
                                'cid': cid,
                                'term_id': term_id_list,
                                'video_id': video_id,
                                'm3u8_url': m3u8_url,
                                'sign': sign
                            }
                            self.download_list.append(download_info)

                        elif isinstance(resid_list, list):
                            for resid in resid_list:
                                video_id = resid

                                m3u8_url, sign = t.get_course_info(cid, term_id_list, video_id, self.qq, self.clarity)
                                if m3u8_url is None or sign is None:
                                    continue
                                if len(resid_list) > 1:
                                    c_name = course_name + '_' + video_id
                                else:
                                    c_name = course_name
                                download_info = {
                                    'course_name': c_name,
                                    'cid': cid,
                                    'term_id': term_id_list,
                                    'video_id': video_id,
                                    'm3u8_url': m3u8_url,
                                    'sign': sign
                                }
                                self.download_list.append(download_info)

    def download(self):
        for video_info in tqdm(self.download_list):
            file_name = self.save_path + video_info['course_name'] + '.mp4'
            m3u8_url = video_info['m3u8_url']
            sign = video_info['sign']
            if os.path.exists(file_name):
                print(f'The file ${file_name} has been download, jump...')
                continue
            dm = M3U8Downloader(m3u8_url, sign, file_name, self.process_num)
            dm.run()


if __name__ == '__main__':
    pp = TencentClassDownloader()
    pp.creat_download_info()
    pp.download()
