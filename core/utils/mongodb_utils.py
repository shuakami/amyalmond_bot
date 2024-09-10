from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient, errors
from config import MONGODB_URI, MONGODB_USERNAME, MONGODB_PASSWORD
from core.utils.logger import get_logger

_log = get_logger()

class MongoDBUtils:
    def __init__(self):
        """
        初始化MongoDBUtils实例，连接到指定的MongoDB数据库和集合
        """
        try:
            # 修改URI，增加authSource参数
            updated_uri = f"{MONGODB_URI}?authSource=admin"
            self.client = MongoClient(updated_uri, username=MONGODB_USERNAME, password=MONGODB_PASSWORD)
            self.db = self.client["amyalmond"]
            self.users_collection = self.db["users"]
            self.conversations_collection = self.db["conversations"]
            self.temp_memories_collection = self.db["temp_memories"]  # 临时记忆集合
            _log.info("<DB CONNECT> 成功连接到MongoDB:")
            _log.info(f"   ↳ URI: {updated_uri}")
            _log.info(f"   ↳ 数据库: amyalmond")
        except errors.ConnectionFailure as e:
            _log.error("<DB ERROR> 🚨无法连接到MongoDB服务器:")
            _log.error(f"   ↳ 错误详情: {e}")
            raise

    def get_all_database_names(self):
        """
        获取MongoDB服务器上的所有数据库名称

        返回:
            list: 数据库名称列表
        """
        try:
            db_names = self.client.list_database_names()
            _log.info("<DB INFO> 获取所有数据库名称成功:")
            _log.info(f"   ↳ 数据库列表: {db_names}")
            return db_names
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨获取数据库名称列表失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return []

    def get_all_collection_names(self, db_name):
        """
        获取指定数据库中的所有集合名称

        参数:
            db_name (str): 数据库名称

        返回:
            list: 集合名称列表
        """
        try:
            db = self.client[db_name]
            collection_names = db.list_collection_names()
            _log.info(f"<DB INFO> 获取数据库 '{db_name}' 中的所有集合名称成功:")
            _log.info(f"   ↳ 集合列表: {collection_names}")
            return collection_names
        except errors.PyMongoError as e:
            _log.error(f"<DB ERROR> 🚨获取数据库 '{db_name}' 中的集合名称列表失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return []

    def insert_temporary_memory(self, memory_document):
        """
        插入一份临时记忆到MongoDB的临时集合中，自动添加时间戳和ID
        """
        try:
            # 如果没有_id，MongoDB会自动生成
            memory_document["_id"] = memory_document.get("_id", ObjectId())
            # 如果没有时间戳，使用当前时间
            memory_document["timestamp"] = memory_document.get("timestamp", datetime.now(timezone.utc))

            result = self.temp_memories_collection.insert_one(memory_document)
            return result.inserted_id
        except errors.PyMongoError as e:
            _log.error(f"插入临时记忆失败: {e}")
            return None

    def find_temporary_memories(self, group_id):
        """
        获取特定群组的所有临时记忆
        """
        try:
            memories = list(self.temp_memories_collection.find({"group_id": group_id}))
            return memories
        except errors.PyMongoError as e:
            _log.error(f"查找临时记忆失败: {e}")
            return []

    def clear_temporary_memory(self, group_id):
        """
        清空特定群组的所有临时记忆
        """
        try:
            result = self.temp_memories_collection.delete_many({"group_id": group_id})
            return result.deleted_count
        except errors.PyMongoError as e:
            _log.error(f"清空临时记忆失败: {e}")
            return 0

    def insert_user(self, user_document):
        """
        插入一份用户文档到MongoDB的用户集合中，自动添加时间戳和ID
        """
        try:
            user_document["_id"] = user_document.get("_id", ObjectId())
            user_document["timestamp"] = user_document.get("timestamp", datetime.now(timezone.utc))

            result = self.users_collection.insert_one(user_document)
            _log.info("<DB INSERT> 插入用户文档成功:")
            _log.info(f"   ↳ _id: {result.inserted_id}")
            return result.inserted_id
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨插入用户文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None

    def find_user(self, query):
        """
        根据查询条件查找用户文档

        参数:
            query (dict): 查询条件
        返回:
            找到的用户文档（dict），如果未找到则返回None
        """
        try:
            user_document = self.users_collection.find_one(query)
            if user_document:
                _log.info("<DB FIND> 找到用户文档:")
                _log.info(f"   ↳ 文档内容: {user_document}")
            else:
                _log.info("<DB FIND> 未找到符合条件的用户文档:")
                _log.info(f"   ↳ 查询条件: {query}")
            return user_document
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨查询用户文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None
    def update_user(self, query, update_values):
        """
        根据查询条件更新用户文档

        参数:
            query (dict): 查询条件
            update_values (dict): 更新的内容
        返回:
            更新的结果
        """
        try:
            result = self.users_collection.update_one(query, {'$set': update_values})
            _log.info("<DB UPDATE> 更新用户文档成功:")
            _log.info(f"   ↳ 匹配数: {result.matched_count}")
            _log.info(f"   ↳ 修改数: {result.modified_count}")
            return result.modified_count
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨更新用户文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None

    def delete_user(self, query):
        """
        根据查询条件删除用户文档

        参数:
            query (dict): 查询条件
        返回:
            删除的结果
        """
        try:
            result = self.users_collection.delete_one(query)
            _log.info("<DB DELETE> 删除用户文档成功:")
            _log.info(f"   ↳ 删除数: {result.deleted_count}")
            return result.deleted_count
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨删除用户文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None

    def find_conversations(self, query):
        """
        根据查询条件查找多个对话文档

        参数:
            query (dict): 查询条件
        返回:
            找到的对话文档列表（list of dict），如果未找到则返回空列表
        """
        try:
            conversation_documents = list(self.conversations_collection.find(query))
            if conversation_documents:
                _log.info("<DB FIND> 找到对话文档:")
                _log.info(f"   ↳ 数量: {len(conversation_documents)}")
                _log.debug(f"   ↳ 文档内容: {conversation_documents}")
            else:
                _log.info("<DB FIND> 未找到符合条件的对话文档:")
                _log.info(f"   ↳ 查询条件: {query}")
            return conversation_documents
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨查询对话文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return []

    def find_all_conversations(self):
        """
        从MongoDB的对话集合中检索所有对话文档。

        返回:
            list[dict]: 包含所有对话文档的列表。
        """
        try:
            conversations = list(self.conversations_collection.find({}))
            _log.info("<DB FIND> 检索到所有对话记录:")
            _log.info(f"   ↳ 总记录数: {len(conversations)} 条")
            return conversations
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨检索所有对话文档时发生错误:")
            _log.error(f"   ↳ 错误详情: {e}")
            return []

    def insert_conversation(self, conversation_document):
        """
        插入一份对话文档到MongoDB的对话集合中，自动添加时间戳和ID
        """
        try:
            conversation_document["_id"] = conversation_document.get("_id", ObjectId())
            conversation_document["timestamp"] = conversation_document.get("timestamp", datetime.now(timezone.utc))

            result = self.conversations_collection.insert_one(conversation_document)
            _log.info("<DB INSERT> 插入对话文档成功:")
            _log.info(f"   ↳ _id: {result.inserted_id}")
            return result.inserted_id
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨插入对话文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None

    def find_conversation(self, query):
        """
        根据查询条件查找对话文档

        参数:
            query (dict): 查询条件
        返回:
            找到的对话文档（dict），如果未找到则返回None
        """
        try:
            conversation_documents = list(self.conversations_collection.find(query))
            if conversation_documents:
                _log.info("<DB FIND> 找到对话文档:")
                _log.info(f"   ↳ 数量: {len(conversation_documents)}")
                _log.debug(f"   ↳ 文档内容: {conversation_documents}")
            else:
                _log.info("<DB FIND> 未找到符合条件的对话文档:")
                _log.info(f"   ↳ 查询条件: {query}")
            return conversation_documents
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨查询对话文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return []

    def update_conversation(self, query, update_values):
        """
        根据查询条件更新对话文档

        参数:
            query (dict): 查询条件
            update_values (dict): 更新的内容
        返回:
            更新的结果
        """
        try:
            result = self.conversations_collection.update_one(query, {'$set': update_values})
            _log.info("<DB UPDATE> 更新对话文档成功:")
            _log.info(f"   ↳ 匹配数: {result.matched_count}")
            _log.info(f"   ↳ 修改数: {result.modified_count}")
            return result.modified_count
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨更新对话文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None

    def delete_conversation(self, query):
        """
        根据查询条件删除对话文档

        参数:
            query (dict): 查询条件
        返回:
            删除的结果
        """
        try:
            result = self.conversations_collection.delete_one(query)
            _log.info("<DB DELETE> 删除对话文档成功:")
            _log.info(f"   ↳ 删除数: {result.deleted_count}")
            return result.deleted_count
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨删除对话文档失败:")
            _log.error(f"   ↳ 错误详情: {e}")
            return None



    def close_connection(self):
        """
        关闭MongoDB连接
        """
        try:
            self.client.close()
            _log.info("<DB CLOSE> 成功关闭MongoDB连接")
        except errors.PyMongoError as e:
            _log.error("<DB ERROR> 🚨关闭MongoDB连接时出错:")
            _log.error(f"   ↳ 错误详情: {e}")
