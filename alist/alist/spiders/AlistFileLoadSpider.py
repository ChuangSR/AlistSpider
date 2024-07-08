import json
from typing import Iterable, Union, Any

import scrapy
from scrapy import Request, Spider
from scrapy.http import Response
from twisted.internet.defer import Deferred

from alist import settings
from alist.dao.MysqlDao import MysqlDao
from alist.utils.Util import Util


class AlistFileLoadSpider(scrapy.Spider):
    name = 'AlistFileLoadSpider'
    allowed_domains = settings.config.get("spider").get("allowed_domains")
    # 缓存
    cache = {}
    config_spider = settings.config.get("spider")
    custom_settings = {
        "DOWNLOAD_DELAY": config_spider.get("download_delay_dir")
    }

    def start_requests(self) -> Iterable[Request]:
        # 绑定mysql持久操作
        settings.dao = MysqlDao()
        dirs = settings.dao.select_dir_table_all()
        for dir in dirs:
            dir = list(dir)
            # 使用通配符，并且存在子目录的情况下，变量所有的目录，获取总文件数目
            if dir[4] > 0 or not Util.download_all():
                dir[6] = 0
                dir[5] = 0
                self.cache[dir[1]] = dir
                yield Util.get_json_request(self, dir[1], "get_file_list")
            else:
                dir[6] = dir[5]
                self.cache[dir[1]] = dir

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data_json = json.loads(response.text)
        # 获取目录列表
        content = data_json["data"].get("content")
        if content is None:
            return
        content_length = len(content)
        if content[-1]["is_dir"]:
            content = reversed(content)
        # 目录数目
        dirs = 0
        # 文件数目
        files = 0
        # 是否为子文件夹
        args = response.meta.get("args")
        arg = response.meta["path"]
        for i in content:
            # 文件名称
            name = i["name"]
            path = response.meta["path"]
            path = Util.get_path(path, name)
            if args:
                arg = args[0]
            # 对于目录进行处理
            if bool(i["is_dir"]):
                dirs += 1
                yield Util.get_json_request(self, path, "get_file_list", arg)
            else:
                if Util.download_all():
                    files = content_length
                    break
                if Util.download_check(path):
                    print(path)
                    files += 1
        self.cache[arg][5] += content_length - dirs
        sum = files - dirs
        self.cache[arg][6] += sum if sum > 0 else 0

    @staticmethod
    def close(spider: Spider, reason: str) -> Union[Deferred, None]:
        values = spider.cache.values()
        dao = settings.dao
        for i in values:
            try:
                print(f"目录:{i[1]}")
                print(f"总文件数目：{i[5]}")
                print(f"需要下载的文件数目：{i[6]}")
                if i[6] <= 0:
                    dao.delete_dir_table(i)
                    print("删除!")
                else:
                    dao.update_dir_table(i)
                print("--------------------------")
            except Exception as e:
                print(e)
        dao.close()
        return super().close(spider, reason)
