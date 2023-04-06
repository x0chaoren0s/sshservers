from urllib.parse import urlparse
import logging, socket

class Server_list_parser_base:
    name = 'Server_list_parser_base'

    def __init__(self,
                 server_list_url: str = None,
                 server_provider_url: str = None) -> None:
        self.server_list_url = server_list_url[:-1] if server_list_url.endswith('/') \
                                else server_list_url
        if server_provider_url:
            self.server_provider_url = server_provider_url[:-1] if server_provider_url.endswith('/') \
                else server_provider_url
        else:
            urlp = urlparse(server_list_url)
            self.server_provider_url = f'{urlp.scheme}://{urlp.netloc}'

            
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        _ch = logging.StreamHandler()
        _ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    datefmt='%Y-%m-%d %H:%M:%S')
        _ch.setFormatter(formatter)
        logger.addHandler(_ch)
        self.logger = logger
        self.logger.info(f'[{self.server_provider_url}], {self.server_list_url}')

    def parse(self) -> dict:
        raise Exception('未实现parse方法')
    
    @staticmethod
    def check_server(host, port=22):
        # ref: https://cloud.tencent.com/developer/article/1570645
        try:
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host,port))
            return True
        except socket.error as e:
            return False
        finally:
            sock.close()




if __name__ == '__main__':
    # FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
    # logging.basicConfig(format=FORMAT)
    slp = Server_list_parser_base('https://sshocean.com/ssh7days/')
    slp.parse()