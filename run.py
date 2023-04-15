from multiprocessing import Process

from spider.server.server_parser_sshocean import SP_SSHOCEAN
from spider.server.server_parser_vpnjantit import SP_VPNJANTIT
from spider.server.server_parser_serverssh import SP_SERVERSSH

if __name__ == '__main__':
    spiders = [SP_SSHOCEAN, SP_VPNJANTIT,SP_SERVERSSH]
    # spiders = [SP_SSHOCEAN,]
    # spiders = [SP_VPNJANTIT,]
    spiders = [SP_SERVERSSH,]
    spider_processes = [Process(target=s.parse) for s in spiders]
    [process.start() for process in spider_processes]
    [process.join() for process in spider_processes]