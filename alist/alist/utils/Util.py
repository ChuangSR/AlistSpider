import os
import random
import re
import time
import urllib
from urllib import parse

import scrapy

from alist import settings


class Util:
    """
        用于保证文件的名称的可存储性，替换异常字符
    """

    @staticmethod
    def replace_name(name):
        char_list = ['*', '|', ':', '?', '/', '<', '>', '"', '\\',"'"]
        return Util.__replace(name, char_list)

    """
        替换存储路径中的异常字符
    """

    @staticmethod
    def replace_path(path):
        char_list = ['*', '|', ':', '?', '<', '>', '"',"'"]
        return Util.__replace(path, char_list)

    """
        执行替换
    """

    @staticmethod
    def __replace(input_str, char_list):
        for i in char_list:
            if i in input_str:
                input_str = input_str.replace(i, "_")
        return input_str

    @staticmethod
    def get_time():
        return time.strftime("%Y-%m-%d %H:%H:%S")

    @staticmethod
    def get_path(path, name):
        if path[-1] == "/":
            return path + name
        elif name[0] == "/":
            return path + name
        else:
            return path+"/"+name

    @staticmethod
    def get_download_path(path, sign):
        download_apis = settings.config.get("website").get("download_api")

        # if type(download_apis) == str:
        #     path = Util.get_path(download_apis, path)
        # elif type(download_apis) == list:
        #     path = Util.get_path(random.choice(download_apis), path)
        # elif type(download_apis) == dict:
        #     for key in download_apis.keys():
        #         if re.match(key, path) or key in path:
        #             path = Util.get_path(download_apis[key], path)
        #             break
        return f"{Util.get_path(download_apis,path)}?sign={sign}"

    @staticmethod
    def get_json_data(path):
        return {
            'path': path,
            'password': Util.get_password(path),
            'page': 1,
            'per_page': 0,
            'refresh': False,
        }

    @staticmethod
    def get_proxy():
        proxy = settings.config.get("spider").get("proxy")
        if proxy and "http" in proxy:
            return proxy

    @staticmethod
    def path_check(path):
        config_spider = settings.config.get("spider")
        allowed_path = config_spider.get("allowed_path") or []
        dont_allowed_path = config_spider.get("dont_allowed_path") or []
        for i in allowed_path:
            if re.match(i, path):
                return True
        for i in dont_allowed_path:
            if re.match(i, path):
                return False
        return config_spider.get("path_default")

    @staticmethod
    def download_check(path):
        config_spider = settings.config.get("spider")
        # 允许下载的类型
        allowed_download_type = config_spider.get("allowed_download_type") or ["*"]
        # 禁止下载的类型
        dont_allowed_download_type = config_spider.get("dont_allowed_download_type") or []
        type = path.split(".")[-1]
        return (type in allowed_download_type or "*" in allowed_download_type) and type not in dont_allowed_download_type


    @staticmethod
    def file_exists(path):
        config_spider = settings.config.get("spider")
        return os.path.exists(Util.get_path(config_spider.get("save_path"),path))
    @staticmethod
    def download_all():
        config_spider = settings.config.get("spider")
        # 允许下载的类型
        allowed_download_type = config_spider.get("allowed_download_type") or ["*"]
        dont_allowed_download_type = config_spider.get("allowed_download_type")
        return "*" in allowed_download_type and dont_allowed_download_type is None
    @staticmethod
    def redirect_check(path):
        redirect = settings.config.get("spider").get("redirect") or {}
        return Util.get_dict_value(redirect, path, 0)



    @staticmethod
    def get_download_meta():
        meta = {
            "request_type": "download",
        }

        if settings.config.get("spider").get("download_proxy_status"):
            proxy = Util.get_proxy()
            if proxy is not None:
                meta["proxy"] = proxy

        return meta

    #获取文件的数目
    @staticmethod
    def get_file_size(path):
        if not os.path.exists(path):
            os.makedirs(path)
        file_size = 0
        dirs = os.listdir(path)
        for dir in dirs:
            if os.path.isfile(Util.get_path(path,dir)):
                file_size += 1
            else:
                file_size += Util.get_file_size(Util.get_path(path,dir))
        return file_size

    # 对于获取请求对象的一种封装
    @staticmethod
    def get_json_request(spider, path, request_type,*args):
        proxy = Util.get_proxy()
        meta = {
            "path": path,
            "request_type": request_type,
            "args":args,
        }
        if proxy is not None:
            meta["proxy"] = proxy
        json_request = scrapy.http.JsonRequest(settings.config.get("website").get("list_api"),
                                               data=Util.get_json_data(path), callback=spider.parse,
                                               meta=meta,
                                               headers=Util.get_headers(path))
        return json_request

    @staticmethod
    def get_password(path):
        passwords = settings.config.get("website").get("password") or ""
        if type(passwords) == str:
            return passwords
        if type(passwords) == dict:
            return Util.get_dict_value(passwords, path, "")

    @staticmethod
    def get_dict_value(data_dict, value, default):
        reply = None
        num = -1
        for key in data_dict.keys():
            if key == "default":
                continue
            if re.match(key, value):
                length = len(key)
                if length > num:
                    num = length
                    reply = data_dict.get(key)
        return reply or (data_dict.get("default") or default)

    # 获取请求头
    @staticmethod
    def get_headers(path):
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'authorization': '',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': settings.config.get("website").get("url"),
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': settings.config.get("website").get("url") + urllib.parse.quote(path),
            'sec-ch-ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': random.choice(settings.USER_AGENT)
        }

    # 构建url的工具
    @staticmethod
    def url_builder(url, num):
        url_list = url.split("/")
        url = ""
        for i in range(0, num):
            url += url_list[i]
            if i != num - 1:
                url += "/"
        return url
