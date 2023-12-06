# -*- coding: utf-8 -*-
# @Time    : 2019/7/11
# @Author  : zl

from mitmproxy import http
from mitmproxy import ctx
from urllib import parse
import json


def response(flow: http.HTTPFlow):
    try:
        info = ctx.log.info
        req = flow.request
        resp = flow.response
        url = req.url
        purl = parse.urlparse(url)
        param_dict = parse.parse_qs(purl.query)
        host = purl.hostname
        path = purl.path

        if host == 'mp.weixin.qq.com' and path == '/mp/profile_ext':
            action = param_dict['action'][0]
            if action in ['home', 'getmsg']:
                msg = {}
                msg['url'] = url
                msg['action'] = action
                msg['req_header'] = dict(req.headers)
                msg['resp_header'] = dict(resp.headers)
                if action == 'getmsg':
                    msg['resp_body'] = json.loads(resp.content)
                info('msg : %s----' % msg)

    except Exception as e:
        ctx.log.error('wechatproxy error, %s' % e)
