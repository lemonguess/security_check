#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本结果查询接口示例代码
"""

import hashlib
import json
import random
import time
import urllib3
from urllib.parse import urlencode
from gmssl import sm3, func


class TextQueryByTaskIdsDemo(object):
    """文本结果查询接口示例代码"""

    API_URL = "http://as.dun.163.com/v5/text/query/task"
    VERSION = "v5"

    def __init__(self, secret_id, secret_key, business_id):
        """
        Args:
            secret_id (str) 产品密钥ID，产品标识
            secret_key (str) 产品私有密钥，服务端生成签名信息使用
            business_id (str) 业务ID，易盾根据产品业务特点分配
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.business_id = business_id
        self.http = urllib3.PoolManager()  # 初始化连接池

    def gen_signature(self, params=None):
        """生成签名"""
        if params is None:
            params = {}
        
        sorted_params = sorted(params.keys())
        params_str = '&'.join(['%s=%s' % (key, params[key]) for key in sorted_params])
        
        sorted_params = sorted(params.keys()) + sorted(self.headers.keys())
        params_str = '&'.join(['%s=%s' % (key, params[key]) for key in sorted(params.keys())])
        params_str += '&' + '&'.join(['%s=%s' % (key, self.headers[key]) for key in sorted(self.headers.keys())])
        
        return hashlib.md5((params_str + self.secret_key).encode('utf8')).hexdigest()

    def query(self, params):
        """请求易盾接口
        Args:
            params (object) 请求参数
        Returns:
            请求结果，json格式
        """
        params["secretId"] = self.secret_id
        params["businessId"] = self.business_id
        params["version"] = self.VERSION
        params["timestamp"] = int(time.time() * 1000)
        params["nonce"] = int(random.random() * 100000000)
        # params["signatureMethod"] = "SM3"  # 签名方法，默认MD5，支持SM3
        params["signature"] = self.gen_signature(params)

        try:
            encoded_params = urlencode(params).encode("utf8")
            response = self.http.request(
                'POST',
                self.API_URL,
                body=encoded_params,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=urllib3.Timeout(connect=10, read=10)
            )
            content = response.data
            return json.loads(content)
        except Exception as ex:
            print("调用API接口失败:", str(ex))