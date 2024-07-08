# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.http.request import NO_CALLBACK
from scrapy.pipelines.files import FilesPipeline

from alist import settings
from alist.dao.MysqlDao import MysqlDao
from alist.utils.Util import Util

class AlistDirPipeline:
    def process_item(self, item, spider):
        settings.dao.insert_dir_table(item)
        return item
class AlistPipeline:
    def process_item(self, item, spider):
        dao: MysqlDao = settings.dao
        dao.insert_file_data(item, settings.config.get("download").get("table_name"))
        return item


class AlistFilePipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        urls = ItemAdapter(item).get(self.files_urls_field, [])
        meta = Util.get_download_meta()
        return [Request(u, callback=NO_CALLBACK, meta=meta,headers=Util.get_headers("")) for u in urls]

    def file_path(self, request, response=None, info=None, *, item=None):
        return item["file_path"]

class AlistEndPipeline:
    def process_item(self, item, spider):
        if len(item["files"]) > 0 and item["files"][0]["status"] == "downloaded":
            dao: MysqlDao = settings.dao
            dao.update_file_status(item["file_name"], settings.config.get("download").get("table_name"))
        return item