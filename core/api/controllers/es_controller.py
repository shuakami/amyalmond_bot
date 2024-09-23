from fastapi import APIRouter, HTTPException, Body, Depends
from core.ace.secure import SecureInterface
from pydantic import BaseModel
from core.utils.logger import get_logger
from core.db.elasticsearch_index_manager import ElasticsearchIndexManager

logger = get_logger()
router = APIRouter()

# 依赖注入 ElasticsearchIndexManager 实例
async def get_es():
    es = ElasticsearchIndexManager()
    try:
        yield es
    finally:
        pass  # Elasticsearch 连接不需要手动关闭

class UpdateDocumentModel(BaseModel):
    update: dict

@router.get("/indices")
async def get_all_indices(es: ElasticsearchIndexManager = Depends(get_es)):
    """获取所有索引名称"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        indices = es.get_all_indices()
        return {"status": "success", "indices": indices}
    except Exception as e:
        logger.error(f"获取索引列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mapping/{index_name}")
async def get_index_mapping(index_name: str, es: ElasticsearchIndexManager = Depends(get_es)):
    """获取指定索引的映射"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        mapping = es.get_index_mapping(index_name)
        if mapping:
            return {"status": "success", "mapping": mapping}
        else:
            return {"status": "not_found", "message": f"索引 '{index_name}' 不存在"}
    except Exception as e:
        logger.error(f"获取索引映射时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{index_name}")
async def get_all_documents(index_name: str, es: ElasticsearchIndexManager = Depends(get_es)):
    """获取指定索引中的所有文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 使用 match_all 查询获取所有文档
        query = {"query": {"match_all": {}}}
        documents = es.search(index_name, query)
        return {"status": "success", "documents": documents}
    except Exception as e:
        logger.error(f"获取文档列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{index_name}")
async def insert_document(index_name: str, document: dict = Body(...), es: ElasticsearchIndexManager = Depends(get_es)):
    """向指定索引中插入文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 使用 Elasticsearch 的 index API 插入文档
        result = es.es.index(index=index_name, body=document)  # 直接使用 es.es
        return {"status": "success", "inserted_id": result["_id"]}
    except Exception as e:
        logger.error(f"插入文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{index_name}/find")
async def find_document(index_name: str, query: dict = Body(...), es: ElasticsearchIndexManager = Depends(get_es)):
    """根据查询条件查找文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        documents = es.search(index_name, query)
        if documents:
            return {"status": "success", "documents": documents}
        else:
            return {"status": "not_found", "message": "未找到符合条件的文档"}
    except Exception as e:
        logger.error(f"查找文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/documents/{index_name}/update/{document_id}")
async def update_document(index_name: str, document_id: str, update_data: UpdateDocumentModel = Body(...), es: ElasticsearchIndexManager = Depends(get_es)):
    """根据文档ID更新文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 使用 Elasticsearch 的 update API 更新文档
        result = es.es.update(index=index_name, id=document_id, body=update_data.update) # 直接使用 es.es
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"更新文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{index_name}/delete/{document_id}")
async def delete_document(index_name: str, document_id: str, es: ElasticsearchIndexManager = Depends(get_es)):
    """根据文档ID删除文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        success = es.delete_document(index_name, document_id)
        if success:
            return {"status": "success", "message": f"文档 '{document_id}' 已删除"}
        else:
            return {"status": "not_found", "message": f"索引 '{index_name}' 或文档 '{document_id}' 不存在"}
    except Exception as e:
        logger.error(f"删除文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))