import sys
from pathlib import Path
sys.path.append(Path(__file__).parent.parent.parent)


from .server_parser_base import Server_parser_base, Tuple
from ..server_list.server_list_parser_serverssh import SLP_SERVERSSH

from lxml import etree

class Server_parser_serverssh(Server_parser_base):
    name = 'serverssh'
    def __init__(self, server_dict: dict = None, server_list_parser = SLP_SERVERSSH, interval_sec: int = 0) -> None:
        super().__init__(server_dict, server_list_parser, interval_sec)
        
    def filling_form(self, res) -> Tuple[str, dict]:
        form_data = dict()
        html = etree.HTML(res.text)
        websiteKey = html.xpath('//div[@class="h-captcha"]/@data-sitekey')[0]
        captcha_res = self.solve_hcaptcha(res.url, websiteKey)
        form_data['id'] = res.url.split('https://serverssh.net/?q=create-ssh&filter=')[1]
        form_data['username'] = self.getRandStr(12)
        form_data['password'] = self.getRandStr(12)
        form_data['g-recaptcha-response'] = captcha_res
        form_data['h-captcha-response'] = captcha_res
        form_data['createAcc'] = ''
        return res.url, form_data
    
    def after_filling_form(self, res) -> dict:
        ret = dict()
        html = etree.HTML(res.text)
        try:
            success_info_xpath = html.xpath('//div[@class="alert alert-success alert-dismissable"]')[0]
            ret['user'] = success_info_xpath.xpath('li[2]/font/b/text()')[0].split(':')[1].strip()
            ret['pass'] = success_info_xpath.xpath('li[3]/font/b/text()')[0].split(':')[1].strip()
            ret['host'] = success_info_xpath.xpath('li[1]/font/b/text()')[0].split(':')[1].strip()
            ret['port'] = '22'
            ret['date_create'] = self.normalized_local_date()
            ret['date_expire'] = self.normalize_date(success_info_xpath.xpath('li[4]/font/b/text()')[0].split(':')[1].strip(), '%d-%m-%Y')
        except:
            ret['error_info'] = 'something wrong.'
            with open(f'{self.name}.html', 'w') as fout:
                print(res.text, file=fout)
        return ret
    
SP_SERVERSSH = Server_parser_serverssh()

if __name__ == '__main__':
    server_dict = SP_SERVERSSH.parse()
    sp = Server_parser_serverssh(server_dict)
    sp.parse()
