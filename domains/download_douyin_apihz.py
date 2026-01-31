from pathlib import Path
import requests
import re
import json
import os
import time
import random
from tqdm import tqdm
from urllib.parse import urlparse
from .config import Config
from fake_useragent import UserAgent        
import requests


class DouyinDownloader:
    def __init__(self,cookie,share_url):

        general_headers = self._generate_headers()
        specail_headers =   {          
            'Referer': 'https://www.douyin.com/',
            'Cookie': cookie
            }
        
        self.headers = {**general_headers,**specail_headers}
        
        self.api_url = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
        
        self.share_rul = share_url
       


    def _generate_headers(self):
        """生成逻辑一致的请求头，确保 User-Agent 和 sec-ch-ua 内容不冲突"""
        # 创建动态 UA 生成器（自动保持浏览器版本一致性）
        ua = UserAgent(min_version=124)  # 限定最低版本为 Chrome 124
        
        # 构建核心浏览器标识（确保两种字段内容一致）
        chrome_version = "124"  # 统一版本号
        platform = "Windows"    # 统一操作系统
        
        return {
            # 传统 User-Agent（包含完整设备信息）
            'User-Agent': f'Mozilla/5.0 ({platform}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
            
            # 客户端提示头（结构化浏览器品牌信息）
            'sec-ch-ua': f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',  # 非移动设备
            'sec-ch-ua-platform': f'"{platform}"',
            
            # 补充标准协议头
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }

 
        
    def get_video_id(self, share_url: str) -> str:
        """解析抖音分享链接获取视频ID（自动处理重定向）"""
        session = requests.Session()
        try:
            # 处理短链接重定向
            resp = session.head(share_url, headers=self.headers, allow_redirects=True, timeout=10)
            final_url = resp.url
            # 正则匹配视频ID（适配多种链接格式）
            video_id = re.search(r'/video/(\d+)|/v\.douyin\.com/(\w+)', final_url)
            if video_id:
                return video_id.group(1) or video_id.group(2)
            else:
                raise ValueError("未在链接中发现视频ID")
        except Exception as e:
            raise ConnectionError(f"链接解析失败: {str(e)}")

    
    def get_douyin_url(self,video_id):
        uid = Config.apihz_uid # 替换为实际uid
        key = Config.apihz_key # 替换为实际key
        video_url = f"https://www.douyin.com/video/{video_id}"

        api = "https://cn.apihz.cn/api/fun/douyin.php"
        params = {
            "id": uid,    # 替换为你的uid
            "key": key,   # 替换为你的key
            "url": video_url
        }
        response = requests.get(api, params=params).json()
        if response["code"] == 200:
            return response["yvideo"]  # 长期有效的无水印地址
        else:
            raise Exception(f"解析失败: {response.get('msg')}")       


    def download_video(self, video_url: str, filename: str = "douyin_video.mp4"):
        """流式下载视频文件并显示进度条[2,4](@ref)"""
        readme_path = Path( filename).with_suffix(".txt")   #.split(".")[0]+"_url.txt"
        with open(readme_path, 'w',encoding="utf-8") as f:
            f.write(video_url)
        
        response = requests.get(video_url, headers=self.headers, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f:
            with tqdm(
                total=total_size, 
                unit='B', 
                unit_scale=True,
                desc=f"下载 {filename}"
            ) as pbar:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

    def _random_delay(self):
        """随机延迟（0.5~2秒）规避反爬机制"""
        time.sleep(random.uniform(0.5, 2.0))

    def process(self, share_url: str, output_path: str = None):
        """主处理流程：输入分享链接 → 输出视频文件"""
        share_url = self.share_rul
        try:
            print("正在解析链接...")
            video_id = self.get_video_id(share_url)
            print(f"获取视频ID: {video_id}")
            
            print("请求视频数据...")
            video_url = self.get_douyin_url(video_id)
            print(f"无水印链接: {video_url}")
            
            filename = output_path+f"/douyin_{video_id}.mp4"
            print("视频下载开始...")
            self.download_video(video_url, filename)
            
            print(f"视频下载完成:: {os.path.abspath(filename)}")
            return True
        except Exception as e:
            print(f"错误: {str(e)}")
            return False

if __name__ == "__main__":
    share_url = "https://v.douyin.com/pLUxFnfbvus/ I@v.FH"
    cookies = "=douyin.com; xg_device_score=7.601412568506403; device_web_cpu_core=8; device_web_memory_size=8; architecture=amd64; UIFID_TEMP=c8c20d54553eadab8c678961c2b0df95555df87bbc6b890988ad105aec15abc0d02e312c2894abf6426f6937fe020b7c93a115dfa120832c09ad5993afc7c57fe8e35f032a18ff40a85b83c196e7d878; fpk1=U2FsdGVkX19FL0DbkPGdrIRSVHdTn1giU/Esoi97z+/itmVnwCOK8HhxO5WithT0QO5upCftkz5o3LfTdlqu9Q==; fpk2=8369da3c75ccd12bc017791df73a85c8; xgplayer_device_id=35632193858; xgplayer_user_id=291173461503; UIFID=c8c20d54553eadab8c678961c2b0df95555df87bbc6b890988ad105aec15abc0d02e312c2894abf6426f6937fe020b7c8763fab2a9a28e0350abcf27ec08de93184a274b2f7ed773913f1d6b15577114395a14cde69d9acdd0a0e85b3f5fcbb97873c101369a320653e20a1d587b504e1096aa501da4c3ee40b28979218677944f53febacbf479bd558f003d5b712cd0773e8996b9d8d99d0e2287d340074228; bd_ticket_guard_client_web_domain=2; d_ticket=d40e04630cca992510b4cadf13620f0ef9d6d; is_staff_user=false; login_time=1747312070163; SelfTabRedDotControl=%5B%5D; SEARCH_RESULT_LIST_TYPE=%22single%22; passport_assist_user=CkxXY2Cd1GDkQ11-xAz1JpkGrGF4ULa3mpDrdfjKxez9yfHYN5BJ_ZNyqiVqZV1weHUaM34WfTiJgw8ynpJClAX7l2cVySe2iCcbYuj7GkoKPAAAAAAAAAAAAABPAUgotzM4eVv6CpLs3uO0gFTuMj1QtlnoFQB8F5PEuQHTe-5BxafeMFaI7vFuuee81BCbzPENGImv1lQgASIBAxFGeJg%3D; n_mh=9-mIeuD4wZnlYrrOvfzG3MuT6aQmCUtmr8FxV8Kl8xY; uid_tt=f5300c2930c46e91852485f20505dbf0; uid_tt_ss=f5300c2930c46e91852485f20505dbf0; sid_tt=b7834126706ba6d8d9983231c4e07994; sessionid=b7834126706ba6d8d9983231c4e07994; sessionid_ss=b7834126706ba6d8d9983231c4e07994; __druidClientInfo=JTdCJTIyY2xpZW50V2lkdGglMjIlM0ExMTEyJTJDJTIyY2xpZW50SGVpZ2h0JTIyJTNBNTA4JTJDJTIyd2lkdGglMjIlM0ExMTEyJTJDJTIyaGVpZ2h0JTIyJTNBNTA4JTJDJTIyZGV2aWNlUGl4ZWxSYXRpbyUyMiUzQTEuNSUyQyUyMnVzZXJBZ2VudCUyMiUzQSUyMk1vemlsbGElMkY1LjAlMjAoV2luZG93cyUyME5UJTIwMTAuMCUzQiUyMFdpbjY0JTNCJTIweDY0KSUyMEFwcGxlV2ViS2l0JTJGNTM3LjM2JTIwKEtIVE1MJTJDJTIwbGlrZSUyMEdlY2tvKSUyMENocm9tZSUyRjEzNi4wLjAuMCUyMFNhZmFyaSUyRjUzNy4zNiUyMEVkZyUyRjEzNi4wLjAuMCUyMiU3RA==; enter_pc_once=1; x-hng=lang=zh-CN&domain=www.douyin.com; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.6%7D; sid_guard=b7834126706ba6d8d9983231c4e07994%7C1752483773%7C5184000%7CFri%2C+12-Sep-2025+09%3A02%3A53+GMT; sid_ucp_v1=1.0.0-KDA3MGYzODJmNTA1ODQ4ZTQyNTI5MGI0OWVhM2JiMTE3ZDU2ZDhiZDAKIQjwqYD1-M2VBxC9j9PDBhjaFiAMMOXV47cGOAdA9AdIBBoCaGwiIGI3ODM0MTI2NzA2YmE2ZDhkOTk4MzIzMWM0ZTA3OTk0; ssid_ucp_v1=1.0.0-KDA3MGYzODJmNTA1ODQ4ZTQyNTI5MGI0OWVhM2JiMTE3ZDU2ZDhiZDAKIQjwqYD1-M2VBxC9j9PDBhjaFiAMMOXV47cGOAdA9AdIBBoCaGwiIGI3ODM0MTI2NzA2YmE2ZDhkOTk4MzIzMWM0ZTA3OTk0; passport_csrf_token=33d28d05614a47f7e1dffc49c5758f8a; passport_csrf_token_default=33d28d05614a47f7e1dffc49c5758f8a; __security_mc_1_s_sdk_crypt_sdk=5d22face-440d-93b6; __security_mc_1_s_sdk_cert_key=5a93cfa5-4095-a188; s_v_web_id=verify_md483xcq_H1MrnPQR_6okw_4t48_9W9I_62U3qV7tFOdL; __ac_nonce=068859b35003c1f2ced76; __ac_signature=_02B4Z6wo00f01JRbvLQAAIDBJpYn.I-Et2CUe7gAAE2Yfb; IsDouyinActive=true; dy_swidth=1280; dy_sheight=720; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1280%2C%5C%22screen_height%5C%22%3A720%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAA0iehJnc3hz7WbHdpqUKVZymrG_Ip62p1Cw6y6HYOnZmDhQGQG4SFjDU24IB5iHsY%2F1753632000000%2F0%2F1753586490159%2F0%22; strategyABtestKey=%221753586490.316%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCTFdEbEU1cHRpajVocjNML2VqWWdXQlkrN3YzRHFOTFFUQjU5V05QeHlnY1BkdG1MWHRUV3IvSmFueVU4ZkRoQ2ZkOFJ0Ui9xbmp3ZUtnVTQ1OElkMWM9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; session_tlb_tag=sttt%7C2%7Ct4NBJnBrptjZmDIxxOB5lP_________hvU97KeL_PSjmGj1dyBgBQbEajybabD4-i287gAq0ghA%3D; __security_mc_1_s_sdk_sign_data_key_web_protect=c6bc9214-4416-b62a; home_can_add_dy_2_desktop=%221%22; publish_badge_show_info=%220%2C0%2C0%2C1753586492397%22; odin_tt=fcbbb9dec8281eca4798f5de59341745b0e37bbf95082053c7951627b88811a10d5ec225a2ab021fc3122a8ba24a13944e1b4ad8491870c1eec3468e899dce1b; passport_fe_beating_status=true; ttwid=1%7CZAU22RaDXm8wa7QUiuLdrjM0yqFb2ItbnWt9sXeneRc%7C1753586496%7Cdf9b09376d40feaa063933afbde91fb07add21dd47de871f8283da51abd92946; biz_trace_id=b1703d21; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f27636469766027292771273f27333036333c31333d3036303234272927676c715a75776a716a666a69273f2763646976602778; bit_env=r5i84bY8MIywbMXHDxYharBxY9qWey3HbeDwPm0qqM1ZoMope7UAfqJSegvB-bUpe1ZgBDcXn6oaAEcLAesVwp-Acc1LxnrdxT5iRhWbLtxHN2dcQ2FdjdXFI8c0b4ErYgoAAnnDUV55WyxKsiNqEDsTqs6OkMr95w_yxe70VyONs4yTEShdy-hf6LHmzkv9ie_ktX4l85kMToeS2413GJzQg95Qoq-VP7srGU2kHMIYNnaejG4SxemeoEODZZnEDSTFbBaDifwzTBPumNVR5z90QlO2U-SQFKwI54Px4GXProSxK7DYiUe-JFuR1UGj8mfkRsujVLJfyvWLpoEu2SqDDli3QU52rxjDyUeW7tnzHy83XGfXWpavdvqYDpDJEqmVgE6N9z40pmVQo9TiMefFGZX8gk_2sAALdMipSfQ4coq86LF86y_MR1OStVCPQPDuBuwfiyaFqrymTWOSMJJmyHfuE4Pl_6vHKyqXAUfO_Tx1uZFsmVbtO7lTFE0JQZkHVQQFeE4hq8rXuJvg5v0sCNlLBS5B-0CFpOyZlvE%3D; gulu_source_res=eyJwX2luIjoiNzU0M2ZjOGQ1M2I0ODllM2QzNDA1NDBmYmViY2VhOTQ5YjdkNmE0NmQyY2RiODQzN2RiNDY4OTdiNDkzN2RlZiJ9; passport_auth_mix_state=yoyfkbak8uf12so1i2nfs3363h814z3d83clo5ftz3jdqzz4"
    output_path = "extract_videos"
    downloader = DouyinDownloader(cookie= cookies,share_url= share_url)
    
    
    downloader.process(share_url= share_url,output_path= output_path)