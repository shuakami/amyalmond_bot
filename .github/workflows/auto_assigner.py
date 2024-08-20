from github import Github
import requests
import json
import os
from time import sleep

# 设置环境变量
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "shuakami/amyalmond_bot"

# 创建 Github 对象
g = Github(GITHUB_TOKEN)

# 获取仓库
repo = g.get_repo(REPO_NAME)

# 获取所有打开的 Issues，过滤出没有 Assignees 的
open_issues = list(repo.get_issues(state='open'))
issues_without_assignees = [issue for issue in open_issues if not issue.assignees]

# System prompt
system_prompt = (
    "你是一个高级的GitHub Issue分配助手。以下是一个或多个GitHub Issue的标题和描述，"
    "以及相关的对话参与者和仓库所有者的信息。"
    "请基于这些信息为每个Issue推荐最合适的Assignee。"
    "此外，请生成一条通知消息，告知被推荐的Assignee他们已经被系统指定为受理人或处理人。"
    "返回格式如下：\n"
    "Issue 1: Assignee1, Assignee2, Assignee3\n"
    "Message: 通知消息\n"
    "...\n"
    "请确保返回的Assignees符合这些格式要求，Assignees之间用逗号分隔，通知消息中可以使用@符号来提及相关人员。"
)

# 请求体模板
def create_request(issues_data):
    combined_content = "\n\n".join([f"Issue {i+1}:\n标题: {issue['title']}\n内容: {issue['body']}\n参与者: {issue['participants']}\n仓库所有者: {issue['owner']}" for i, issue in enumerate(issues_data)])
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

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer hk-k416ch1000010138b9f6f6efae6a7a407995c942b8d9221a"
}

# 批量处理 Issues
batch_size = 5
for i in range(0, len(issues_without_assignees), batch_size):
    batch = issues_without_assignees[i:i+batch_size]
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

    # 调用 OpenAI API
    response = requests.post("https://api.openai-hk.com/v1/chat/completions", headers=headers, data=json.dumps(data).encode('utf-8'))
    result = response.json()

    # 解析 LLM 返回的Assignees和通知消息
    content = result['choices'][0]['message']['content'].split("\n")
    assignees_per_issue = [line for line in content if line.startswith("Issue")]
    notification_message = next((line for line in content if line.startswith("Message:")), "")

    for j, issue_assignees in enumerate(assignees_per_issue):
        if i + j >= len(issues_without_assignees):
            break

        issue = issues_without_assignees[i + j]
        assignees = [assignee.strip() for assignee in issue_assignees.split(':')[1].split(',')]

        # 调试信息
        print(f"Issue #{issue.number} 原始返回的Assignees: {issue_assignees}")
        print(f"Issue #{issue.number} 解析后的Assignees: {assignees}")

        # 为 Issue 添加 Assignees
        if assignees:
            issue.add_to_assignees(*assignees)
            print(f"已为 Issue #{issue.number} 添加Assignees: {assignees}")

            # 回复通知消息
            if notification_message:
                notification_message = notification_message.replace("Message: ", "").replace("Issue 1:", f"Issue #{issue.number}:")
                issue.create_comment(notification_message)
                print(f"已在 Issue #{issue.number} 中添加通知消息。")
        else:
            print(f"Issue #{issue.number} 没有需要添加的Assignees。")

    # 添加延迟以避免 API 限制
    sleep(1)

print("所有无Assignees的 Issues 处理完成。")
