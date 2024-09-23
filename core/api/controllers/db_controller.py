from fastapi import APIRouter, HTTPException, Body, Depends
from core.ace.secure import SecureInterface
from pydantic import BaseModel
from core.utils.logger import get_logger
from core.utils.mongodb_utils import MongoDBUtils

logger = get_logger()
router = APIRouter()

# 依赖注入 MongoDBUtils 实例
async def get_db():
    db = MongoDBUtils()
    try:
        yield db
    finally:
        db.close_connection()

class UpdateDocumentModel(BaseModel):
    update: dict

@router.get("/databases")
async def get_all_databases(db: MongoDBUtils = Depends(get_db)):
    """获取所有数据库名称"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        databases = db.get_all_database_names()
        return {"status": "success", "databases": databases}
    except Exception as e:
        logger.error(f"获取数据库列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections/{db_name}")
async def get_all_collections(db_name: str, db: MongoDBUtils = Depends(get_db)):
    """获取指定数据库中的所有集合名称"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        collections = db.get_all_collection_names(db_name)
        return {"status": "success", "collections": collections}
    except Exception as e:
        logger.error(f"获取数据库集合列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{db_name}/{collection_name}")
async def get_all_documents(db_name: str, collection_name: str, db: MongoDBUtils = Depends(get_db)):
    """获取指定集合中的所有文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 获取集合对象
        collection = db.client[db_name][collection_name]
        documents = list(collection.find({}))

        # 将 ObjectId 转换为字符串
        for document in documents:
            if "_id" in document:
                document["_id"] = str(document["_id"])

        return {"status": "success", "documents": documents}
    except Exception as e:
        logger.error(f"获取数据库文档列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{db_name}/{collection_name}")
async def insert_document(db_name: str, collection_name: str, document: dict = Body(...), db: MongoDBUtils = Depends(get_db)):
    """向指定集合中插入文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 获取集合对象
        collection = db.client[db_name][collection_name]
        result = collection.insert_one(document)
        return {"status": "success", "inserted_id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"插入数据库文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/find/{db_name}/{collection_name}")
async def find_document(db_name: str, collection_name: str, query: dict = Body(...),
                        db: MongoDBUtils = Depends(get_db)):
    """根据查询条件查找文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 获取集合对象
        collection = db.client[db_name][collection_name]
        # 查找文档
        cursor = collection.find(query)
        result = []
        for document in cursor:
            if "_id" in document:
                document["_id"] = str(document["_id"])  # 将 ObjectId 转换为字符串
            result.append(document)

        return {"status": "success", "documents": result}

    except Exception as e:
        logger.error(f"查找数据库文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/documents/{db_name}/{collection_name}")
async def update_document(db_name: str, collection_name: str, query: dict = Body(...), update_data: UpdateDocumentModel = Body(...), db: MongoDBUtils = Depends(get_db)):
    """根据查询条件更新文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 获取集合对象
        collection = db.client[db_name][collection_name]
        result = collection.update_one(query, update_data.update)
        return {"status": "success", "matched_count": result.matched_count, "modified_count": result.modified_count}
    except Exception as e:
        logger.error(f"更新数据库文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/documents/{db_name}/{collection_name}")
async def delete_document(db_name: str, collection_name: str, query: dict = Body(...), db: MongoDBUtils = Depends(get_db)):
    """根据查询条件删除文档"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        # 获取集合对象
        collection = db.client[db_name][collection_name]
        result = collection.delete_one(query)
        return {"status": "success", "deleted_count": result.deleted_count}
    except Exception as e:
        logger.error(f"删除数据库文档时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))