from pymongo import MongoClient
from elasticsearch import Elasticsearch
from config import MONGODB_URI, MONGODB_USERNAME, MONGODB_PASSWORD, ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, \
    ELASTICSEARCH_PASSWORD

# MongoDB 配置
DATABASE_NAME = 'amyalmond'
CONVERSATION_COLLECTION = 'conversations'

# Elasticsearch 配置
ES_INDEX_NAME = 'messages'

# 连接到 MongoDB
mongo_client = MongoClient(
    MONGODB_URI,
    username=MONGODB_USERNAME,
    password=MONGODB_PASSWORD
)
db = mongo_client[DATABASE_NAME]
conversation_collection = db[CONVERSATION_COLLECTION]

# 连接到 Elasticsearch
es = Elasticsearch(
    [ELASTICSEARCH_URL],
    basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    verify_certs=True
)


def clear_mongodb():
    # 清空 MongoDB 集合中的所有数据
    delete_result = conversation_collection.delete_many({})
    print(f"从 MongoDB 中删除了 {delete_result.deleted_count} 条记录")


def clear_elasticsearch():
    # 删除 Elasticsearch 索引，然后重新创建索引
    if es.indices.exists(index=ES_INDEX_NAME):
        es.indices.delete(index=ES_INDEX_NAME)
        print(f"Elasticsearch 索引 {ES_INDEX_NAME} 已删除")

    # 重新创建索引
    es.indices.create(index=ES_INDEX_NAME)
    print(f"Elasticsearch 索引 {ES_INDEX_NAME} 已重新创建")


if __name__ == "__main__":
    clear_mongodb()
    clear_elasticsearch()
    print("数据库清理完成。")
