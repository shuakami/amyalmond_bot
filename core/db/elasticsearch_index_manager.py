"""
AmyAlmond Project - core/db/elasticsearch_index_manager.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

elasticsearch_index_manager.py - 负责Elasticsearch索引的创建、更新和管理
"""
import uuid
from datetime import datetime, timezone

from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import bulk, BulkIndexError
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
            _log.info("<ELASTICSEARCH> 成功连接到Elasticsearch服务器:")
            _log.info(f"   ↳ URL: {ELASTICSEARCH_URL}")
        except Exception as e:
            _log.error("<ERROR> 无法连接到Elasticsearch服务器:")
            _log.error(f"   ↳ 错误详情: {e}")
            raise


    def get_all_indices(self):
        """
        获取Elasticsearch服务器上的所有索引名称

        返回:
            list: 索引名称列表
        """
        try:
            indices = self.es.cat.indices(format="json")
            index_names = [index["index"] for index in indices]
            _log.info("<ELASTICSEARCH> 获取所有索引名称成功:")
            _log.info(f"   ↳ 索引列表: {index_names}")
            return index_names
        except TransportError as e:
            _log.error("<ERROR> 获取索引列表时出错:")
            _log.error(f"   ↳ 错误详情: {e}")
            return []

    def get_index_mapping(self, index_name):
        """
        获取指定索引的映射

        参数:
            index_name (str): 索引名称

        返回:
            dict: 索引映射
        """
        try:
            if self.es.indices.exists(index=index_name):
                mapping = self.es.indices.get_mapping(index=index_name)
                _log.info(f"<ELASTICSEARCH> 获取索引 '{index_name}' 的映射成功:")
                _log.debug(f"   ↳ 映射: {mapping}")
                return mapping
            else:
                _log.warning(f"<ELASTICSEARCH> 索引 '{index_name}' 不存在，无法获取映射")
                return None
        except TransportError as e:
            _log.error(f"<ERROR> 获取索引 '{index_name}' 的映射时出错:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None

    def delete_document(self, index_name, document_id):
        """
        从Elasticsearch索引中删除文档

        参数:
            index_name (str): 索引名称
            document_id (str): 文档ID
        """
        try:
            if self.es.indices.exists(index=index_name):
                self.es.delete(index=index_name, id=document_id)
                _log.info(f"<ELASTICSEARCH> 成功删除文档:")
                _log.info(f"   ↳ 索引名称: {index_name}")
                _log.info(f"   ↳ 文档ID: {document_id}")
                return True
            else:
                _log.warning(f"<ELASTICSEARCH> 索引 '{index_name}' 不存在，无法删除文档")
                return False
        except TransportError as e:
            _log.error(f"<ERROR> 删除文档时出错:")
            _log.error(f"   ↳ 索引名称: {index_name}")
            _log.error(f"   ↳ 文档ID: {document_id}")
            _log.error(f"   ↳ 错误详情: {e}")
            return False

    def create_index(self, index_name, settings=None, mappings=None):
        """
        创建Elasticsearch索引
        """
        try:
            body = {}
            if settings:
                body['settings'] = settings
            if mappings:
                body['mappings'] = mappings

            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=body)
                _log.info("<INDEX> 成功创建Elasticsearch索引:")
                _log.info(f"   ↳ 索引名称: {index_name}")
                return True
            else:
                _log.warning("<INDEX> 索引已存在，跳过创建:")
                _log.warning(f"   ↳ 索引名称: {index_name}")
                return False
        except TransportError as e:
            _log.error("<ERROR> 创建索引时出错:")
            _log.error(f"   ↳ 索引名称: {index_name}")
            _log.error(f"   ↳ 错误详情: {e}")
            return False

    def delete_index(self, index_name):
        """
        删除Elasticsearch索引
        """
        try:
            if self.es.indices.exists(index=index_name):
                self.es.indices.delete(index=index_name)
                _log.info("<INDEX> 成功删除Elasticsearch索引:")
                _log.info(f"   ↳ 索引名称: {index_name}")
                return True
            else:
                _log.warning("<INDEX> 索引不存在，无法删除:")
                _log.warning(f"   ↳ 索引名称: {index_name}")
                return False
        except TransportError as e:
            _log.error("<ERROR> 删除索引时出错:")
            _log.error(f"   ↳ 索引名称: {index_name}")
            _log.error(f"   ↳ 错误详情: {e}")
            return False

    def update_index(self, index_name, settings=None, mappings=None):
        """
        更新Elasticsearch索引的设置和映射
        """
        try:
            if self.es.indices.exists(index=index_name):
                if settings:
                    self.es.indices.put_settings(index=index_name, body=settings)
                    _log.info("<INDEX> 成功更新索引设置:")
                    _log.info(f"   ↳ 索引名称: {index_name}")
                if mappings:
                    self.es.indices.put_mapping(index=index_name, body=mappings)
                    _log.info("<INDEX> 成功更新索引映射:")
                    _log.info(f"   ↳ 索引名称: {index_name}")
                return True
            else:
                _log.warning("<INDEX> 索引不存在，无法更新:")
                _log.warning(f"   ↳ 索引名称: {index_name}")
                return False
        except TransportError as e:
            _log.error("<ERROR> 更新索引时出错:")
            _log.error(f"   ↳ 索引名称: {index_name}")
            _log.error(f"   ↳ 错误详情: {e}")
            return False

    def bulk_insert(self, index_name, data):
        """
        批量插入数据到Elasticsearch索引中
        """
        try:
            if not self.es.indices.exists(index=index_name):
                _log.error("<ERROR> 索引不存在，无法插入数据:")
                _log.error(f"   ↳ 索引名称: {index_name}")
                return False

            actions = []
            for doc in data:
                doc_id = doc.get("_id", str(uuid.uuid4()))
                doc.pop("_id", None)
                doc["timestamp"] = doc.get("timestamp", datetime.now(timezone.utc).isoformat())

                actions.append({
                    "_index": index_name,
                    "_id": doc_id,
                    "_source": doc
                })

            _log.debug(f"<BULK INSERT> 尝试插入的数据: {actions}")

            success, _ = bulk(self.es, actions)
            _log.info("<BULK INSERT> 成功插入数据:")
            _log.info(f"   ↳ 插入数量: {success} 条记录")
            _log.info(f"   ↳ 目标索引: {index_name}")
            return True

        except BulkIndexError as e:
            _log.error("<ERROR> 批量插入数据时出错:")
            _log.error(f"   ↳ 错误详情: {e.errors}")  # 打印详细的错误信息
            _log.error(f"   ↳ 索引名称: {index_name}")
            return False
        except TransportError as e:
            _log.error("<ERROR> 批量插入数据时出错:")
            _log.error(f"   ↳ 索引名称: {index_name}")
            _log.error(f"   ↳ 错误详情: {e}")
            return False

    def search(self, index_name, query):
        """
        在Elasticsearch索引中执行搜索查询
        """
        try:
            if not self.es.indices.exists(index=index_name):
                _log.warning("<INDEX> 索引不存在，正在自动创建:")
                _log.warning(f"   ↳ 索引名称: {index_name}")
                self.create_index(index_name)

            result = self.es.search(index=index_name, body=query)
            hits = result.get("hits", {}).get("hits", [])
            _log.info("<SEARCH> 搜索成功:")
            _log.info(f"   ↳ 索引名称: {index_name}")
            _log.info(f"   ↳ 记录数: {len(hits)} 条")
            _log.debug(f"   ↳ 搜索结果: {hits}")
            return [hit.get("_source", {}) for hit in hits]
        except TransportError as e:
            _log.error("<ERROR> 搜索索引时出错:")
            _log.error(f"   ↳ 索引名称: {index_name}")
            _log.error(f"   ↳ 错误详情: {e}")
            return []
