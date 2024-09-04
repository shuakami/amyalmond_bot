import os
import re
import zipfile
import requests
from github import Github

# 配置
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")  # 使用当前仓库
API_URL = "https://api.openai-hk.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer hk-k416ch1000010138b9f6f6efae6a7a407995c942b8d9221a"
}

def get_version_from_file(file_path):
    """从指定文件中读取版本号信息。"""
    with open(file_path, 'r') as file:
        lines = file.readlines()
        version_line = lines[6]  # 第七行
        version_match = re.search(r'Version:\s*(.*)', version_line)
        if version_match:
            return version_match.group(1).strip()
    return None

def create_zip_file(version):
    """创建包含代码的 zip 文件，跳过指定目录。"""
    zip_filename = f"{version}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk('.'):
            if '.git' in root or '.github/workflows' in root:
                continue  # 跳过 .git 和 .github/workflows 目录
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, '.'))
    return zip_filename

def get_commit_history(repo, branch='main', limit=10):
    """获取最近的提交记录。"""
    commits = repo.get_commits(sha=branch)
    commit_messages = [commit.commit.message for commit in commits[:limit]]
    return "\n".join(commit_messages)

def create_release(repo, version, zip_filename, prerelease):
    """在 GitHub 上创建 release。"""
    release_name = version
    release_tag = f"v{version}"
    
    # 生成 release 描述
    commit_history = get_commit_history(repo)
    description = generate_release_description(version, commit_history)
    
    try:
        release = repo.create_git_release(
            tag=release_tag,
            name=release_name,
            message=description,
            draft=False,
            prerelease=prerelease  # 根据分支类型设置为预发布
        )
        with open(zip_filename, 'rb') as zip_file:
            release.upload_asset(zip_filename)
        print(f"Release {release_tag} 创建并上传成功。")
    except Exception as e:
        print(f"创建 Release 时出错: {e}")

def generate_release_description(version, commit_history):
    """使用 OpenAI API 生成 release 描述，包含提交记录。"""
    system_prompt = (
        "请为以下版本更新生成一个详细的 release 描述，包含更新内容、已知问题和鸣谢部分。"
        "以下是该版本的提交记录：\n"
        f"{commit_history}"
    )
    user_content = f"版本 {version} 的更新说明。"
    data = {
        "max_tokens": 500,
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    }
    
    response = requests.post(API_URL, headers=HEADERS, json=data)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']

if __name__ == "__main__":
    # 获取版本号
    version = get_version_from_file('main.py')
    if version:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # 检查当前分支
        current_branch = os.getenv('GITHUB_REF_NAME', '')
        prerelease = current_branch == 'develop'
        
        # 创建 zip 文件
        zip_filename = create_zip_file(version)
        # 创建 release 并上传 zip 文件
        create_release(repo, version, zip_filename, prerelease)
    else:
        print("未能从 main.py 文件中读取版本信息。")
