import sys
import os
import random

sys.path.append(os.getcwd())
from misc.agents import AGENTS


class WeiboUserAgentMiddleware(object):
    def process_request(self, request, spider):
        DEFAULT_REQUEST_HEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'Cookie': 'WBtopGlobal_register_version=2023111214;SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5_O.oej.39ZcWLp6oDWTkx5JpX5KzhUgL.FoM7eo.4ehzNeoe2dJLoI7_N9PSj9PLkUfvrUBtt;SCF=AmcpWYdzMxEhUWLHtPDTlbQwfWmdXoXXSAVDE3zNSqAnongJh_1R04emj0dDgaebWYf4Bv11mto8nfW35Xvr3kc.;_s_tentry=www.amz123.com;UOR=,,www.amz123.com;SUB=_2A25IVApEDeRhGeFO6VsY8CzLyT-IHXVrKAOMrDV8PUNbmtANLWz-kW9NQWztmZkmYhNmjW5A0cgGP8Z8CjOvoPkG;Apache=2559002441077.0586.1699597577296;ALF=1731308948;PC_TOKEN=bc73529cb3;SINAGLOBAL=8684552721605.112.1696770171512;SSOLoginState=1699597596;ULV=1699597577339:7:3:2:2559002441077.0586.1699597577296:1699518952747'
        }
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
        request.headers['Accept'] = DEFAULT_REQUEST_HEADERS['Accept']
        request.headers['Accept-Language'] = DEFAULT_REQUEST_HEADERS['Accept-Language']
        request.headers['Cookie'] = DEFAULT_REQUEST_HEADERS['Cookie']
