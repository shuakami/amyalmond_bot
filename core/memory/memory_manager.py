"""
AmyAlmond Project - core/memory/memory_manager.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.0 (Stable_827001)

memory_manager.py 包含管理消息历史和记忆存储的主要类和方法，支持MongoDB Full-Text Search+Elasticsearch以及智能记忆管理。
"""
import random
import jieba.analyse

from collections import deque
from core.llm.plugins.inject_memory_client import InjectMemoryClient
from core.db.elasticsearch_index_manager import ElasticsearchIndexManager
from core.utils.mongodb_utils import MongoDBUtils
from config import MAX_CONTEXT_TOKENS, MEMORY_THRESHOLD, OPENAI_SECRET, OPENAI_MODEL, OPENAI_API_URL, ELASTICSEARCH_QUERY_TERMS
from core.utils.logger import get_logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from core.llm.plugins.openai_client import OpenAIClient

_log = get_logger()


class MemoryManager:
    """
    管理消息历史和智能记忆存储的类
    """

    def __init__(self):
        """
        初始化 MemoryManager 实例，创建消息历史字典并连接到数据库
        """
        self.message_history = {}
        self.mongo = MongoDBUtils()  # 初始化MongoDB工具
        self.es_manager = ElasticsearchIndexManager()  # 初始化Elasticsearch管理器
        self.inject_client = InjectMemoryClient(OPENAI_SECRET, OPENAI_MODEL, OPENAI_API_URL)  # 初始化注入记忆的LLM客户端
        self.openai_client = OpenAIClient(OPENAI_SECRET, OPENAI_MODEL, OPENAI_API_URL)

    def add_message_to_history(self, group_id, message):
        """
        添加一条消息到指定群组的消息历史中

        参数:
            group_id (str): 群组的唯一标识符
            message (dict): 包含角色和内容的消息字典
        """
        if group_id not in self.message_history:
            self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_TOKENS)
        self.message_history[group_id].append(message)

    def get_message_history(self, group_id):
        """
        获取指定群组的消息历史

        参数:
            group_id (str): 群组的唯一标识符

        返回:
            deque: 包含消息历史的双端队列
        """
        return self.message_history.get(group_id, deque(maxlen=MAX_CONTEXT_TOKENS))

    async def compress_memory(self, group_id, get_gpt_response):
        """
        压缩消息历史以减少内存占用，如果消息历史超过最大允许Token数，将使用 GPT 生成摘要并替换历史记录

        参数:
            group_id (str): 群组的唯一标识符
            get_gpt_response (function): 用于获取 GPT 回复的函数

        返回:
            list: 压缩后的消息历史
        """
        message_history = self.get_message_history(group_id)

        # 过滤掉没有 'content' 键的消息
        valid_message_history = [msg for msg in message_history if 'content' in msg and msg['content'].strip()]

        token_count = sum(len(msg['content']) for msg in valid_message_history)

        # 创建新的列表来存储压缩后的消息历史记录
        compressed_history = valid_message_history

        if token_count > MAX_CONTEXT_TOKENS:
            summary = await get_gpt_response(
                list(valid_message_history), "你是高级算法机器，请在不忽略关键人名或数据以及细节的情况下总结无损压缩对话（20-40字）。"
            )
            compressed_history = [{"role": "assistant", "content": summary}]

            # 将摘要存储到Elasticsearch中，以便以后可以检索到
            await self.store_memory(group_id, None, "assistant", summary)
            _log.info(f"压缩群组 {group_id} 的消息历史，摘要内容：{summary}")

        return compressed_history

    async def store_memory(self, group_id, message, role, content):
        """
        智能存储消息到数据库，根据内容决定存储到MongoDB还是Elasticsearch。

        参数:
            group_id (str): 群组的唯一标识符
            message (GroupMessage): 包含角色和内容的消息对象，允许为None
            role (str): 角色，可能是 'user' 或 'assistant'
            content (str): 消息内容
        """
        try:
            _log.debug(f"正在存储消息: group_id={group_id}, role={role}, content={content}")

            if content is None:
                _log.warning(f">>>>遇到了一个空内容的消息: group_id={group_id}, role={role}")
                _log.warning(f">>>>请检查您的api或模型！")
                return  # 如果内容为空，则不存储

            # 短消息存储到MongoDB，长消息和摘要存储到Elasticsearch
            if len(content) <= MEMORY_THRESHOLD:
                # 存储到MongoDB
                self.mongo.insert_conversation({
                    "group_id": group_id,
                    "role": role,
                    "content": content
                })
                _log.info(f"消息已存储到MongoDB, group_id: {group_id}, role: {role}, content: {content}")
            else:
                # 存储到Elasticsearch
                self.es_manager.bulk_insert(index_name="messages", data=[{
                    "group_id": group_id,
                    "role": role,
                    "content": content
                }])
                _log.info(f"消息已存储到Elasticsearch, group_id: {group_id}, role: {role}, content: {content}")
        except Exception as e:
            _log.error(f"存储消息到数据库时发生错误: {e}", exc_info=True)

    async def load_memory(self):
        try:
            _log.info("正在加载消息历史...")

            # 从MongoDB加载消息历史
            conversations = self.mongo.find_all_conversations()
            for conversation in conversations:
                group_id = conversation.get('group_id')
                if group_id not in self.message_history:
                    self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_TOKENS)
                self.message_history[group_id].append(conversation.get('message', {}))

            _log.debug(f"MongoDB消息历史: {conversations}")
            _log.info("MongoDB消息历史加载完成。")

            # 使用 set 对消息进行去重
            unique_messages = set()
            for conversation in conversations:
                message = conversation.get('message', {})
                message_str = str(message)  # 将字典转换为字符串以便去重
                if message_str not in unique_messages:
                    group_id = conversation.get('group_id')
                    if group_id not in self.message_history:
                        self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_TOKENS)
                    self.message_history[group_id].append(message)
                    unique_messages.add(message_str)

            # 从Elasticsearch中加载更多记忆
            es_conversations = self.es_manager.search(index_name="messages", query={"query": {"match_all": {}}})
            for conversation in es_conversations:
                group_id = conversation.get('group_id')
                if group_id not in self.message_history:
                    self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_TOKENS)
                self.message_history[group_id].append({
                    "role": conversation.get('role'),
                    "content": conversation.get('content')
                })

            _log.debug(f"Elasticsearch消息历史: {es_conversations}")
            _log.info("Elasticsearch消息历史加载完成。")

            _log.info("所有消息历史已成功加载。")

        except Exception as e:
            _log.error(f"加载消息历史时发生错误: {e}", exc_info=True)

    async def retrieve_memory(self, group_id, query):
        try:
            # 首先使用本地分词进行高级搜索
            keywords = self.extract_keywords(query)
            _log.debug(f"提取的关键词: {keywords}")

            advanced_results = await self.advanced_search(group_id, " ".join(keywords))
            if not advanced_results:
                # 如果本地分词的高级搜索无结果，尝试使用LLM进行分词和高级搜索
                _log.info("高级搜索无结果，尝试使用LLM分词")
                semantic_keywords = await self.semantic_analysis(query)
                _log.debug(f"语义分析关键词: {semantic_keywords}")
                advanced_results = await self.advanced_search(group_id, " ".join(semantic_keywords))

            if advanced_results:
                sorted_results = self.sort_results_by_relevance(query, advanced_results)
                _log.info(f"排序后的搜索结果: {sorted_results}")
                return {"role": "system", "content": f"相关记忆: {sorted_results[0]['content']}"}

            # 如果所有高级搜索都无结果，作为最后手段，尝试基础搜索
            _log.info("高级搜索无结果，尝试基础搜索")
            basic_results = await self.basic_search(group_id, keywords)
            if basic_results:
                sorted_results = self.sort_results_by_relevance(query, basic_results)
                _log.info(f"排序后的基础搜索结果: {sorted_results}")
                return {"role": "system", "content": f"相关记忆: {sorted_results[0]['content']}"}
            else:
                _log.info("未找到相关记忆")
                return None

        except Exception as e:
            _log.error(f"检索记忆时发生错误: {e}", exc_info=True)
            return None

    def sort_results_by_relevance(self, query, results):
        # 准备文档集合
        documents = [result['content'] for result in results]
        documents.insert(0, query)  # 将查询添加到文档集合的开头

        # 创建TF-IDF向量化器
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        # 计算查询与每个文档的余弦相似度
        query_vec = tfidf_matrix[0:1]
        cosine_similarities = cosine_similarity(query_vec, tfidf_matrix[1:]).flatten()

        # 将相似度分数与结果配对，并按相似度降序排序
        sorted_results = sorted(zip(results, cosine_similarities), key=lambda x: x[1], reverse=True)

        # 返回排序后的结果
        return [item[0] for item in sorted_results]

    def extract_keywords(self, text, top_k=5):
        """使用jieba进行关键词提取"""
        keywords = jieba.analyse.extract_tags(text, topK=top_k)
        return keywords

    async def basic_search(self, group_id, keywords):
        query = {
            "group_id": group_id,
            "content": {"$regex": "|".join(keywords)}
        }
        _log.debug(f"MongoDB查询: {query}")
        results = self.mongo.find_conversations(query)
        _log.debug(f"MongoDB搜索结果: {results}")
        return results

    async def semantic_analysis(self, query):
        """使用LLM进行语义分析,提取关键概念"""
        system_prompt = "你是一个语义分析专家。请分析以下查询，提取出3-4个词，和一段推算搜索的语句（5-12字），用逗号分隔。你的所有结果都会带入对话数据库搜索，所以请尽量想象当时对话的上下文。"
        context = []  # 这里可以是空列表，因为我们不需要之前的对话上下文
        user_input = f"{query}"

        response = await self.openai_client.get_response(context=context, user_input=user_input,
                                                         system_prompt=system_prompt)

        if response:
            return response.strip().split(',')
        return []

    async def advanced_search(self, group_id, query_text):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"group_id": group_id}},
                        {
                            "more_like_this": {
                                "fields": ["content"],
                                "like": query_text,
                                "min_term_freq": 1,
                                "max_query_terms": ELASTICSEARCH_QUERY_TERMS
                            }
                        }
                    ]
                }
            }
        }

        _log.debug(f"Elasticsearch查询: {query}")
        results = self.es_manager.search(index_name="messages", query=query)
        _log.debug(f"Elasticsearch搜索结果: {results}")
        return [result['_source'] for result in results if '_source' in result]

    async def inject_memory_to_llm(self, group_id, prompt):
        """
        主动查询记忆并注入到LLM的System Prompt中

        参数:
            group_id (str): 群组的唯一标识符
            prompt (str): 用于生成系统提示的基础Prompt

        返回:
            str: 注入记忆后的系统提示
        """
        try:
            # 从历史对话中提取关键词
            keywords = await self.inject_client.get_keywords_for_memory_retrieval(prompt)

            # 检索相关记忆
            memory_results = await self.retrieve_memory(group_id, keywords)

            # 将检索到的记忆格式化并注入到System Prompt中 <B>
            memory_contexts = [{"role": "system", "content": f"相关记忆: {mem.get('content', '')}"} for mem in
                               memory_results]

            # 确保记忆内容唯一
            unique_memory_contexts = []
            for memory in memory_contexts:
                if memory not in unique_memory_contexts:
                    unique_memory_contexts.append(memory)

            # 混合插入唯一记忆内容
            full_prompt = [{"role": "system", "content": prompt}]
            for memory in unique_memory_contexts:
                insert_position = random.randint(0, len(full_prompt))
                full_prompt.insert(insert_position, memory)

            _log.info(f"生成的系统提示已注入记忆，group_id: {group_id}, prompt: {full_prompt}")
            return full_prompt

        except Exception as e:
            _log.error(f"注入记忆到LLM的System Prompt时发生错误: {e}", exc_info=True)
            return [{"role": "system", "content": prompt}]
