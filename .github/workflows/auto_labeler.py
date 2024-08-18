from github import Github
import requests
import json
import os

# 设置环境变量
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "shuakami/amyalmond_bot"

# 创建 Github 对象
g = Github(GITHUB_TOKEN)

# 获取仓库
repo = g.get_repo(REPO_NAME)

# 获取所有的未标记的 Issues
issues = repo.get_issues(state="open", labels=[])

# System prompt
system_prompt = (
    "你是一个优秀的代码问题标签助手。以下是 GitHub Issue 的描述内容，"
    "请根据内容给出适合的标签。"
    "你需要按以下格式返回标签：\n"
    "标签1, 标签2, 标签3\n"
    "其中，标签可以从下面自由选择：\n"
    "bot, blocked, bot-core, bug, discussion, documentation, duplicate, enhancement, good-first-issue, in-progress, "
    "memory-module, new-feature, on-hold, plugin-system, priority-high, priority-low, priority-medium, question, "
    "refactor, stubborn-bug, urgent-bug, wontfix。\n"
    "请确保返回的标签符合这些格式要求，标签之间用逗号分隔，不要包含其他文本或多余的字符。"
)

# 请求体模板
def create_request(issue_body):
    return {
        "max_tokens": 1200,
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "top_p": 1,
        "presence_penalty": 1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": issue_body}
        ]
    }

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer hk-k416ch1000010138b9f6f6efae6a7a407995c942b8d9221a"
}

# 遍历所有未标记的 Issues
for issue in issues:
    issue_body = issue.body
    data = create_request(issue_body)

    # 调用 OpenAI API
    response = requests.post("https://api.openai-hk.com/v1/chat/completions", headers=headers, data=json.dumps(data).encode('utf-8'))
    result = response.json()

    # 解析 LLM 返回的标签
    labels = [label.strip() for label in result['choices'][0]['message']['content'].split(',')]

    # 调试信息
    print(f"原始返回的标签: {result['choices'][0]['message']['content']}")
    print(f"解析后的标签: {labels}")

    # 确保标签合法
    valid_labels = [label for label in labels if label in [
        'bot', 'blocked', 'bot-core', 'bug', 'discussion', 'documentation', 'duplicate', 'enhancement', 'good-first-issue',
        'in-progress', 'memory-module', 'new-feature', 'on-hold', 'plugin-system', 'priority-high', 'priority-low',
        'priority-medium', 'question', 'refactor', 'stubborn-bug', 'urgent-bug', 'wontfix'
    ]]

    if valid_labels:
        # 逐个添加标签
        for label in valid_labels:
            try:
                issue.add_to_labels(label)
                print(f"已为 Issue #{issue.number} 添加标签: {label}")
            except Exception as e:
                print(f"添加标签 {label} 失败: {e}")
    else:
        print(f"未添加任何标签到 Issue #{issue.number}")
