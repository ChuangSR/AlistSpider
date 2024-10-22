import json
import urllib
from typing import Union
from urllib import parse
import scrapy
from scrapy import Spider
from scrapy.http import JsonRequest
from twisted.internet.defer import Deferred

from alist import settings
from alist.dao.MysqlDao import MysqlDao
from alist.items import AlistItem
from alist.utils.Util import Util


class AlistDownloadSpider(scrapy.Spider):
    name = "AlistDownloadSpider"
    allowed_domains = settings.config.get("spider").get("allowed_domains")

    config_spider = settings.config.get("spider")
    custom_settings = {
        "ITEM_PIPELINES": {
            "alist.pipelines.AlistPipeline": 300,
            "alist.pipelines.AlistFilePipeline": 301,
            "alist.pipelines.AlistEndPipeline": 302
        },
        "DOWNLOAD_DELAY": config_spider.get("download_delay_download"),
        "FILES_STORE": config_spider.get("save_path"),
    }

    def start_requests(self, path="/") -> JsonRequest:
        # 绑定mysql持久操作
        settings.dao = MysqlDao()
        download_config = settings.config.get("download")
        path = download_config.get("path")
        yield Util.get_json_request(self, path, "list_request")

    def parse(self, response, **kwargs):
        data_json = json.loads(response.text)
        content = data_json["data"].get("content")
        if content is None:
            return
        for i in content:
            name = i["name"]
            path = Util.get_path(response.meta["path"], name)
            if bool(i["is_dir"]):
                yield Util.get_json_request(self, path, "list_request")
            else:
                if not Util.download_check(path):
                    print(f"{path} 拒绝下载！")
                    continue
                if Util.file_exists(path):
                    print(f"{path} 文件已存在！")
                    continue
                sign = i['sign']
                item = AlistItem()
                item["file_name"] = Util.replace_name(name.split(".")[0])
                item["url_path"] = Util.get_path(settings.config.get("website").get("url"), urllib.parse.quote(path))
                item["file_path"] = Util.replace_path(path)
                item["file_type"] = name.split(".")[-1]
                item["file_urls"] = [Util.get_download_path(urllib.parse.quote(path), sign)]
                item["file_size"] = i["size"]
                item["redirect"] = Util.redirect_check(path)
                yield self._redirect(item, path)

    def redirect_parse(self, response):
        item = response.meta.get("item")
        location = str(response.headers.get("Location"), encoding="utf-8")
        item["file_urls"] = [location]
        item["redirect"] = item.get("redirect") - 1
        yield self._redirect(item, "")

    def _redirect(self, item, path):
        if item.get("redirect") <= 0:
            return item
        else:
            meta = {
                "item": item,
                "dont_redirect": True,
                'handle_httpstatus_list': [301, 302, 307]
            }
            proxy = Util.get_proxy()

            if proxy:
                meta["proxy"] = proxy
            return scrapy.Request(url=item.get("file_urls")[0], callback=self.redirect_parse, meta=meta,
                                  headers=Util.get_headers(path))

    @staticmethod
    def close(spider: Spider, reason: str) -> Union[Deferred, None]:
        dao = settings.dao
        download = settings.config.get("download")
        need_files = download.get("need_files")
        id = download.get("id")
        path = Util.get_path(settings.config.get("spider").get("save_path")
                             , Util.replace_path(download.get("path")))
        size = Util.get_file_size(path)
        if size == need_files:
            dao.update_table_status(id)
        dao.close()
        return super().close(spider, reason)
