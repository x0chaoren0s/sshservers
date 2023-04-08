import sys
from pathlib import Path
sys.path.append(Path(__file__).parent.parent.parent)


from .server_parser_base import Server_parser_base, Tuple
from ..server_list.server_list_parser_sshocean import SLP_SSHOCEAN

from lxml import etree

class Server_parser_sshocean(Server_parser_base):
    name = 'sshocean'
    def __init__(self, server_dict: dict = SLP_SSHOCEAN.parse(), interval_sec: int = 0) -> None:
        super().__init__(server_dict, interval_sec)

    def filling_form(self, res) -> Tuple[str, dict]:
        form_data = dict()
        html = etree.HTML(res.text)
        websiteKey = html.xpath('//div[@class="g-recaptcha"]/@data-sitekey')[0]
        recaptcha_res = self.solve_recaptcha_v2(res.url, websiteKey)
        form_data['username'] = self.getRandStr(12)
        form_data['password'] = self.getRandStr(12)
        form_data['g-recaptcha-response'] = recaptcha_res
        form_data['submit'] = ''
        return res.url, form_data
    
    def after_filling_form(self, res) -> dict:
        ret = dict()
        html = etree.HTML(res.text)
        if len(html.xpath('//div[@class="alert alert-success text-center p-2"]'))>0:
            success_info_xpath = html.xpath('//div[@class="alert alert-success text-center p-2"]')[0]
            ret['user'] = success_info_xpath.xpath('ul/li[2]/b/text()')[0]
            ret['pass'] = success_info_xpath.xpath('ul/li[3]/b/text()')[0]
            ret['host'] = success_info_xpath.xpath('ul/li[1]/b/text()')[0]
            ret['port'] = '22'
            ret['config'] = f"forward=ssh://{ret['user']}:{ret['pass']}@{ret['host']}:{ret['port']}"
            ret['date_create'] = self.normalize_date(success_info_xpath.xpath('ul/li[4]/b/text()')[0], '%d %b %Y')
            ret['date_expire'] = self.normalize_date(success_info_xpath.xpath('ul/li[5]/b/text()')[0], '%d %b %Y')
            ret['date_span'] = f"{ret['date_create']} - {ret['date_expire']}"
        elif len(html.xpath('//div[@class="alert alert-warning"]/text()[2]'))>0:
            ret['error_info'] = html.xpath('//div[@class="alert alert-warning"]/text()[2]')[0].strip()
        else:
            ret['error_info'] = 'something wrong.'
        return ret
    
SP_SSHOCEAN = Server_parser_sshocean()

if __name__ == '__main__':
    server_dict = SLP_SSHOCEAN.parse()
    sp = Server_parser_sshocean(server_dict)
    sp.parse()
