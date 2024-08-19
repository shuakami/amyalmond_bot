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

# 获取所有 Issues（包括打开和关闭的），然后过滤出没有标签的
all_issues = list(repo.get_issues(state='all'))
issues_without_labels = [issue for issue in all_issues if len(list(issue.labels)) == 0]

# System prompt
system_prompt = (
    "你是一个优秀的代码问题标签助手。以下是多个 GitHub Issue 的标题和描述内容，"
    "请根据内容给出适合的标签。"
    "你需要按以下格式返回标签：\n"
    "Issue 1: 标签1, 标签2, 标签3\n"
    "Issue 2: 标签1, 标签2\n"
    "...\n"
    "其中，标签可以从下面自由选择：\n"
    "bot, blocked, bot-core, bug, discussion, documentation, duplicate, enhancement, good-first-issue, in-progress, "
    "memory-module, new-feature, on-hold, plugin-system, priority-high, priority-low, priority-medium, question, "
    "refactor, stubborn-bug, urgent-bug, wontfix。\n"
    "请确保返回的标签符合这些格式要求，标签之间用逗号分隔，不要包含其他文本或多余的字符。"
)

# 请求体模板
def create_request(issues_data):
    combined_content = "\n\n".join([f"Issue {i+1}:\n标题: {issue['title']}\n内容: {issue['body']}" for i, issue in enumerate(issues_data)])
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
for i in range(0, len(issues_without_labels), batch_size):
    batch = issues_without_labels[i:i+batch_size]
    issues_data = [{"title": issue.title, "body": issue.body} for issue in batch]
    
    data = create_request(issues_data)

    # 调用 OpenAI API
    response = requests.post("https://api.openai-hk.com/v1/chat/completions", headers=headers, data=json.dumps(data).encode('utf-8'))
    result = response.json()

    # 解析 LLM 返回的标签
    labels_per_issue = result['choices'][0]['message']['content'].split('\n')

    for j, issue_labels in enumerate(labels_per_issue):
        if i + j >= len(issues_without_labels):
            break
        
        issue = issues_without_labels[i + j]
        labels = [label.strip() for label in issue_labels.split(':')[1].split(',')]

        # 调试信息
        print(f"Issue #{issue.number} 原始返回的标签: {issue_labels}")
        print(f"Issue #{issue.number} 解析后的标签: {labels}")

        # 为 Issue 添加标签
        if labels:
            issue.add_to_labels(*labels)
            print(f"已为 Issue #{issue.number} 添加标签: {labels}")
        else:
            print(f"Issue #{issue.number} 没有需要添加的标签。")

    # 添加延迟以避免 API 限制
    sleep(1)

print("所有无标签的 Issues 处理完成。")
