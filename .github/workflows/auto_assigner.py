from github import Github
import requests
import json
import os
from time import sleep

# 配置
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "shuakami/amyalmond_bot"
BATCH_SIZE = 4  # 每次处理的 Issue 数量
SLEEP_TIME = 3  # 每次请求后的延迟时间，单位：秒
API_URL = "https://api.openai-hk.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer hk-k416ch1000010138b9f6f6efae6a7a407995c942b8d9221a"
}

# 创建 Github 对象
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def get_issues_without_assignees():
    """获取所有打开且没有分配人的 Issues。"""
    try:
        open_issues = repo.get_issues(state='open')
        return [issue for issue in open_issues if not issue.assignees]
    except Exception as e:
        print(f"获取 Issues 时出错: {e}")
        return []

def create_request(issues_data):
    """创建发送给 OpenAI API 的请求数据。"""
    system_prompt = (
        "你是一个高级的GitHub Issue分配助手。以下是多个或单个 GitHub Issue 的标题和描述，"
        "以及相关的参与者和仓库所有者的信息。"
        "请为每个 Issue 推荐最合适的 Assignee，并为推荐的 Assignee 生成一条通知消息。"
        "对于每个 Issue，请使用如下格式：\n"
        "Issue <编号>: Assignee1, Assignee2\n"
        "Message <编号>: 通知内容\n"
        "确保每个 Issue 至少有一个 Assignee，并且通知消息中使用 @ 符号提及相关人员，请尽量客气（不要提到issue序号，而是自己总结这个issue的内容输出合适的内容）。"
    )
    
    combined_content = "\n\n".join([
        f"Issue {i+1}:\n标题: {issue['title']}\n内容: {issue['body']}\n参与者: {issue['participants']}\n仓库所有者: {issue['owner']}"
        for i, issue in enumerate(issues_data)
    ])
    
    return {
        "max_tokens": 2000,
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "top_p": 1,
        "presence_penalty": 1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": combined_content}
        ]
    }

def parse_llm_response(response_content, num_issues):
    """解析语言模型的响应以提取每个 Issue 的 assignees 和通知消息。"""
    lines = response_content.split("\n")
    assignees_per_issue = []
    messages_per_issue = []

    for line in lines:
        if line.startswith("Issue"):
            assignees_per_issue.append(line)
        elif line.startswith("Message"):
            messages_per_issue.append(line)

    # 检查解析到的数量是否匹配请求的 Issue 数量
    if len(assignees_per_issue) != num_issues or len(messages_per_issue) != num_issues:
        raise ValueError("响应中 Issue 的数量与请求数量不匹配")

    return assignees_per_issue, messages_per_issue

def assign_and_notify(issue, assignees, notification_message):
    """为 Issue 分配用户并添加通知评论。"""
    if assignees:
        try:
            issue.add_to_assignees(*assignees)
            print(f"已为 Issue #{issue.number} 添加Assignees: {assignees}")
            # 格式化并发布通知消息
            if notification_message:
                notification_message_formatted = notification_message.replace("Message: ", "").replace(f"Issue 1:", f"Issue #{issue.number}:")
                issue.create_comment(notification_message_formatted)
                print(f"已在 Issue #{issue.number} 中添加通知消息。")
        except Exception as e:
            print(f"分配用户到 Issue #{issue.number} 时出错: {e}")
    else:
        print(f"Issue #{issue.number} 没有需要添加的Assignees。")

def process_issues():
    """批量处理 Issues 的主函数。"""
    issues = get_issues_without_assignees()
    
    for i in range(0, len(issues), BATCH_SIZE):
        batch = issues[i:i+BATCH_SIZE]
        issues_data = []
        
        for issue in batch:
            participants = [comment.user.login for comment in issue.get_comments()] + [issue.user.login]
            owner = repo.owner.login
            issues_data.append({
                "title": issue.title,
                "body": issue.body,
                "participants": ", ".join(set(participants)),
                "owner": owner
            })
        
        data = create_request(issues_data)
        try:
            response = requests.post(API_URL, headers=HEADERS, json=data)
            response.raise_for_status()
            result = response.json()
            assignees_per_issue, messages_per_issue = parse_llm_response(result['choices'][0]['message']['content'], len(batch))
            
            for j in range(len(batch)):
                if i + j >= len(issues):
                    break
                issue = issues[i + j]
                assignees = [assignee.strip() for assignee in assignees_per_issue[j].split(':')[1].split(',')]
                notification_message = messages_per_issue[j].split(': ', 1)[1]
                assign_and_notify(issue, assignees, notification_message)
        except requests.exceptions.RequestException as e:
            print(f"调用 OpenAI API 时出错: {e}")
        except (KeyError, IndexError, ValueError) as e:
            print(f"解析 OpenAI API 响应时出错: {e}")
        
        sleep(SLEEP_TIME)

    print("所有无Assignees的 Issues 处理完成。")

if __name__ == "__main__":
    process_issues()
