import sys
sys.path.append(r'D:\Users\60490\sshservers')

from spider.server_list.server_list_parser_base import Server_list_parser_base

import requests
from lxml import etree
from tqdm import tqdm

class Server_list_parser_sshocean(Server_list_parser_base):
    name = 'Server_list_parser_sshocean'

    def __init__(self, server_list_url: str = 'https://sshocean.com/ssh7days',
                 server_provider_url: str = None) -> None:
        super().__init__(server_list_url, server_provider_url)

    def parse(self) -> dict:
        res = requests.get(self.server_list_url)
        assert res.status_code==200, f'status_code: {res.status_code}, url: {res.url}'
        # print(res.text)
        html = etree.HTML(res.text)
        region_card_xpath_list = html.xpath('//div[@class="col-lg-3 col-md-6 mb-5"]')
        # region_str_list = [x.xpath('div/div/h4')[0].text for x in region_card_xpath_list] # ['AUSTRALIA', 'CANADA', ..
        # print(region_str_list)
        region_list_url_list = [x.xpath('div/div/a/@href')[0] for x in region_card_xpath_list] # ['https://sshocean.com/ssh7days/australia', ..
        # print(region_list_url_list)

        ret = dict()
        # for region, list_url in zip(region_str_list, region_list_url_list):
        for list_url in tqdm(region_list_url_list, desc='parsing regions: '):
            res = requests.get(list_url)
            assert res.status_code==200, f'status_code: {res.status_code}, url: {res.url}'
            html = etree.HTML(res.text)
            server_card_xpath_list = html.xpath('//div[@class="col-lg-4 col-md-6 mb-5"]')
            server_region_list = [x.xpath('div/div/table/tr[2]/td[2]/b/text()')[0] for x in server_card_xpath_list]
            # print(server_region_list) # ['United States', 
            server_host_list = [x.xpath('div/div/table/tr[1]/td[2]/b/text()')[0] for x in server_card_xpath_list]
            # print(server_host_list) # ['us01.sshocean.net', 
            # server_url_list = [x.xpath('div/div/a/@href')[0] for x in server_card_xpath_list]  # 要到的不准，真实页面在 australia/au02 写的却是 australia/au03
            server_url_list = [f"https://sshocean.com/ssh7days/{region.lower().replace(' ','-')}/{host.split('.')[0]}"
                                for region,host in zip(server_region_list,server_host_list)]
            # print(server_url_list) # ['https://sshocean.com/ssh7days/united-states/us01', 
            server_remain_list = [x.xpath('div/div/p/span/text()') for x in server_card_xpath_list]
            server_remain_list = [int(rl[0]) if len(rl) else 0 for rl in server_remain_list]
            # print(server_remain_list)

            for region, host, url, remain in zip(server_region_list, server_host_list, server_url_list, server_remain_list):
                if remain==0 or not self.check_server(host):
                    continue
                ret[url] = {'region': region, 'host': host, 'port': 22, 'Referer': res.url}
        return ret
                




SLP_SSHOCEAN = Server_list_parser_sshocean()
        
if __name__ == '__main__':
    pass
    servers = SLP_SSHOCEAN.parse()
    # print(servers)
    for s in servers:
        print(s,servers[s])
    print(len(servers))