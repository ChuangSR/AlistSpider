import hashlib

import pymysql
from alist import settings
from alist.items import AlistItem, AlistDirItem


class MysqlDao:
    def __init__(self):
        config: dict = settings.config
        config_mysql: dict = config.get("mysql")
        connect = pymysql.connect(host=config_mysql.get("host")
                                  , user=config_mysql.get("user")
                                  , passwd=config_mysql.get("password")
                                  , port=config_mysql.get("port")
                                  , charset='utf8mb4')
        cursor = connect.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.get('mysql').get('database')}")
        connect.commit()
        cursor.close()
        connect.close()

        self.connect = pymysql.connect(host=config_mysql.get("host")
                                       , user=config_mysql.get("user")
                                       , passwd=config_mysql.get("password")
                                       , port=config_mysql.get("port")
                                       , db=config_mysql.get("database")
                                       , charset='utf8mb4')
        self.cursor = self.connect.cursor()
        path = config.get("spider").get("start_path")
        path_code = hashlib.md5(path.encode("utf-8")).hexdigest()
        self.dir_table = f"dir_table_{path_code}"
        self._create_dir_table(self.dir_table)

    def table_cheack(self, table_name):
        sql = f"""
            select 
                TABLE_NAME 
            from 
                INFORMATION_SCHEMA.TABLES 
            where 
                TABLE_SCHEMA="{settings.config.get('mysql').get('database')}" and TABLE_NAME="{table_name}"
        """
        self.cursor.execute(sql)
        return len(self.cursor.fetchall()) == 1

    def _create_file_table(self, table_name):
        if self.table_cheack(table_name):
            return
        self.cursor.execute(f"""
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
        """)
        self.connect.commit()

    # 创建目录表
    def _create_dir_table(self, table_name):
        if self.table_cheack(table_name):
            return
        self.cursor.execute(f"""
            CREATE TABLE `{table_name}`  (
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
        """)

        self.connect.commit()

    def select_dir_table(self, table_name):
        sql = f"""
            select 
                id,path,table_name,subdirectory,dirs,files,status,size,remark
            from 
                {self.dir_table}
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
                {self.dir_table}
            where
                status = 0
        """

        self.cursor.execute(sql)
        return self.cursor.fetchall()

    # 更新表格数据
    def update_dir_table(self, dir):
        sql = f"""
                update 
                    {self.dir_table}
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
                {self.dir_table}
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
                `{self.dir_table}`(path,table_name,subdirectory,dirs,files,size)
            values
                ("{path}","{table_name}",{subdirectory},{dirs},{files},{size})
        """
        self.cursor.execute(sql)
        self.connect.commit()

        if self.table_cheack(table_name):
            return

        self._create_file_table(table_name)

    def update_table_status(self, id):
        sql = f"""
            update 
                {self.dir_table}
            set
                status = 1
            where
                id = {id}
        """
        self.cursor.execute(sql)
        self.connect.commit()

    # 跟新表格数据
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
