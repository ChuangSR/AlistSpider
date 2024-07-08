import hashlib
import json
from typing import Union

import scrapy
from scrapy import Spider
from twisted.internet.defer import Deferred

from alist import settings
from alist.dao.MysqlDao import MysqlDao
from alist.items import AlistDirItem
from alist.utils.Util import Util


# 此爬虫用于获取网址的目录，并且根据深度创建对应的表格
class AlistDirSpider(scrapy.Spider):
    name = 'AlistDirSpider'
    config_spider = settings.config.get("spider")
    allowed_domains = settings.config.get("spider").get("allowed_domains")
    # 目录的遍历深度
    dir_depth = config_spider.get("dir_depth")
    # 缓存
    cache = {}
    custom_settings = {
        "ITEM_PIPELINES": {
            "alist.pipelines.AlistDirPipeline": 300
        },
        "DOWNLOAD_DELAY": config_spider.get("download_delay_dir")
    }

    def start_requests(self):
        # 绑定mysql持久操作
        settings.dao = MysqlDao()
        yield Util.get_json_request(self, self.config_spider.get("start_path"), "list_request")

    def parse(self, response, **kwargs):
        data_json = json.loads(response.text)
        # 获取目录列表
        content = data_json["data"].get("content")
        if content is None:
            return
        temp = ""
        dirs = 0
        subdirectory = len(content)
        if content[-1]["is_dir"]:
            content = reversed(content)
        # 遍历列表
        for i in content:
            name = i["name"]
            path = response.meta["path"]
            path = Util.get_path(path, name)
            # 对于目录进行处理
            if i["is_dir"]:
                dirs += 1
                # 深度处理
                if len(path.split("/")) <= self.get_depth(path):
                    print(path)
                    # 将目录大小加入缓存
                    self.cache[path] = i["size"]
                    yield Util.get_json_request(self, path, "list_request")
            else:
                temp = path
                # 判读该路径是否支持，如果不支持直接退出
                if not Util.path_check(temp):
                    temp = ""
                    del self.cache[response.meta["path"]]
                    break
                # 判断该路径下是否有需要下载的文件或者文件夹
                # 如果没有那么该路径不会被加入数据库中
                if Util.download_check(temp) or dirs != 0:
                    break
                temp = ""
        if temp != "":
            path = response.meta["path"]
            table_name = hashlib.md5(path.encode("utf-8")).hexdigest()
            size = self.cache[path]
            item = AlistDirItem()
            item["path"] = path
            item["table_name"] = table_name
            item["subdirectory"] = subdirectory
            item["dirs"] = dirs
            item["files"] = subdirectory - dirs
            item["size"] = size
            del self.cache[path]
            yield item

    def get_depth(self, path):
        if type(self.dir_depth) == int:
            return self.dir_depth + 1
        if type(self.dir_depth) == dict:
            return Util.get_dict_value(self.dir_depth, path, 0) + 1

    @staticmethod
    def close(spider: Spider, reason: str) -> Union[Deferred, None]:
        settings.dao.close()
        return super().close(spider, reason)
