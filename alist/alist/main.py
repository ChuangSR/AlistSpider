import multiprocessing
import os
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import yaml

from alist import settings
from alist.dao.MysqlDao import MysqlDao
from alist.utils.Util import Util


def init():
    # 读取配置文件
    with open("config.yaml", mode="r", encoding="utf-8") as f:
        config: dict = yaml.load(f.read(), yaml.FullLoader)

    # 检查配置文件，是否缺少必要信息
    config_check(config)

    # 读取url，为创建数据库做准备
    url: str = config.get("website").get("url")
    if "http://" in url or "https://" in url:
        database: str = url.split("/")[2]
    else:
        database:str = url.split("/")[0]
    # 添加数据库名称到配置文件中
    config.get("mysql")["database"] = database.replace(".", "_")

    # 设置文件管道存储路径
    settings.FILES_STORE = config.get("spider").get("save_path")

    # 在setting中绑定配置文件
    settings.config = config


# 用于检查配置文件
def config_check(config: dict):
    config_website: dict = config.get("website")
    config_spider: dict = config.get("spider")
    config_mysql: dict = config.get("mysql")

    if not config_website.get("url"):
        sys.exit("爬虫退出:website.url 缺失")
    if "http://" in config_website.get("url") or "https://" in config_website.get("url"):
        config_website["url"] = Util.url_builder(config_website.get("url"), 3)
    else:
        config_website["url"] = Util.url_builder(config_website.get("url"),1)

    if not config_website.get("list_api"):
        sys.exit("爬虫退出:website.list_api 缺失")
    if not config_website.get("download_api"):
        sys.exit("爬虫退出:website.download_api 缺失")
    config_website["download_api"] = Util.url_builder(config_website.get("download_api"), 4)
    if not config_website.get("password"):
        config_website["password"] = ""
    if type(config_website.get("password")) not in [dict, str]:
        sys.exit("爬虫退出:website.password 数据类型异常")

    if not config_spider.get("save_path"):
        config_spider["save_path"] = "./download"
        print("爬虫:spider.save_path 缺失，将下载到当前目录的download文件中")
    if not os.path.exists(config_spider.get("save_path")):
        try:
            os.mkdir(config_spider.get("save_path"))
        except IOError:
            sys.exit("爬虫退出:website.save_path 无法创建")
    if not config_spider.get("allowed_domains"):
        sys.exit("爬虫退出:spider.allowed_domains 缺失")
    if not config_spider.get("download_proxy_status"):
        config_spider["download_proxy_status"] = False
        print("爬虫:spider.download_proxy_status 缺失，将默认不使用代理进行下载")
    if type(config_spider.get("download_proxy_status")) not in [dict, bool]:
        sys.exit("爬虫:spider.download_proxy_status 数据类型异常")
    if not config_spider.get("start_path"):
        config_spider["start_path"] = "/"
        print("爬虫:spider.start_path 缺失，将默认将从根目录开始运行")
    if config_spider.get("path_default") is None:
        config_spider["path_default"] = True
        print("爬虫:spider.path_default 缺失，将默认将进行下载")
    if type(config_spider.get("path_default")) != bool:
        sys.exit("爬虫:spider.path_default 数据类型异常")
    if not config_spider.get("thread_number"):
        config_spider["thread_number"] = 1
        print("爬虫:spider.thread_number 缺失默认值为1")
    if type(config_spider.get("thread_number")) != int:
        sys.exit("爬虫:spider.thread_number 数据类型异常")
    if not config_spider.get("dir_depth"):
        config_spider["dir_depth"] = 0
        print("爬虫:spider.dir_depth 缺失，将默认将直接进行下载")
    if type(config_spider.get("dir_depth")) not in [int, dict]:
        sys.exit("爬虫退出:spider.dir_depth 数据类型异常")

    if not config_mysql.get("host"):
        sys.exit("爬虫退出:mysql.host 缺失")
    if not config_mysql.get("user"):
        sys.exit("爬虫退出:mysql.user 缺失")
    if not config_mysql.get("password"):
        sys.exit("爬虫退出:mysql.password 缺失")
    if not config_mysql.get("port"):
        sys.exit("爬虫退出:mysql.port 缺失")


def base_thread(spider_name):
    init()
    setting = get_project_settings()
    crawler = CrawlerProcess(setting)
    crawler.crawl(spider_name)
    crawler.start()


def base_thread_run(spider_name):
    dir_spider = multiprocessing.Process(target=base_thread, args=(spider_name,))
    dir_spider.start()
    dir_spider.join()


def download_thread(spider_name, id, path, table_name, need_files):
    init()
    download_config = settings.config.get("download")
    download_config["id"] = id
    download_config["path"] = path
    download_config["table_name"] = table_name
    download_config["need_files"] = need_files
    setting = get_project_settings()
    crawler = CrawlerProcess(setting)
    crawler.crawl(spider_name)
    crawler.start()


def download_thread_run(spider_name, id, path, table_name, need_files):
    dir_spider = multiprocessing.Process(target=download_thread, args=(spider_name, id, path, table_name, need_files,))
    dir_spider.start()
    dir_spider.join()


def run():
    # 目录加载爬虫开启
    base_thread_run("AlistDirSpider")

    # 文件加载爬虫开启
    base_thread_run("AlistFileLoadSpider")

    # 文件下载处理
    dao = MysqlDao()
    dirs = dao.select_dir_table_all()
    for dir in dirs:
        path = Util.get_path(settings.config.get("spider").get("save_path"), Util.replace_path(dir[1]))
        size = Util.get_file_size(path)
        if dir[6] == size and dir[7] == 1:
            print(f"路径：{dir[1]}")
            print(f"文件下载数目：{dir[6]}")
            print(f"状态：完成")
            continue
        download_thread_run("AlistDownloadSpider", dir[0], dir[1], dir[2], dir[6])
    dao.close()


if __name__ == "__main__":
    author = 'ChangSR'
    version = '1.0'
    print(f'author:{author}')
    print(f'version:{version}')
    init()
    run()
