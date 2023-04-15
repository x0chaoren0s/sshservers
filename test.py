# from spider.server_list.server_list_parser_vpnjantit import SLP_VPNJANTIT
from spider.server.server_parser_vpnjantit import Server_parser_vpnjantit

# SLP_SSHOCEAN.parse()
# print(SLP_VPNJANTIT.parse())
Server_parser_vpnjantit({'https://www.vpnjantit.com/create-free-account?server=usa5&type=SSH': 
                         {'region': 'Dallas, USA', 'host': 'usa5.vpnjantit.com', 'ip': '154.7.253.177', 'port': 22, 
                          'Referer': 'https://www.vpnjantit.com/free-ssh-7-days'}}).parse()