#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
易盾反垃圾云服务图片批量提交接口python示例代码
接口文档: http://dun.163.com/api.html
python版本：python3.7
运行:
    1. 修改 SECRET_ID,SECRET_KEY,BUSINESS_ID 为对应申请到的值
    2. $ python image_submit.py
"""
__author__ = 'yidun-dev'
__date__ = '2019/11/27'
__version__ = '0.2-dev'

import hashlib
import time
import random
import urllib3
from urllib.parse import urlencode
import json
from gmssl import sm3, func


class ImageSubmitAPIDemo(object):
    """图片批量提交接口"""

    API_URL = "http://as.dun.163.com/v5/image/submit"
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
        """生成签名信息
        Args:
            params (object) 请求参数
        Returns:
            参数签名md5值
        """
        buff = ""
        for k in sorted(params.keys()):
            buff += str(k) + str(params[k])
        buff += self.secret_key
        if "signatureMethod" in params.keys() and params["signatureMethod"] == "SM3":
            return sm3.sm3_hash(func.bytes_to_list(bytes(buff, encoding='utf8')))
        else:
            return hashlib.md5(buff.encode("utf8")).hexdigest()

    def check(self, params):
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
        # 100：色情，110：性感低俗，200：广告，210：二维码，260：广告法，300：暴恐，400：违禁，500：涉政，800：恶心类，900：其他，1100：涉价值观
        params["checkLabels"] = '100,110,300,400,800'
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


if __name__ == "__main__":
    """示例代码入口"""
    SECRET_ID = "43f09889d47e9ea9878cf43c8f39f7e4"  # 产品密钥ID，产品标识
    SECRET_KEY = "15811c80819180295d3840765d3ac34a"  # 产品私有密钥，服务端生成签名信息使用，请严格保管，避免泄露
    BUSINESS_ID = "a6ff11039b1dfbe87d3d9bdfb4e73972"  # 业务ID，易盾根据产品业务特点分配
    api = ImageSubmitAPIDemo(SECRET_ID, SECRET_KEY, BUSINESS_ID)

    # 私有请求参数
    images: list = []
    # dataId结构产品自行设计，用于唯一定位该图片数据
    image1 = {
        "name": "image1",
        "data": "https://nos.netease.com/yidun/2-0-0-a6133509763d4d6eac881a58f1791976.jpg",
        "level": "2"
        # "ip": "123.115.77.137"
        # "account": "python@163.com"
        # "deviceId": "deviceId"
        # "callbackUrl": "http://***"  # 主动回调地址url,如果设置了则走主动回调逻辑
    }
    image2 = {
        "name": "image2",
        "data": "http://dun.163.com/public/res/web/case/sexy_normal_2.jpg?dda0e793c500818028fc14f20f6b492a",
        "level": "0"
        # "ip": "123.115.77.137"
        # "account": "python@163.com"
        # "deviceId": "deviceId"
        # "callbackUrl": "http://***"  # 主动回调地址url,如果设置了则走主动回调逻辑
    }
    images.append(image1)
    images.append(image2)
    params = {
        "images": json.dumps(images)
    }

    ret = api.check(params)

    code: int = ret["code"]
    msg: str = ret["msg"]
    if code == 200:
        resultArray: list = ret["result"]
        for result in resultArray:
            name: str = result["name"]
            taskId: str = result["taskId"]
            dataId: str = result["dataId"]
            print("图片提交返回, name: %s, taskId: %s" % (name, taskId))

    else:
        print("ERROR: code=%s, msg=%s" % (ret["code"], ret["msg"]))