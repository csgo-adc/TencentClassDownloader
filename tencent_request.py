import requests
import json
import logging
from enum import Enum

logging.basicConfig(filename='log/output.log',
                    level=logging.INFO,
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
logger = logging.getLogger(__name__)


class clarityResolution(Enum):
    HIGH = 1
    MID = 2
    LOW = 3


class TencentRequest(object):

    def __init__(self, cid, term_id_list):
        self.cookie = None
        self.cid = str(cid)
        self.tid = str(term_id_list)
        self.load_cookie()
        self.header = {
            'Referer': f'https://ke.qq.com/webcourse/${self.cid}/${self.tid}',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Cookie": self.cookie
        }

    def load_cookie(self):
        try:
            with open('cookie', 'r') as f:
                self.cookie = f.read().strip()
        except Exception as e:
            print("load cookie failed")
            logger.error(e)

    def get_course_list(self):
        terms_url = "https://ke.qq.com/cgi-bin/course/get_terms_detail?cid=" + self.cid + "&term_id_list=%5B" + self.tid + "%5D&bkn=&preload=1"
        content = requests.get(terms_url, headers=self.header).text
        tlist = json.loads(content)
        chapters_list = tlist['result']['terms'][0]['chapter_info']
        sub_info = []
        for chapter in chapters_list:
            sub_info.append(chapter['sub_info'])
        return sub_info

    def get_course_info(self, cid, tid, vid, qq, r: clarityResolution = clarityResolution.LOW):
        m3u8_url = ""
        course_url = "https://ke.qq.com/cgi-proxy/rec_video/describe_rec_video?course_id=" + cid + "&file_id=" + vid + "&header=%7B%22srv_appid%22%3A201%2C%22cli_appid%22%3A%22ke%22%2C%22uin%22%3A%22" + qq + "%22%2C%22cli_info%22%3A%7B%22cli_platform%22%3A3%7D%7D&term_id=" + tid + "&vod_type=0"
        try:
            res = requests.get(course_url, headers=self.header).text
            course_info = json.loads(res)
            video_list = course_info['result']['rec_video_info']['infos']
            video_list.sort(key=lambda x: x['size'])
            if r == clarityResolution.LOW:
                m3u8_url = video_list[0].get('url')
            elif r == clarityResolution.HIGH:
                m3u8_url = video_list[-1].get('url')
            elif r == clarityResolution.MID:
                length = len(video_list)
                if length == 3:
                    m3u8_url = video_list[1].get('url')
                elif length < 3:
                    m3u8_url = video_list[0].get('url')
                else:
                    m3u8_url = video_list[int(length / 2)].get('url')

            sign = course_info['result']['rec_video_info']['d_sign']
            return m3u8_url, sign
        except Exception as e:
            print(e)
            logger.error(f'get_course_info failed, error = ${str(e)}')
            return None, None
