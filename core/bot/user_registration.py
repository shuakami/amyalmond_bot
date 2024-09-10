from core.utils.logger import get_logger
from core.utils.user_management import add_new_user

_log = get_logger()

async def handle_new_user_registration(client, group_id, user_id, cleaned_content, msg_id):
    """
    处理新用户注册，检查用户是否已注册，并提示用户提供昵称
    """
    try:
        # 插件处理部分
        if client.plugin_manager:
            plugin_response = await client.plugin_manager.handle_event("on_registration", group_id=group_id, user_id=user_id, cleaned_content=cleaned_content, msg_id=msg_id)
            if plugin_response:
                _log.info(f"插件已处理注册逻辑，跳过默认处理")  # 添加日志以确认插件已处理事件
                return  # 如果插件处理成功，结束函数

        # 默认处理逻辑
        if user_id not in client.pending_users:
            _log.info("<REGISTRATION> 检测到未注册用户:")
            _log.info(f"   ↳ 用户ID: {user_id}")
            _log.info("   ↳ 操作: 提示用户提供昵称")

            await client.api.post_group_message(
                group_openid=group_id,
                content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                msg_id=msg_id
            )
            client.pending_users[user_id] = True
        else:
            if cleaned_content.strip():
                if await add_new_user(user_id, cleaned_content.strip()):
                    _log.info("<REGISTRATION> 新用户注册成功:")
                    _log.info(f"   ↳ 用户ID: {user_id}")
                    _log.info(f"   ↳ 昵称: {cleaned_content.strip()}")

                    await client.api.post_group_message(
                        group_openid=group_id,
                        content=f"原来是{cleaned_content}吗 ... 我已经记住你了~",
                        msg_id=msg_id
                    )
                else:
                    _log.info("<REGISTRATION> ✅用户已注册:")
                    _log.info(f"   ↳ 用户ID: {user_id}")
                    _log.info(f"   ↳ 昵称: {cleaned_content.strip()}")

                    await client.api.post_group_message(
                        group_openid=group_id,
                        content="你的昵称已经录入~",
                        msg_id=msg_id
                    )
            else:
                _log.info("<REGISTRATION> 用户未提供昵称，再次提示:")
                _log.info(f"   ↳ 用户ID: {user_id}")
                _log.info("   ↳ 操作: 提示用户提供昵称")

                await client.api.post_group_message(
                    group_openid=group_id,
                    content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                    msg_id=msg_id
                )
            client.pending_users.pop(user_id, None)
    except Exception as e:
        _log.error("<ERROR> 🚨新用户注册过程中出错:")
        _log.error(f"   ↳ 群组ID: {group_id}")
        _log.error(f"   ↳ 错误详情: {e}", exc_info=True)
