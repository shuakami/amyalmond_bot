import zipfile

import requests
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from core.plugins.plugin_manager import PluginManager
from core.plugins.tools.add_plugin import create_plugin
from core.utils.logger import get_logger
import tempfile
import os
import shutil

logger = get_logger()
router = APIRouter()
plugin_manager = PluginManager(bot_client=None)



@router.post("/install")
async def install_plugin(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="上传文件不存在")

    try:
        # 使用 tempfile 来生成一个跨平台的临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        logger.info(f"文件 {file.filename} 已上传到 {tmp_file_path}")

        # 获取插件的目标安装目录
        plugin_name = os.path.splitext(file.filename)[0]
        plugins_dir = os.path.join("core", "plugins", plugin_name)

        if os.path.exists(plugins_dir):
            logger.warning(f"插件目录 {plugins_dir} 已存在，正在删除...")
            shutil.rmtree(plugins_dir)

        os.makedirs(plugins_dir, exist_ok=True)

        # 解压到插件目录
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            zip_ref.extractall(plugins_dir)

        logger.info(f"插件 {file.filename} 已成功解压到 {plugins_dir}")
        plugin_manager.load_plugins()  # 重新加载插件

        return {"status": "success", "message": f"插件 {file.filename} 已成功安装"}
    except Exception as e:
        logger.error(f"安装插件时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理上传的文件
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

@router.post("/url_install")
async def install_plugin_from_url(url: str):
    """
    通过提供zip文件链接安装插件。
    """
    tmp_file_path = None  # 初始化临时文件路径
    try:
        # 处理 zip 文件链接
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        logger.info(f"文件 {url} 已下载到 {tmp_file_path}")
        file_name = os.path.basename(url)  # 从链接中提取文件名

        # 获取插件的目标安装目录
        plugin_name = os.path.splitext(file_name)[0]
        plugins_dir = os.path.join("core", "plugins", plugin_name)

        if os.path.exists(plugins_dir):
            logger.warning(f"插件目录 {plugins_dir} 已存在,正在删除...")
            shutil.rmtree(plugins_dir)

        os.makedirs(plugins_dir, exist_ok=True)

        # 解压到插件目录
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            zip_ref.extractall(plugins_dir)

        logger.info(f"插件 {file_name} 已成功解压到 {plugins_dir}")
        plugin_manager.load_plugins()  # 重新加载插件

        return {"status": "success", "message": f"插件 {file_name} 已成功安装"}

    except Exception as e:
        logger.error(f"安装插件时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理下载的临时文件
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


@router.post("/uninstall")
async def uninstall_plugin(plugin_name: str):
    try:
        plugin_manager.uninstall_plugin(plugin_name)
        return {"status": "success", "message": f"插件 {plugin_name} 已成功卸载"}
    except Exception as e:
        logger.error(f"卸载插件时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/enable")
# async def enable_plugin(plugin_name: str):
#     try:
#         plugin_manager.enable_plugin(plugin_name)
#         return {"status": "success", "message": f"插件 {plugin_name} 已启用"}
#     except Exception as e:
#         logger.error(f"启用插件时出错: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/disable")
# async def disable_plugin(plugin_name: str):
#     try:
#         plugin_manager.disable_plugin(plugin_name)
#         return {"status": "success", "message": f"插件 {plugin_name} 已禁用"}
#     except Exception as e:
#         logger.error(f"禁用插件时出错: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_plugin_list():
    try:
        plugin_list = plugin_manager.get_plugin_list()
        return {"status": "success", "plugins": plugin_list}
    except Exception as e:
        logger.error(f"获取插件列表时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_plugins():
    """
    热重载所有插件
    """
    try:
        plugin_manager.reload_plugins()
        return {"status": "success", "message": "插件已成功热重载"}
    except Exception as e:
        logger.error(f"热重载插件时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add_plugin")
async def add_plugin(
    system_prompt: str = Body(..., embed=True),
    user_input: str = Body(..., embed=True)
):
    """
    使用LLM帮助用户创建插件的API接口

    参数:
        system_prompt (str): 逗号分隔的系统提示词，将在服务端转换为列表
        user_input (str): 用户输入的插件需求

    返回:
        dict: LLM生成的插件代码或相关信息
    """
    try:
        # 调用 create_plugin 函数来生成插件代码
        result = await create_plugin(system_prompt, user_input)
        return {"status": "success", "plugin_code": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建插件失败: {e}")