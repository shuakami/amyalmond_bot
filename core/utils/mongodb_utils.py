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
            self.client = MongoClient(MONGODB_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD)
            self.db = self.client["amyalmond"]
            self.users_collection = self.db["users"]
            self.conversations_collection = self.db["conversations"]
            _log.info(f"成功连接到MongoDB: {MONGODB_URI}, 数据库: amyalmond")
        except errors.ConnectionFailure as e:
            _log.error(f"无法连接到MongoDB服务器: {e}")
            raise

    def insert_user(self, user_document):
        """
        插入一份用户文档到MongoDB的用户集合中

        参数:
            user_document (dict): 要插入的用户文档
        返回:
            插入文档的_id
        """
        try:
            result = self.users_collection.insert_one(user_document)
            _log.info(f"插入用户文档成功, _id: {result.inserted_id}")
            return result.inserted_id
        except errors.PyMongoError as e:
            _log.error(f"插入用户文档失败: {e}")
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
                _log.info(f"根据查询条件找到用户文档: {user_document}")
            else:
                _log.info(f"未找到符合条件的用户文档: {query}")
            return user_document
        except errors.PyMongoError as e:
            _log.error(f"查询用户文档失败: {e}")
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
            _log.info(f"更新用户文档成功, 匹配数: {result.matched_count}, 修改数: {result.modified_count}")
            return result.modified_count
        except errors.PyMongoError as e:
            _log.error(f"更新用户文档失败: {e}")
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
            _log.info(f"删除用户文档成功, 删除数: {result.deleted_count}")
            return result.deleted_count
        except errors.PyMongoError as e:
            _log.error(f"删除用户文档失败: {e}")
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
                _log.info(f"根据查询条件找到 {len(conversation_documents)} 个对话文档")
                _log.debug(f"对话文档: {conversation_documents}")
            else:
                _log.info(f"未找到符合条件的对话文档: {query}")
            return conversation_documents
        except errors.PyMongoError as e:
            _log.error(f"查询对话文档失败: {e}")
            return []

    def find_all_conversations(self):
        """
        从MongoDB的对话集合中检索所有对话文档。

        返回:
            list[dict]: 包含所有对话文档的列表。
        """
        try:
            conversations = list(self.conversations_collection.find({}))
            _log.info(f"find_all_conversations 检索到 {len(conversations)} 条对话记录。")
            return conversations
        except errors.PyMongoError as e:
            _log.error(f"检索所有对话文档时发生错误: {e}")
            return []


    def insert_conversation(self, conversation_document):
        """
        插入一份对话文档到MongoDB的对话集合中

        参数:
            conversation_document (dict): 要插入的对话文档
        返回:
            插入文档的_id
        """
        try:
            result = self.conversations_collection.insert_one(conversation_document)
            _log.info(f"插入对话文档成功, _id: {result.inserted_id}")
            return result.inserted_id
        except errors.PyMongoError as e:
            _log.error(f"插入对话文档失败: {e}")
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
            conversation_document = self.conversations_collection.find_one(query)
            if conversation_document:
                _log.info(f"根据查询条件找到对话文档: {conversation_document}")
            else:
                _log.info(f"未找到符合条件的对话文档: {query}")
            return conversation_document
        except errors.PyMongoError as e:
            _log.error(f"查询对话文档失败: {e}")
            return None

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
            _log.info(f"更新对话文档成功, 匹配数: {result.matched_count}, 修改数: {result.modified_count}")
            return result.modified_count
        except errors.PyMongoError as e:
            _log.error(f"更新对话文档失败: {e}")
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
            _log.info(f"删除对话文档成功, 删除数: {result.deleted_count}")
            return result.deleted_count
        except errors.PyMongoError as e:
            _log.error(f"删除对话文档失败: {e}")
            return None

    def close_connection(self):
        """
        关闭MongoDB连接
        """
        try:
            self.client.close()
            _log.info("已成功关闭MongoDB连接")
        except errors.PyMongoError as e:
            _log.error(f"关闭MongoDB连接时出错: {e}")
