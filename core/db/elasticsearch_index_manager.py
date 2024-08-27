"""
AmyAlmond Project - core/db/elasticsearch_index_manager.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.0 (Pre_827001)

elasticsearch_index_manager.py - 负责Elasticsearch索引的创建、更新和管理
"""

from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import bulk
from config import ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD
from core.utils.logger import get_logger

_log = get_logger()


class ElasticsearchIndexManager:
    """
    负责管理Elasticsearch索引的类
    """

    def __init__(self):
        """
        初始化ElasticsearchIndexManager实例并连接到Elasticsearch服务器
        """
        try:

            self.es = Elasticsearch(
                [ELASTICSEARCH_URL],
                http_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
                verify_certs=True
            )
            _log.info(f"成功连接到Elasticsearch: {ELASTICSEARCH_URL}")
        except Exception as e:
            _log.error(f"无法连接到Elasticsearch服务器: {e}")
            raise

    def create_index(self, index_name, settings=None, mappings=None):
        """
        创建Elasticsearch索引

        参数:
            index_name (str): 索引名称
            settings (dict): 索引设置 (可选)
            mappings (dict): 索引映射 (可选)

        返回:
            bool: 索引创建是否成功
        """
        try:
            body = {}
            if settings:
                body['settings'] = settings
            if mappings:
                body['mappings'] = mappings

            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=body)
                _log.info(f"成功创建Elasticsearch索引: {index_name}")
                return True
            else:
                _log.warning(f"索引 {index_name} 已存在，跳过创建。")
                return False
        except TransportError as e:
            _log.error(f"创建索引 {index_name} 时出错: {e}")
            return False

    def delete_index(self, index_name):
        """
        删除Elasticsearch索引

        参数:
            index_name (str): 索引名称

        返回:
            bool: 索引删除是否成功
        """
        try:
            if self.es.indices.exists(index=index_name):
                self.es.indices.delete(index=index_name)
                _log.info(f"成功删除Elasticsearch索引: {index_name}")
                return True
            else:
                _log.warning(f"索引 {index_name} 不存在，无法删除。")
                return False
        except TransportError as e:
            _log.error(f"删除索引 {index_name} 时出错: {e}")
            return False

    def update_index(self, index_name, settings=None, mappings=None):
        """
        更新Elasticsearch索引的设置和映射

        参数:
            index_name (str): 索引名称
            settings (dict): 更新的设置 (可选)
            mappings (dict): 更新的映射 (可选)

        返回:
            bool: 索引更新是否成功
        """
        try:
            if self.es.indices.exists(index=index_name):
                if settings:
                    self.es.indices.put_settings(index=index_name, body=settings)
                    _log.info(f"成功更新Elasticsearch索引 {index_name} 的设置")
                if mappings:
                    self.es.indices.put_mapping(index=index_name, body=mappings)
                    _log.info(f"成功更新Elasticsearch索引 {index_name} 的映射")
                return True
            else:
                _log.warning(f"索引 {index_name} 不存在，无法更新。")
                return False
        except TransportError as e:
            _log.error(f"更新索引 {index_name} 时出错: {e}")
            return False

    def bulk_insert(self, index_name, data):
        """
        批量插入数据到Elasticsearch索引中

        参数:
            index_name (str): 索引名称
            data (list): 要插入的文档列表

        返回:
            bool: 插入操作是否成功
        """
        try:
            if not self.es.indices.exists(index=index_name):
                _log.error(f"索引 {index_name} 不存在，无法插入数据。")
                return False

            actions = [
                {
                    "_index": index_name,
                    "_source": doc
                }
                for doc in data
            ]
            success, _ = bulk(self.es, actions)
            _log.info(f"成功插入 {success} 条记录到索引 {index_name} 中。")
            return True
        except TransportError as e:
            _log.error(f"批量插入数据到索引 {index_name} 时出错: {e}")
            return False

    def search(self, index_name, query):
        """
        在Elasticsearch索引中执行搜索查询

        参数:
            index_name (str): 索引名称
            query (dict): 查询条件

        返回:
            list: 查询结果
        """
        try:
            # 如果索引不存在，先创建索引
            if not self.es.indices.exists(index=index_name):
                _log.warning(f"索引 {index_name} 不存在，正在创建...")
                self.create_index(index_name)  # 自动创建索引

            result = self.es.search(index=index_name, body=query)
            hits = result.get("hits", {}).get("hits", [])
            _log.info(f"搜索索引 {index_name} 成功，找到 {len(hits)} 条记录。")
            _log.debug(f"搜索结果: {hits}")
            return [hit.get("_source", {}) for hit in hits]
        except TransportError as e:
            _log.error(f"在索引 {index_name} 中执行搜索时出错: {e}")
            return []
