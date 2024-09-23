<div align="center">
  
  # AmyAlmond 聊天机器人
  
  [![License](https://img.shields.io/badge/license-MPL2-red.svg)](hhttps://opensource.org/license/mpl-2-0)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
  [![GitHub Stars](https://img.shields.io/github/stars/shuakami/amyalmond_bot.svg)](https://github.com/shuakami/amyalmond_bot/stargazers)
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/shuakami/amyalmond_bot)
  [![Version](https://img.shields.io/badge/version-1.3.0_(Stable_923001)-yellow.svg)](https://github.com/shuakami/amyalmond_bot/releases)

  [English](README_en.md) | 简体中文

 ⭐ 强大的聊天机器人，助力群聊智能化 ⭐
  
  [功能特性](#功能特性) • [效果图](#先看效果) •  [官方文档](#安装部署开发) • [开发与贡献](#开发与贡献) • [许可证](#许可证)
</div>

> ⚠️此版本为抢先体验版。如追求稳定请使用 1.2.0_(Stable_827001)

## 功能特性

AmyAlmond 是一个基于 LLM API 的智能聊天机器人，旨在无缝集成到 QQ 群聊、频道中。

通过利用LLM API，AmyAlmond 提供上下文感知的智能回复，增强用户互动体验，并支持长期记忆管理。无论是自动化回复还是提升用户参与度，她都能够轻松处理复杂的对话场景。

- 🌈  她使用**LLM API**，根据对话上下文生成类似人类的回复，且Prompt可定制。
- 💗  她使用QQ官方 Python SDK，再也不怕被封锁。
- 🔥  她会自动识别并记住用户姓名，提供个性化的互动体验。
- 🧠  她拥有**长期和短期记忆能力**，能够记录并引用重要信息，保障对话的延续性。
- 🐳  支持管理员通过特定命令控制机器人的行为。
- ⭐  **全配置支持热更新**，减少重启次数，提高效率。
- 🪝  日志、代码注释详细，方便调试和监控。

## 先看效果？
![效果图_对话注册](/dist/background/chat-demo.png)
![效果图_记忆上下文](/dist/background/chat-memory-demo.png)

## 安装/部署/开发


<a href="https://www.notion.so/tiancailuoxiaohei/dfd73a088f7745d39244bbcecbbaf910?v=972fb97796534341aca87a165039a3b1">
    <img src="/dist/background/docs-background.png" alt="文档数据库" />
</a>

<div align="center">
点击图片以跳转
</div>

## 开发与贡献

我们非常欢迎您。无论是提供新功能、修复问题，还是改进文档，都可以~

### 分支策略

我们采用 Git Flow 分支管理模型：

- **main**: 主分支，始终保持稳定可用的版本。
- **develop**: 开发分支，所有新功能在此分支上集成。
- **feature/**: 功能分支，从 `develop` 分支分出，开发完成后合并回 `develop`。
- **hotfix/**: 修复分支，用于修复紧急问题，完成后合并回 `main` 和 `develop`。

### 提交规范

1. **Fork 本仓库**  
   在您的 GitHub 账户中 fork 本项目。

2. **创建分支**  
   为您的改动创建一个新的功能分支：
   ```bash
   git checkout -b feature/AmazingFeature
   ```


3. **提交更改**  
   提交您的代码，并确保提交信息简洁明了：
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```

4. **推送到分支**  
   推送分支到 GitHub：
   ```bash
   git push origin feature/AmazingFeature
   ```

5. **创建 Pull Request**  
   在 GitHub 上创建一个 Pull Request，描述您的更改内容及其影响。



## 许可证
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

AmyAlmond 遵循 [MPL2 许可证](LICENSE)。您可以自由使用、修改和分发本项目，但在分发修改后的版本时，您需要开放源代码并保留原作者的版权声明。

## 免责声明

本项目仅供学习和研究使用，开发者不对任何因使用本项目而导致的后果负责。在使用本项目时，请确保遵守相关法律法规，并尊重他人的知识产权。

## 功能排期表
详见 [Project](https://github.com/users/shuakami/projects/1)

q(≧▽≦q) 看了这么久了~ 给我们一个 ⭐️ 呗？


<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="
      https://api.star-history.com/svg?repos=shuakami/amyalmond_bot&type=Date&theme=dark
    "
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="
      https://api.star-history.com/svg?repos=shuakami/amyalmond_bot&type=Date
    "
  />
  <img
    alt="amyalmond_bot Chart"
    src="https://api.star-history.com/svg?repos=shuakami/amyalmond_bot&type=Date"
  />
</picture>





