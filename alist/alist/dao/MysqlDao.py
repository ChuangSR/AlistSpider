import hashlib

import pymysql
from alist import settings
from alist.items import AlistItem, AlistDirItem


class MysqlDao:
    def __init__(self):
        #加载配置文件
        config: dict = settings.config
        config_mysql: dict = config.get("mysql")
        #创建数据库链接
        self.connect = pymysql.connect(host=config_mysql.get("host")
                                  , user=config_mysql.get("user")
                                  , passwd=config_mysql.get("password")
                                  , port=config_mysql.get("port")
                                  , charset='utf8mb4')
        self.cursor = self.connect.cursor()
        self.root_database = "AlistSpider"
        #爬虫总数据库的处理
        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.root_database}")
        self.cursor.execute(f"use {self.root_database}")
        #数据库表的处理
        self.root_table = "t_root"
        self._create_root_table()

        #当前网站的数据库处理

        # 需要爬取的路径
        path = config.get("spider").get("start_path")

        date = self.select_root_table(path)
        if date and len(date[0]) == 2 and date[0][0] and date[0][1]:
            self.spider_database = date[0][0]
            self.spider_dir = date[0][1]
            self.cursor.execute(f"use {self.spider_database}")
        else:
            # 数据名称
            self.spider_database = config.get('mysql').get('database')
            # 生成对应的数据表名称
            path_code = hashlib.md5(path.encode("utf-8")).hexdigest()
            self.spider_dir = f"dir_table_{path_code}"
            # 将表格中插入数据
            self.insert_root_table(self.spider_database, path, self.spider_dir)
            # 创建网站数据库
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.spider_database}")
            self.cursor.execute(f"use {self.spider_database}")
            # 创建目录表格
            self._create_dir_table()
    #用于检查表格是否存在
    def table_cheack(self,database,table_name):
        sql = f"""
            select 
                TABLE_NAME 
            from 
                INFORMATION_SCHEMA.TABLES 
            where 
                TABLE_SCHEMA="{database}" and TABLE_NAME="{table_name}"
        """
        self.cursor.execute(sql)
        return len(self.cursor.fetchall()) == 1

    #创建程序的总表格
    def _create_root_table(self):
        if self.table_cheack(self.root_database, self.root_table):
            return
        """
            这个表格用于保存爬虫运行过的所有信息
            id为一个索引
            database表示数据库的名字，每一个database代表着一个网站
            path当前脚本运行的路径（即需要爬取的网站路径）
            table_name于路径对应的名称
            status爬取路径的下载状态，为1表示完成
        """
        sql = f"""
            CREATE TABLE `{self.root_table}`  (
                `id` int NOT NULL AUTO_INCREMENT,
                `database_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `table_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `status` tinyint NULL DEFAULT 0,
                PRIMARY KEY (`id`) USING BTREE
            ) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;
        """
        self.cursor.execute(sql)
        self.connect.commit()
    def insert_root_table(self,database_name,path,table_name):
        sql = f"""
            insert into
                {self.root_table}
            (database_name,path,table_name)
            values (
                "{database_name}",
                "{path}",
                "{table_name}"
            )
        """
        self.cursor.execute(sql)
        self.connect.commit()

    def select_root_table(self,path):
        sql = f"""
            select
                database_name,table_name
            from
                {self.root_table}
            where
                path = "{path}"
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def _create_file_table(self, table_name):
        if self.table_cheack(self.spider_database,table_name):
            return
        sql = f"""
            CREATE TABLE `{table_name}`  (
                `id` int NOT NULL AUTO_INCREMENT,
                `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `url_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `download_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
                `file_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `file_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `file_size` int NULL DEFAULT NULL,
                `status` tinyint(1) NULL DEFAULT 0,
                `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                PRIMARY KEY (`id`) USING BTREE
            ) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;
        """
        self.cursor.execute(sql)
        self.connect.commit()

    # 创建目录表
    def _create_dir_table(self):
        if self.table_cheack(self.spider_database,self.spider_dir):
            return
        sql = f"""
            CREATE TABLE `{self.spider_dir}`  (
                `id` int NOT NULL AUTO_INCREMENT,
                `path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `table_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                `subdirectory` int NULL DEFAULT NULL,
                `dirs` int NULL DEFAULT NULL,
                `files` int NULL DEFAULT NULL,
                `need_files` int NULL DEFAULT 0,
                `status` tinyint(1) NULL DEFAULT 0,
                `size` bigint NULL DEFAULT NULL,
                `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
                PRIMARY KEY (`id`) USING BTREE
            ) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;
        """
        self.cursor.execute(sql)
        self.connect.commit()

    def select_dir_table(self,table_name):
        sql = f"""
            select 
                id,path,table_name,subdirectory,dirs,files,status,size,remark
            from 
                {self.spider_dir}
            where 
                table_name = "{table_name}"
        """
        self.cursor.execute(sql)

        return self.cursor.fetchall()

    # 获取所有的需要加载数据的表格
    def select_dir_table_all(self):
        sql = f"""
            select 
                id,path,table_name,subdirectory,dirs,files,need_files,status,size,remark
            from
                {self.spider_dir}
            where
                status = 0
        """

        self.cursor.execute(sql)
        return self.cursor.fetchall()

    # 更新表格数据
    def update_dir_table(self, dir):
        sql = f"""
                update 
                    {self.spider_dir}
                set
                    files = {dir[5]},
                    need_files = {dir[6]}
                where 
                    id = "{dir[0]}"
                """
        self.cursor.execute(sql)
        self.connect.commit()

    # 删除无用的数据和表格
    def delete_dir_table(self, dir):
        sql = f"""
            delete from
                {self.spider_dir}
            where
                id = {dir[0]}
        """
        self.cursor.execute(sql)
        sql = f"""
            drop table if exists `{dir[2]}`
        """
        self.cursor.execute(sql)
        self.connect.commit()

    # 插入表格数据
    def insert_dir_table(self, item: AlistDirItem):
        path = item["path"]
        table_name = item["table_name"]
        subdirectory = item["subdirectory"]
        dirs = item["dirs"]
        files = item["files"]
        size = item["size"]

        if self.select_dir_table(table_name):
            return

        sql = f"""
            insert into
                `{self.spider_dir}`(path,table_name,subdirectory,dirs,files,size)
            values
                ("{path}","{table_name}",{subdirectory},{dirs},{files},{size})
        """
        self.cursor.execute(sql)
        self.connect.commit()

        if self.table_cheack(self.spider_database,table_name):
            return

        self._create_file_table(table_name)

    #更新表格状态，表示所有的表格是否下载完成
    def update_table_status(self, id):
        sql = f"""
            update 
                {self.spider_dir}
            set
                status = 1
            where
                id = {id}
        """
        self.cursor.execute(sql)
        self.connect.commit()

    # 更新表格数据
    def insert_file_data(self, item: AlistItem, table_name):
        self._create_file_table(table_name)
        file_name = item["file_name"]
        result = self.select_file(file_name, table_name)
        if len(result) != 0:
            return
        sql = f"""
            insert into 
                `{table_name}`(file_name,url_path,download_path,file_type,file_path,file_size) 
            values 
                ('{item["file_name"]}','{item["url_path"]}',
                '{item["file_urls"][0]}','{item["file_type"]}',
                '{item["file_path"]}',{item["file_size"]})
        """

        self.cursor.execute(sql)
        self.connect.commit()

    #查询文件的信息
    def select_file(self, file_name, table_name):
        sql = f"""
            select 
                id,file_name,url_path,download_path,file_type,file_path,file_size,status,remark 
            from 
                `{table_name}`
            where 
                file_name = "{file_name}"
        """
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

    #更新文件的状态表示文件是否下载完成
    def update_file_status(self, file_name, table_name):
        if len(self.select_file(file_name, table_name)) == 0:
            return

        sql = f"""
            update 
                `{table_name}`
            set 
                status = 1
            where 
                file_name = "{file_name}"
        """

        self.cursor.execute(sql)
        self.connect.commit()

    def close(self):
        self.cursor.close()
        self.connect.close()
