import os
from core.db.elasticsearch_index_manager import ElasticsearchIndexManager
from core.utils.mongodb_utils import MongoDBUtils
from core.utils.logger import get_logger
from config import ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD, MONGODB_URI, MONGODB_USERNAME, MONGODB_PASSWORD

_log = get_logger()

def log_elasticsearch_status(log_dir):
    """
    记录Elasticsearch的详细状态信息到指定文件中
    """
    es_manager = ElasticsearchIndexManager()
    es_status_file = os.path.join(log_dir, "elasticsearch_status.txt")

    try:
        cluster_health = es_manager.es.cluster.health()
        indices_stats = es_manager.es.indices.stats()
        nodes_stats = es_manager.es.nodes.stats()
        cat_indices = es_manager.es.cat.indices(format="json")

        with open(es_status_file, 'w', encoding='utf-8') as f:
            f.write("Elasticsearch 集群健康状态:\n")
            f.write(f"{cluster_health}\n\n")
            f.write("Elasticsearch 索引统计信息:\n")
            f.write(f"{indices_stats}\n\n")
            f.write("Elasticsearch 节点统计信息:\n")
            f.write(f"{nodes_stats}\n\n")
            f.write("Elasticsearch 索引详情:\n")
            f.write(f"{cat_indices}\n")

        _log.info("Elasticsearch状态信息已记录")
    except Exception as e:
        _log.error(f"记录Elasticsearch状态时发生错误: {e}")
        with open(es_status_file, 'w', encoding='utf-8') as f:
            f.write(f"记录Elasticsearch状态时发生错误: {e}\n")

def log_mongodb_status(log_dir):
    """
    记录MongoDB的详细状态信息到指定文件中
    """
    mongo_utils = MongoDBUtils()
    mongo_status_file = os.path.join(log_dir, "mongodb_status.txt")

    try:
        server_status = mongo_utils.db.command("serverStatus")
        db_stats = mongo_utils.db.command("dbStats")
        collections_stats = {}
        for collection_name in mongo_utils.db.list_collection_names():
            collections_stats[collection_name] = mongo_utils.db.command("collStats", collection_name)

        with open(mongo_status_file, 'w', encoding='utf-8') as f:
            f.write("MongoDB 服务器状态:\n")
            f.write(f"{server_status}\n\n")
            f.write("MongoDB 数据库状态:\n")
            f.write(f"{db_stats}\n\n")
            f.write("MongoDB 集合统计信息:\n")
            for collection_name, stats in collections_stats.items():
                f.write(f"集合: {collection_name}\n")
                f.write(f"{stats}\n\n")

        _log.info("MongoDB状态信息已记录")
    except Exception as e:
        _log.error(f"记录MongoDB状态时发生错误: {e}")
        with open(mongo_status_file, 'w', encoding='utf-8') as f:
            f.write(f"记录MongoDB状态时发生错误: {e}\n")

