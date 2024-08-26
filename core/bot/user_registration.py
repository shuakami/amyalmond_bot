# user_registration.py
from core.utils.logger import get_logger
from core.utils.user_management import add_new_user

_log = get_logger()

async def handle_new_user_registration(client, group_id, user_id, cleaned_content, msg_id):
    """
    处理新用户注册，检查用户是否已注册，并提示用户提供昵称

    参数:
        client (BotClient): 机器人客户端实例
        group_id (str): 群组的唯一标识符
        user_id (str): 用户的唯一标识符
        cleaned_content (str): 用户发送的消息内容
        msg_id (str): 消息的唯一标识符
    """
    try:
        if user_id not in client.pending_users:
            _log.info(f"User {user_id} not registered. Prompting for nickname.")
            await client.api.post_group_message(
                group_openid=group_id,
                content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                msg_id=msg_id
            )
            client.pending_users[user_id] = True
        else:
            if cleaned_content.strip():
                if await add_new_user(user_id, cleaned_content.strip()):
                    _log.info(f"New user {user_id} registered with nickname: {cleaned_content.strip()}")
                    await client.api.post_group_message(
                        group_openid=group_id,
                        content=f"原来是{cleaned_content}吗 ... 我已经记住你了~",
                        msg_id=msg_id
                    )
                else:
                    _log.info(f"User {user_id} nickname already registered.")
                    await client.api.post_group_message(
                        group_openid=group_id,
                        content="你的昵称已经录入~",
                        msg_id=msg_id
                    )
            else:
                _log.info(f"User {user_id} did not provide a nickname. Prompting again.")
                await client.api.post_group_message(
                    group_openid=group_id,
                    content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                    msg_id=msg_id
                )
            client.pending_users.pop(user_id, None)
    except Exception as e:
        _log.error(f"Error during new user registration for group {group_id}: {e}", exc_info=True)
