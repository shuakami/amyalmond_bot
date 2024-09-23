from fastapi import APIRouter, HTTPException, Body
from core.ace.secure import SecureInterface
from pydantic import BaseModel
from core.plugins.plugin_manager import PluginManager
from core.utils.logger import get_logger
from config import (  # 导入配置管理方法
    get_all_config,
    add_config,
    update_config,
    delete_config,
)


logger = get_logger()
router = APIRouter()
plugin_manager = PluginManager(bot_client=None)

class UpdateConfigModel(BaseModel):
    value: str


@router.get("/get_all")
async def get_configs():
    """获取所有配置"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        configs = get_all_config()
        return {"status": "success", "configs": configs}
    except Exception as e:
        logger.error(f"获取配置时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_config_api(key: str = Body(...), value: str = Body(...)):
    """添加新的配置项"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        if add_config(key, value):
            return {"status": "success", "message": f"配置项 '{key}' 添加成功"}
        else:
            raise HTTPException(status_code=400, detail=f"配置项 '{key}' 已存在")
    except Exception as e:
        logger.error(f"添加配置项时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/{key}")
async def update_config_api(key: str, body: UpdateConfigModel):
    """修改或添加配置项"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        if update_config(key, body.value):
            return {"status": "success", "message": f"配置项 '{key}' 修改成功"}
        else:
            raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")
    except Exception as e:
        logger.error(f"修改配置项时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{key}")
async def delete_config_api(key: str):
    """删除配置项"""
    secure_interface = SecureInterface()
    if not secure_interface.verify_request():
        return {"status": "error", "message": "验证码错误或已过期或者已经拒绝此请求"}

    try:
        if delete_config(key):
            return {"status": "success", "message": f"配置项 '{key}' 删除成功"}
        else:
            raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")
    except Exception as e:
        logger.error(f"删除配置项时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))