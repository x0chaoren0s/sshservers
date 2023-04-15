import sys
from pathlib import Path
sys.path.append(Path(__file__).parent.parent.parent)

from .server_list_parser_base import Server_list_parser_base

from lxml import etree
from tqdm import tqdm
from typing import Tuple

class Server_list_parser_serverssh(Server_list_parser_base):
    name = 'Server_list_parser_serverssh'

    def __init__(self, server_list_url: str = 'https://serverssh.net/?q=ssh-servers&filter=extra&page=1',
                 server_provider_url: str = None) -> None:
        super().__init__(server_list_url, server_provider_url)
        self.list_page_url_base = 'https://serverssh.net/?q=ssh-servers&filter=extra&page=' # 长度为55

    def parse(self) -> dict:
        super().parse()

        ret = dict()
        for list_page_ind in tqdm(range(1,100), bar_format='{desc} {n_fmt}', desc=f'{self.name} parsing list pages: '): # 其实就几页而已
            now_list_page_ret, has_next_list_page = self.parse_list_page(list_page_ind)
            ret.update(now_list_page_ret)
            if not has_next_list_page:
                break
        # print(ret)
        return ret
                
    def parse_list_page(self, list_page_ind: int) -> Tuple[dict, bool]:
        ''' 返回: (当前页能爬取的服务器信息字典, 是否还有下一页)'''
        list_page_url = self.list_page_url_base+str(list_page_ind)
        try:
            res = self.session.get(list_page_url, timeout=60)
        except:
            return dict(), False
        html = etree.HTML(res.text)
        server_card_xpath_list = html.xpath('//div[@class="col-lg-4 col-md"]')
        server_region_list = [x.xpath('div/div/ul/li[2]/text()')[0].split(':')[1].strip() for x in server_card_xpath_list]
        # print(server_region_list) # ['Singapore', 'Singapore']
        server_available_list = [x.xpath('div/div/ul/li[5]/text()')[0]=='Remaining: ' for x in server_card_xpath_list]
        # print(server_available_list)  # [False, False]
        server_url_list = [self.server_provider_url+x.xpath('div/div/ul/li[6]/a/@href')[0] for x in server_card_xpath_list]
        # print(server_url_list) # ['https://serverssh.net/?q=create-ssh&filter=5', 'https://serverssh.net/?q=create-ssh&filter=6']
        ret = dict()
        for region,available,url in zip(server_region_list,server_available_list,server_url_list):
            if not available:
                continue
            ret[url] = {
                'region': region,
                'Referer': res.url
            }
        return ret, len(server_card_xpath_list)==2  # 这个网站一页只展示最多两个服务器

SLP_SERVERSSH = Server_list_parser_serverssh()
        
if __name__ == '__main__':
    pass
    servers = SLP_SERVERSSH.parse()
    # print(servers)
    for s in servers:
        print(s,servers[s])
    print(len(servers))