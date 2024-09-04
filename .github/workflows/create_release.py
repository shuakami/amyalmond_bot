import os
import re
import zipfile
import requests
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
API_URL = "https://api.openai-hk.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer hk-k416ch1000010138b9f6f6efae6a7a407995c942b8d9221a"
}

def get_version_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        version_line = lines[6]
        version_match = re.search(r'Version:\s*(.*)', version_line)
        if version_match:
            version = version_match.group(1).strip()
            tag = 'v' + version.replace(' ', '-').replace('(', '').replace(')', '')
            print(f"版本号 {version} 成功转换为 tag {tag}")
            return tag
    print("未能读取到版本号信息")
    return None

def create_zip_file(version):
    zip_filename = f"{version}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk('.'):
            if '.git' in root or '.github/workflows' in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, '.'))
    print(f"创建 zip 文件：{zip_filename}")
    return zip_filename

def get_commit_history(repo, branch='main', limit=10):
    try:
        commits = repo.get_commits(sha=branch)
        commit_details = []
        for commit in commits[:limit]:
            commit_data = f"Commit: {commit.commit.message}\nAuthor: {commit.commit.author.name}\nDate: {commit.commit.author.date}\n\n"
            files_changed = commit.files
            for file in files_changed:
                commit_data += f"File: {file.filename}\nChanges: {file.patch}\n\n"
            commit_details.append(commit_data)
        print("成功获取提交记录")
        return "\n".join(commit_details)
    except Exception as e:
        print(f"获取提交历史记录时出错: {e}")
        return "获取提交历史记录失败。"

def create_release(repo, version, zip_filename, prerelease):
    release_name = f"amyalmond_bot {version}"
    release_tag = version
    
    existing_tags = [tag.name for tag in repo.get_tags()]
    tag_suffix = 1
    original_release_tag = release_tag
    while release_tag in existing_tags:
        release_tag = f"{original_release_tag}#{tag_suffix}"
        tag_suffix += 1
        print(f"Tag {release_tag} 已存在，尝试新的 tag {release_tag}")

    current_branch = os.getenv('GITHUB_REF_NAME', 'main')
    commit_history = get_commit_history(repo, branch=current_branch)
    description = generate_release_description(version, commit_history, prerelease)
    
    try:
        release = repo.create_git_release(
            tag=release_tag,
            name=release_name,
            message=description,
            draft=False,
            prerelease=prerelease
        )
        with open(zip_filename, 'rb') as zip_file:
            release.upload_asset(zip_filename)
        print(f"Release {release_tag} 创建并上传成功")
    except Exception as e:
        print(f"创建 Release 时出错: {e}")

def generate_release_description(version, commit_history, prerelease):
    caution_message = "注意：这是一个开发版，请谨慎更新。" if prerelease else ""
    system_prompt = (
        f"请为以下版本更新生成一个详细的 release 描述，包含更新内容、已知问题和鸣谢部分。"
        f"开头部分固定使用：hi，我是洛小黑。给各位带来amyalmond_bot {version}的自动打包~ {caution_message}"
        f"以下是该版本的提交记录和具体更改：\n"
        f"{commit_history}"
    )
    user_content = f"版本 {version} 的更新说明。"
    data = {
        "max_tokens": 2500,
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
    print("生成的 release 描述成功")
    return result['choices'][0]['message']['content']

if __name__ == "__main__":
    version = get_version_from_file('main.py')
    if version:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        current_branch = os.getenv('GITHUB_REF_NAME', '')
        prerelease = current_branch == 'develop'
        
        zip_filename = create_zip_file(version)
        create_release(repo, version, zip_filename, prerelease)
    else:
        print("未能从 main.py 文件中读取版本信息。")
