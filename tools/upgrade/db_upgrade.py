import os
import json
import shutil
import datetime
import sys
import time
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers

# 手动指定项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# 将项目根目录添加到 Python 的搜索路径中
sys.path.append(project_root)
from config import MONGODB_URI, MONGODB_USERNAME, MONGODB_PASSWORD, ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, \
    ELASTICSEARCH_PASSWORD

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backup", "data")

# 连接数据库
mongo_client = MongoClient(MONGODB_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD)
mongo_db = mongo_client["amyalmond"]
mongo_collection = mongo_db["conversations"]

es_client = Elasticsearch(
    [ELASTICSEARCH_URL],
    basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
)


def backup_mongodb():
    """备份 MongoDB 数据"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, "mongodb", timestamp)

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    for document in mongo_collection.find():
        with open(os.path.join(backup_dir, f"{document['_id']}.json"), "w", encoding="utf-8") as file:
            json.dump(document, file, default=str)

    print(f"> MongoDB 数据备份完成，备份目录: {backup_dir}")


def backup_elasticsearch():
    """备份 Elasticsearch 数据"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, "elasticsearch", timestamp)

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    query = {"query": {"match_all": {}}}
    results = helpers.scan(es_client, index="messages", query=query)

    for i, result in enumerate(results):
        with open(os.path.join(backup_dir, f"{i}.json"), "w", encoding="utf-8") as file:
            json.dump(result, file, default=str)

    print(f"> Elasticsearch 数据备份完成，备份目录: {backup_dir}")


def backup_data():
    """备份旧数据"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_DIR, timestamp)

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.isfile(file_path):
            shutil.copy(file_path, backup_dir)
            print(f"> 备份文件: {filename} 到 {backup_dir}")

    print("> 文件数据备份完成.")


def prompt_clear_databases():
    """提示用户是否清空数据库"""
    print("> 即将清空 MongoDB 和 Elasticsearch 数据库。")
    print("> 请确认是否要继续，10 秒后将自动清空数据库...")
    time.sleep(10)

    print("> 清空 MongoDB 'conversations' 集合...")
    mongo_collection.delete_many({})
    print("> MongoDB 清空完成.")

    print("> 清空 Elasticsearch 'messages' 索引...")
    if es_client.indices.exists(index="messages"):
        es_client.options(ignore_status=[400, 404]).indices.delete(index="messages")
    es_client.indices.create(index="messages")
    print("> Elasticsearch 清空完成.")


def migrate_memory_json():
    """迁移 memory.json 数据到 MongoDB"""
    memory_json_path = os.path.join(DATA_DIR, "memory.json")

    if not os.path.exists(memory_json_path):
        print(f"! 未找到 memory.json 文件: {memory_json_path}")
        return

    with open(memory_json_path, "r", encoding="utf-8") as file:
        try:
            memory_data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"! 解析 memory.json 文件时发生错误: {e}")
            return

    for group_id, conversations in memory_data.items():
        for conversation in conversations:
            try:
                document = {
                    "group_id": group_id,
                    "role": conversation.get("role"),
                    "content": conversation.get("content"),
                    "timestamp": datetime.datetime.now(datetime.timezone.utc)
                }
                if not document["role"] or not document["content"]:
                    raise ValueError("无效数据，跳过")

                mongo_collection.insert_one(document)
                print(f"> 成功迁移对话记录到 MongoDB: group_id={group_id}, role={document['role']}")

            except Exception as e:
                print(f"! 迁移数据时发生错误，跳过: {e}, 数据: {conversation}")


def migrate_long_term_memory():
    """迁移 long_term_memory_*.txt 数据到 Elasticsearch"""
    for filename in os.listdir(DATA_DIR):
        if filename.startswith("long_term_memory_") and filename.endswith(".txt"):
            group_id = filename.split("long_term_memory_")[-1].replace(".txt", "")
            long_term_memory_path = os.path.join(DATA_DIR, filename)

            with open(long_term_memory_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            actions = []
            for line in lines:
                content = line.strip()
                if not content:
                    continue

                action = {
                    "_index": "messages",
                    "_source": {
                        "group_id": group_id,
                        "role": "system",
                        "content": content
                    }
                }
                actions.append(action)

            try:
                helpers.bulk(es_client, actions)
                print(f"> 成功迁移长时间记忆数据到 Elasticsearch: group_id={group_id}, 文件={filename}")

            except Exception as e:
                print(f"! 迁移 Elasticsearch 数据时发生错误: {e}, 文件: {filename}")


def main():
    # 打印项目根目录
    print("+------------------------------+")
    print("| 开始数据库迁移...             |")
    print("+------------------------------+")

    # 备份数据
    backup_data()
    backup_mongodb()
    backup_elasticsearch()

    # 提示用户是否清空数据库
    prompt_clear_databases()

    # 迁移 memory.json 数据到 MongoDB
    migrate_memory_json()

    # 迁移 long_term_memory_*.txt 数据到 Elasticsearch
    migrate_long_term_memory()

    print("+------------------------------+")
    print("| 数据库迁移完成                |")
    print("+------------------------------+")


if __name__ == "__main__":
    main()
