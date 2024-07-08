# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AlistItem(scrapy.Item):
    #文件的名称
    file_name = scrapy.Field()

    #文件的网站路径
    url_path = scrapy.Field()

    #文件的存储路径
    file_path = scrapy.Field()

    #文件的类型
    file_type = scrapy.Field()

    #文件的url
    file_urls = scrapy.Field()

    #文件的大小
    file_size = scrapy.Field()

    files = scrapy.Field()

    #文件的备注
    remark = scrapy.Field()

    #链接重定向的次数
    redirect = scrapy.Field()
class AlistDirItem(scrapy.Item):
    #网站路径
    path = scrapy.Field()

    #生成的表格名称
    table_name = scrapy.Field()

    #所有的子目录数目
    subdirectory = scrapy.Field()

    #目录的数目
    dirs = scrapy.Field()

    #文件的数目
    files = scrapy.Field()

    #路径的文件大小，并不准确
    size = scrapy.Field()
