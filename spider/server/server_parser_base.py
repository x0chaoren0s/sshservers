import time, requests, logging, random, string, json
from requests.adapters import HTTPAdapter
from typing import Tuple, Iterable
from tqdm import tqdm
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(Path(__file__).parent.parent.parent)

from ..server_list.server_list_parser_base import Server_list_parser_base



class Server_parser_base:
    name = 'Server_parser_base'
    save_folder = Path(__file__).absolute().parent.parent.parent/'results'

    def __init__(self,
                 server_dict: dict = None,
                 server_list_parser: Server_list_parser_base = None,
                 interval_sec: int = 0
                 ) -> None:
        '''
        server_dict 若为 None, 则使用 server_list_parser.parse()
        
        server_dict 格式: {url:{'host':.., 'port':.., 'region':..}}
        '''
        self.server_dict = server_dict
        self.server_list_parser = server_list_parser
        self.interval_sec = interval_sec

        self.session = None
        
            
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        _ch = logging.StreamHandler()
        _ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    datefmt='%Y-%m-%d %H:%M:%S')
        _ch.setFormatter(formatter)
        logger.addHandler(_ch)
        self.logger = logger

    def parse(self, save=True, init_index=0) -> dict:
        if self.server_dict is None:
            self.server_dict = self.server_list_parser.parse()
        self.logger.info(f'num of servers: {len(self.server_dict)}')

        ret = self.server_dict.copy()
        for i, url in tqdm(enumerate(self.server_dict.keys()), desc=f'{self.name} parsing servers: '):
            self.session = self.new_session()
            if i<init_index:
                continue
            self.logger.info(url)
            if i>0:
                time.sleep(self.interval_sec)
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
                'Referer': self.server_dict[url]['Referer']
            }
            try:
                res = self.session.get(url, headers=headers, allow_redirects=False, timeout=60)
            except:
                ret[url]['error_info'] = 'get timeout'
                self.logger.info(f"{ret[url]['region']}, {url} , {ret[url]['error_info']}")
                continue
            post_url, form_data = self.filling_form(res)
            headers['Referer'] = res.url
            try:
                res = self.session.post(post_url, data=form_data, headers=headers, allow_redirects=False, timeout=60)
            except:
                ret[url]['error_info'] = 'post timeout'
                self.logger.info(f"{ret[url]['region']}, {url} , {ret[url]['error_info']}")
                continue
            info_dict = self.after_filling_form(res) # keys: user, pass, host, [ip], port, config
            ret[url].update(info_dict)
            if 'error_info' in ret[url]:
                self.logger.info(f"{ret[url]['region']}, {url} , {ret[url]['error_info']}")
            else:
                ret[url]['config'] = f"forward=ssh://{ret[url]['user']}:{ret[url]['pass']}@{ret[url].get('ip', ret[url]['host'])}:{ret[url]['port']}"
                ret[url]['date_span'] = f"{ret[url]['date_create']} - {ret[url]['date_expire']}"
                self.logger.info(f"{ret[url]['region']}, {ret[url]['config']}")
        if save:
            json_file = self.save_folder/f'{self.name}.json'
            with open(json_file, 'w') as fout:
                json.dump(ret, fout, indent=4)
            config_file = self.save_folder/f'{self.name}.conf'
            with open(config_file, 'w') as fout:
                for i,server_info in enumerate(ret.values()):
                    if i==0:
                        print(f"# {server_info['date_span']}", file=fout)
                    if 'config' in server_info:
                        print(server_info['config'], file=fout)
        num_tried = len(ret)
        num_succeed = len([v for v in list(ret.values()) if 'error_info' not in v])
        self.logger.info(f'finished. succeed: {num_succeed} / {num_tried}')
        return ret

    def filling_form(self, res) -> Tuple[str, dict]:
        raise Exception('未实现 filling_form 方法')
    
    def after_filling_form(self, res) -> dict:
        ''' keys: user, pass, host, [ip], port, config '''
        raise Exception('未实现 after_filling_form 方法')
    
    def solve_recaptcha_v2(self, websiteURL: str, websiteKey: str) -> str:
        sleep_sec = 4 # 循环请求识别结果，sleep_sec 秒请求一次
        max_sec = 180  # 最多等待 max_sec 秒
        clientKey = "ddd1cf72d9955a0e8ca7d05597fea5eb1dce33de5331" # clientKey：在个人中心获取

        # 第一步，创建验证码任务 
        self.logger.info(f'getting yescaptcha taskID for recaptcha_v2...')
        url = "https://china.yescaptcha.com/createTask"
        data = {
            "clientKey": clientKey,
            "task": {
                "websiteURL": websiteURL,
                "websiteKey": websiteKey,
                "type": "NoCaptchaTaskProxyless"
            }
        }
        try:
            # 发送JSON格式的数据
            taskID = self.session.post(url, json=data, timeout=60).json().get('taskId')
            self.logger.info(f'yescaptcha taskID for recaptcha_v2: {taskID}')
            
        except Exception as e:
            self.logger.error(e)

        # 第二步：使用taskId获取response 
        self.logger.info(f'getting yescaptcha result for recaptcha_v2...')
        sec = 0
        while sec < max_sec:
            try:
                url = f"https://china.yescaptcha.com/getTaskResult"
                data = {
                    "clientKey": clientKey,
                    "taskId": taskID
                }
            
                result = self.session.post(url, json=data, timeout=60).json()
                solution = result.get('solution', {})
                if solution:
                    gRecaptchaResponse = solution.get('gRecaptchaResponse')
                    if gRecaptchaResponse:
                        return gRecaptchaResponse
            except Exception as e:
                self.logger.error(e)

            sec += sleep_sec
            self.logger.info(f'spent {sec}s in getting...')
            time.sleep(sleep_sec)
    
    def solve_hcaptcha(self, websiteURL: str, websiteKey: str) -> str:
        sleep_sec = 4 # 循环请求识别结果，sleep_sec 秒请求一次
        max_sec = 180  # 最多等待 max_sec 秒
        clientKey = "ddd1cf72d9955a0e8ca7d05597fea5eb1dce33de5331" # clientKey：在个人中心获取

        # 第一步，创建验证码任务 
        self.logger.info(f'getting yescaptcha taskID for hcaptcha...')
        url = "https://china.yescaptcha.com/createTask"
        data = {
            "clientKey": clientKey,
            "task": {
                "websiteURL": websiteURL,
                "websiteKey": websiteKey,
                "type": "HCaptchaTaskProxyless"
            }
        }
        try:
            # 发送JSON格式的数据
            taskID = self.session.post(url, json=data, timeout=60).json().get('taskId')
            self.logger.info(f'yescaptcha taskID for hcaptcha: {taskID}')
            
        except Exception as e:
            self.logger.error(e)

        # 第二步：使用taskId获取response 
        self.logger.info(f'getting yescaptcha result for hcaptcha...')
        sec = 0
        while sec < max_sec:
            try:
                url = f"https://china.yescaptcha.com/getTaskResult"
                data = {
                    "clientKey": clientKey,
                    "taskId": taskID
                }
            
                result = self.session.post(url, json=data, timeout=60).json()
                solution = result.get('solution', {})
                if solution:
                    gRecaptchaResponse = solution.get('gRecaptchaResponse')
                    if gRecaptchaResponse:
                        return gRecaptchaResponse
            except Exception as e:
                self.logger.error(e)

            sec += sleep_sec
            self.logger.info(f'spent {sec}s in getting...')
            time.sleep(sleep_sec)

    def new_session(self) -> requests.Session:
        ''' 每创建一个账号都使用新 session 可直接绕过网站设置的创建账户时间间隔限制 '''
        if 'session' in dir(self) and self.session is not None:
            self.session.close()
            del self.session
        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=10))
        session.mount('https://', HTTPAdapter(max_retries=10))
        return session

    @staticmethod
    def getRandStr(strLen = -1):
        ''' strLen：随机字符串的长度，默认为 -1，代表闭区间 [4,12] 内的随机长度 '''
        if strLen == -1:
            strLen = random.randint(4,12)
        l = []
        #sample = '0123456789abcdefghijklmnopqrstuvwxyz!@#$%^&*()-+=.'
        sample = random.sample(string.ascii_letters + string.digits, 62)## 从a-zA-Z0-9生成指定数量的随机字符： list类型
        # sample = sample + list('!@#$%^&*()-+=.')#原基础上加入一些符号元素
        for i in range(strLen):
            char = random.choice(sample)#从sample中选择一个字符
            l.append(char)
        return ''.join(l)#返回字符串
    
    @staticmethod
    def normalize_date(datestr: str, date_pattern: 'str | Iterable[str]', normalizing_pattern: str="%Y-%m-%d") -> str:
        """
        #### 可将网站给的时间日期格式转换成本项目采用的标准日期格式 "%Y-%m-%d"
        如把 ' 17-07-2022' 标准化成 '2022-07-17'

        %a Locale’s abbreviated weekday name.

        %A Locale’s full weekday name.

        %b Locale’s abbreviated month name.

        %B Locale’s full month name.

        %c Locale’s appropriate date and time representation.

        %d Day of the month as a decimal number [01,31].

        %H Hour (24-hour clock) as a decimal number [00,23].

        %I Hour (12-hour clock) as a decimal number [01,12].

        %j Day of the year as a decimal number [001,366].

        %m Month as a decimal number [01,12].

        %M Minute as a decimal number [00,59].

        %p Locale’s equivalent of either AM or PM.

        %S Second as a decimal number [00,61].

        %U Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0.

        %w Weekday as a decimal number [0(Sunday),6].

        %W Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0.

        %x Locale’s appropriate date representation.

        %X Locale’s appropriate time representation.

        %y Year without century as a decimal number [00,99].

        %Y Year with century as a decimal number.

        %z Time zone offset indicating a positive or negative time difference from UTC/GMT of the form +HHMM or -HHMM, where H represents decimal hour digits and M represents decimal minute digits [-23:59, +23:59]. 1

        %Z Time zone name (no characters if no time zone exists). Deprecated. 1

        %% A literal '%' character.
        """
        for pattern in [date_pattern] if isinstance(date_pattern, str) else date_pattern:
            try:
                return time.strftime(normalizing_pattern, time.strptime(datestr,pattern))
            except:
                pass
        raise ValueError(f"time data '{datestr}' does not match any format in {[date_pattern] if isinstance(date_pattern, str) else date_pattern}")

    @staticmethod
    def normalized_local_date() -> str:
        '''
        #### 输出标准化的当前日期，如 '2022-07-28'
        可用于不显示账户的注册时间的网站，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
        '''
        return time.strftime("%Y-%m-%d",time.localtime())

if __name__ == '__main__':
    spb = Server_parser_base()
    print(spb.normalize_date('6 Apr 2023', '%d %b %Y'))