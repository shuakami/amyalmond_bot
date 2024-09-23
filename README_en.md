<div align="center">

# AmyAlmond Chatbot

  [![License](https://img.shields.io/badge/license-MPL2-red.svg)](hhttps://opensource.org/license/mpl-2-0)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
  [![GitHub Stars](https://img.shields.io/github/stars/shuakami/amyalmond_bot.svg)](https://github.com/shuakami/amyalmond_bot/stargazers)
  [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/shuakami/amyalmond_bot)
  [![Version](https://img.shields.io/badge/version-1.3.0_(Stable_923001)-yellow.svg)](https://github.com/shuakami/amyalmond_bot/releases)

[English](README_en.md) | 简体中文

⭐ Your go-to chatbot for supercharging group chats ⭐

[Features](#功能特性) • [Screenshots](#先看效果) •  [Docs](#安装部署开发) • [Contribute](#开发与贡献) • [License](#许可证)
</div>

## Features

AmyAlmond is an LLM API-powered smart chatbot designed to seamlessly integrate into QQ groups and channels.

By leveraging LLM API, AmyAlmond offers context-aware intelligent responses, enhancing user interaction and supporting long-term memory management. Whether it’s automating replies or boosting user engagement, she handles complex conversations like a breeze.

- 🌈 She uses the **LLM API** to generate human-like responses based on conversation context, with customizable prompts.
- 💗 Integrated with QQ’s official Python SDK, so you don’t have to worry about being blocked.
- 🔥 Automatically recognizes and remembers user names, providing a personalized interaction experience.
- 🧠 Equipped with **long-term and short-term memory**, she can record and recall important information, ensuring continuity in conversations.
- 🐳 Administrators can control her behavior with specific commands.
- ⭐ **Full configuration hot-reloading** reduces restart times, boosting efficiency.
- 🪝 Detailed logs and code comments make debugging and monitoring a breeze.

## Curious about the results?

![效果图_对话注册](/dist/background-en/chat-demo.png)  
![效果图_记忆上下文](/dist/background-en/chat-memory-demo.png)

## Installation/Deployment/Development

<a href="https://www.notion.so/tiancailuoxiaohei/dfd73a088f7745d39244bbcecbbaf910?v=972fb97796534341aca87a165039a3b1">
    <img src="/dist/background-en/docs-background.png" alt="Documentation Database" />
</a>

<div align="center">
Click the image to jump in
</div>

## Contributing

We'd love to have you on board! Whether it’s adding new features, fixing bugs, or improving documentation, your contributions are welcome!

### Branch Strategy

We follow the Git Flow branching model:

- **main**: The stable branch, always ready for production.
- **develop**: The development branch, where all new features are integrated.
- **feature/**: Feature branches, created from `develop`, merged back once the feature is complete.
- **hotfix/**: Hotfix branches, used to quickly patch bugs, merged back into `main` and `develop`.

### How to Contribute

1. **Fork this repo**  
   Fork the project to your GitHub account.

2. **Create a branch**  
   Create a new feature branch for your changes:
   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. **Commit your changes**  
   Commit your code with clear and concise messages:
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```

4. **Push to GitHub**  
   Push your branch to GitHub:
   ```bash
   git push origin feature/AmazingFeature
   ```

5. **Create a Pull Request**  
   Create a Pull Request on GitHub, describing your changes and their impact.

## License

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

AmyAlmond is licensed under the [MPL 2.0 License](LICENSE). You are free to use, modify, and distribute this project, but you must open source any modified versions and retain the original author's copyright notice.

## Disclaimer

This project is for learning and research purposes only. The developers are not responsible for any consequences resulting from the use of this project. Please ensure compliance with relevant laws and respect others' intellectual property rights when using this project.

## Roadmap

Check out our [Project Board](https://github.com/users/shuakami/projects/1) for the latest updates!

q(≧▽≦q) You've read this far—how about dropping us a ⭐️?

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