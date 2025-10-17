# 🚀 LMArena Bridge - AI模型竞技场API代理器 🌉

> **📖 For English setup instructions, see [SETUP.md](SETUP.md)**  
> **📖 中文安装说明请继续阅读本文档**

欢迎来到新一代的 LMArena Bridge！🎉 这是一个基于 FastAPI 和 WebSocket 的高性能工具集，它能让你通过任何兼容 OpenAI API 的客户端或应用程序，无缝使用 [LMArena.ai](https://lmarena.ai/) 平台上提供的海量大语言模型。

这个重构版本旨在提供更稳定、更易于维护和扩展的体验。

## ✨ 主要功能

*   **🚀 高性能后端**: 基于 **FastAPI** 和 **Uvicorn**，提供异步、高性能的 API 服务。
*   **🔌 稳定的 WebSocket 通信**: 使用 WebSocket 替代 Server-Sent Events (SSE)，实现更可靠、低延迟的双向通信。
*   **🤖 OpenAI 兼容接口**: 完全兼容 OpenAI `v1/chat/completions`、`v1/models` 以及 `v1/images/generations` 端点。
*   **📋 手动模型列表更新**: 新增 `model_updater.py` 脚本，可手动触发从 LMArena 页面提取最新的可用模型列表，并保存为 `available_models.json`，方便查阅和更新核心的 `models.json`。
*   **📎 通用文件上传**: 支持通过 Base64 上传任意类型的文件（图片、音频、PDF、代码等），并支持一次性上传多个文件。
*   **🎨 原生流式文生图**: 文生图功能已与文本生成完全统一。只需在 `/v1/chat/completions` 接口中请求图像模型，即可像接收文本一样，流式接收到 Markdown 格式的图片。
*   **🗣️ 完整对话历史支持**: 自动将会话历史注入到 LMArena，实现有上下文的连续对话。
*   **🌊 实时流式响应**: 像原生 OpenAI API 一样，实时接收来自模型的文本回应。
*   **🔄 自动程序更新**: 启动时自动检查 GitHub 仓库，发现新版本时可自动下载并更新程序。
*   **🆔 一键式会话ID更新**: 提供 `id_updater.py` 脚本，只需在浏览器操作一次，即可自动捕获并更新 `config.jsonc` 中所需的会话 ID。
*   **⚙️ 浏览器自动化**: 配套的油猴脚本 (`LMArenaApiBridge.js`) 负责与后端服务器通信，并在浏览器中执行所有必要操作。
*   **🍻 酒馆模式 (Tavern Mode)**: 专为 SillyTavern 等应用设计，智能合并 `system` 提示词，确保兼容性。
*   **🤫 Bypass 模式**: 尝试通过在请求中额外注入一个空的用户消息，绕过平台的敏感词审查。
*   **🔐 API Key 保护**: 可在配置文件中设置 API Key，为你的服务增加一层安全保障。
*   **🎯 模型-会话高级映射**: 支持为不同模型配置独立的会话ID池，并能为每个会话指定特定的工作模式（如 `battle` 或 `direct_chat`），实现更精细的请求控制。

## ⚙️ 配置文件说明

项目的主要行为通过 `config.jsonc`, `models.json` 和 `model_endpoint_map.json` 进行控制。

### `models.json` - 核心模型映射
这个文件包含了 LMArena 平台上的模型名称到其内部ID的映射，并支持通过特定格式指定模型类型。

*   **重要**: 这是程序运行所**必需**的核心文件。你需要手动维护这个列表。
*   **格式**:
    *   **标准文本模型**: `"model-name": "model-id"`
    *   **图像生成模型**: `"model-name": "model-id:image"`
*   **说明**:
    *   程序通过检查模型ID字符串中是否包含 `:image` 来识别图像模型。
    *   这种格式保持了对旧配置文件的最大兼容性，未指定类型的模型将默认为 `"text"`。
*   **示例**:
    ```json
    {
      "gemini-1.5-pro-flash-20240514": "gemini-1.5-pro-flash-20240514",
      "dall-e-3": "null:image"
    }
    ```

### `available_models.json` - 可用模型参考 (可选)
*   这是一个**参考文件**，由新增的 `model_updater.py` 脚本生成。
*   它包含了从 LMArena 页面上提取的所有模型的完整信息（ID, 名称, 组织等）。
*   你可以运行 `model_updater.py` 来生成或更新此文件，然后从中复制你需要使用的模型信息到 `models.json` 中。

### `config.jsonc` - 全局配置

这是主要的配置文件，包含了服务器的全局设置。

*   `session_id` / `message_id`: 全局默认的会话ID。当模型没有在 `model_endpoint_map.json` 中找到特定映射时，会使用这里的ID。
*   `id_updater_last_mode` / `id_updater_battle_target`: 全局默认的请求模式。同样，当特定会话没有指定模式时，会使用这里的设置。
*   `use_default_ids_if_mapping_not_found`: 一个非常重要的开关（默认为 `true`）。
    *   `true`: 如果请求的模型在 `model_endpoint_map.json` 中找不到，就使用全局默认的ID和模式。
    *   `false`: 如果找不到映射，则直接返回错误。这在你需要严格控制每个模型的会话时非常有用。
*   其他配置项如 `api_key`, `tavern_mode_enabled` 等，请参考文件内的注释。

### `model_endpoint_map.json` - 模型专属配置

这是一个强大的高级功能，允许你覆盖全局配置，为特定的模型设置一个或多个专属的会话。

**核心优势**:
1.  **会话隔离**: 为不同的模型使用独立的会话，避免上下文串扰。
2.  **提高并发**: 为热门模型配置一个ID池，程序会在每次请求时随机选择一个ID使用，模拟轮询，减少单个会话被频繁请求的风险。
3.  **模式绑定**: 将一个会话ID与它被捕获时的模式（`direct_chat` 或 `battle`）绑定，确保请求格式永远正确。

**配置示例**:
```json
{
  "claude-3-opus-20240229": [
    {
      "session_id": "session_for_direct_chat_1",
      "message_id": "message_for_direct_chat_1",
      "mode": "direct_chat"
    },
    {
      "session_id": "session_for_battle_A",
      "message_id": "message_for_battle_A",
      "mode": "battle",
      "battle_target": "A"
    }
  ],
  "gemini-1.5-pro-20241022": {
      "session_id": "single_session_id_no_mode",
      "message_id": "single_message_id_no_mode"
  }
}
```
*   **Opus**: 配置了一个ID池。请求时会随机选择其中一个，并严格按照其绑定的 `mode` 和 `battle_target` 来发送请求。
*   **Gemini**: 使用了单个ID对象（旧格式，依然兼容）。由于它没有指定 `mode`，程序会自动使用 `config.jsonc` 中定义的全局模式。

## 🛠️ 安装与使用

你需要准备好 Python 环境和一款支持油猴脚本的浏览器 (如 Chrome, Firefox, Edge)。

### 1. 准备工作

*   **安装 Python 依赖**
    打开终端，进入项目根目录，运行以下命令：
    ```bash
    pip install -r requirements.txt
    ```

*   **安装油猴脚本管理器**
    为你的浏览器安装 [Tampermonkey](https://www.tampermonkey.net/) 扩展。

*   **安装本项目油猴脚本**
    1.  打开 Tampermonkey 扩展的管理面板。
    2.  点击“添加新脚本”或“Create a new script”。
    3.  将 [`TampermonkeyScript/LMArenaApiBridge.js`](TampermonkeyScript/LMArenaApiBridge.js) 文件中的所有代码复制并粘贴到编辑器中。
    4.  保存脚本。

### 2. 运行主程序

1.  **启动本地服务器**
    在项目根目录下，运行主服务程序：
    ```bash
    python api_server.py
    ```
    当你看到服务器在 `http://127.0.0.1:5102` 启动的提示时，表示服务器已准备就绪。

2.  **保持 LMArena 页面开启**
    确保你至少有一个 LMArena 页面是打开的，并且油猴脚本已成功连接到本地服务器（页面标题会以 `✅` 开头）。这里无需保持在对话页面，只要是域名下的页面都可以LeaderBoard都可以。

### 3. 更新可用模型列表 (可选，但推荐)
此步骤会生成 `available_models.json` 文件，让你知道当前 LMArena 上有哪些可用的模型，方便你更新 `models.json`。
1.  **确保主服务器正在运行**。
2.  打开**一个新的终端**，运行模型更新器：
    ```bash
    python model_updater.py
    ```
3.  脚本会自动请求浏览器抓取模型列表，并在根目录生成 `available_models.json` 文件。
4.  打开 `available_models.json`，找到你想要的模型，将其 `"publicName"` 和 `"id"` 键值对复制到 `models.json` 文件中（格式为 `"publicName": "id"`）。


#### 使用 [use-model.py](use-model.py:1) 快速生成 [models.json](models.json:1)

- 前置条件：确保已生成 [available_models.json](available_models.json:1)
  - 方式 A：运行 [model_updater.py](model_updater.py:1)（需要浏览器页面已连接，详见上文）
  - 方式 B：在 Docker+noVNC 模式下执行 `--self-test`，浏览器回传页面后由后端写入 `available_models.json`
- 生成 models.json（自动识别图像能力并加上 `:image` 后缀）：
  ```bash
  python use-model.py
  ```
  - 输出示例：`✅ 已生成 models.json，共 123 个模型。`
- 规则说明：
  - 从 `available_models.json` 读取每个条目的 `publicName` 与 `id`，写入到 [models.json](models.json:1)
  - 若条目 `capabilities.inputCapabilities.image == true`，则写入为 `"id:image"` 形式，供后端区分文生图模型
- 覆盖提醒：该脚本会整体覆盖现有 [models.json](models.json:1)，如需保留自定义条目，请先备份或在生成后再合并修改
- 验证：
  ```bash
  # 后端已启动的前提下
  curl http://127.0.0.1:5102/v1/models
  ```
  - 若返回包含新模型名，表示已生效
- 下一步（可选）：可在 [model_endpoint_map.json](model_endpoint_map.json:1) 为特定模型配置专属会话池，以实现并发与隔离
### 4. 配置会话 ID (需要时，一般只配置一次即可，除非切换模型或者原对话失效)

这是**最重要**的一步。你需要获取一个有效的会话 ID 和消息 ID，以便程序能够正确地与 LMArena API 通信。

1.  **确保主服务器正在运行**
    `api_server.py` 必须处于运行状态，因为 ID 更新器需要通过它来激活浏览器的捕获功能。

2.  **运行 ID 更新器**
    打开**一个新的终端**，在项目根目录下运行 `id_updater.py` 脚本：
    ```bash
    python id_updater.py
    ```
    *   脚本会提示你选择模式 (DirectChat / Battle)。
    *   选择后，它会通知正在运行的主服务器。

3.  **激活与捕获**
    *   此时，你应该会看到浏览器中 LMArena 页面的标题栏最前面出现了一个准星图标 (🎯)，这表示**ID捕获模式已激活**。
    *   在浏览器中打开一个 LMArena 竞技场的 **目标模型发送给消息的页面**。请注意，如果是Battle页面，请不要查看模型名称，保持匿名状态，并保证当前消息界面的最后一条是目标模型的一个回答；如果是Direct Chat，请保证当前消息界面的最后一条是目标模型的一个回答。
    *   **点击目标模型的回答卡片右上角的重试（Retry）按钮**。
    *   油猴脚本会捕获到 `sessionId` 和 `messageId`，并将其发送给 `id_updater.py`。

4.  **验证结果**
    *   回到你运行 `id_updater.py` 的终端，你会看到它打印出成功捕获到的 ID，并提示已将其写入 `config.jsonc` 文件。
    *   脚本在成功后会自动关闭。现在你的配置已完成！

### 5. 配置你的 OpenAI 客户端
将你的客户端或应用的 OpenAI API 地址指向本地服务器：
*   **API Base URL**: `http://127.0.0.1:5102/v1`
*   **API Key**: 如果 `config.jsonc` 中的 `api_key` 为空，则可随便输入；如果已设置，则必须提供正确的 Key。
*   **Model Name**: 在你的客户端中指定你想使用的模型名称（**必须与 `models.json` 中的名称完全匹配**）。服务器会根据这个名称查找对应的模型ID。

### 6. 开始聊天！ 💬
现在你可以正常使用你的客户端了，所有的请求都会通过本地服务器代理到 LMArena 上！

## 🤔 它是如何工作的？

这个项目由两部分组成：一个本地 Python **FastAPI** 服务器和一个在浏览器中运行的**油猴脚本**。它们通过 **WebSocket** 协同工作。

```mermaid
sequenceDiagram
    participant C as OpenAI 客户端 💻
    participant S as 本地 FastAPI 服务器 🐍
    participant MU as 模型更新脚本 (model_updater.py) 📋
    participant IU as ID 更新脚本 (id_updater.py) 🆔
    participant T as 油猴脚本 🐵 (在 LMArena 页面)
    participant L as LMArena.ai 🌐

    alt 初始化
        T->>+S: (页面加载) 建立 WebSocket 连接
        S-->>-T: 确认连接
    end

    alt 手动更新模型列表 (可选)
        MU->>+S: (用户运行) POST /internal/request_model_update
        S->>T: (WebSocket) 发送 'send_page_source' 指令
        T->>T: 抓取页面 HTML
        T->>S: (HTTP) POST /internal/update_available_models (含HTML)
        S->>S: 解析HTML并保存到 available_models.json
        S-->>-MU: 确认
    end

    alt 手动更新会话ID
        IU->>+S: (用户运行) POST /internal/start_id_capture
        S->>T: (WebSocket) 发送 'activate_id_capture' 指令
        T->>L: (用户点击Retry) 拦截到 fetch 请求
        T->>IU: (HTTP) 发送捕获到的ID
        IU->>IU: 更新 config.jsonc
        IU-->>-T: 确认
    end

    alt 正常聊天流程
        C->>+S: (用户聊天) /v1/chat/completions 请求
        S->>S: 转换请求为 LMArena 格式 (并从 models.json 获取模型ID)
        S->>T: (WebSocket) 发送包含 request_id 和载荷的消息
        T->>L: (fetch) 发送真实请求到 LMArena API
        L-->>T: (流式)返回模型响应
        T->>S: (WebSocket) 将响应数据块一块块发回
        S-->>-C: (流式) 返回 OpenAI 格式的响应
    end

    alt 正常聊天流程 (包含文生图)
        C->>+S: (用户聊天) /v1/chat/completions 请求
        S->>S: 检查模型名称
        alt 如果是文生图模型 (如 DALL-E)
            S->>S: (并行) 创建 n 个文生图任务
            S->>T: (WebSocket) 发送 n 个包含 request_id 的任务
            T->>L: (fetch) 发送 n 个真实请求
            L-->>T: (流式) 返回图片 URL
            T->>S: (WebSocket) 将 URL 发回
            S->>S: 将 URL 格式化为 Markdown 文本
            S-->>-C: (HTTP) 返回包含 Markdown 图片的聊天响应
        else 如果是普通文本模型
            S->>S: 转换请求为 LMArena 格式
            S->>T: (WebSocket) 发送包含 request_id 和载荷的消息
            T->>L: (fetch) 发送真实请求到 LMArena API
            L-->>T: (流式)返回模型响应
            T->>S: (WebSocket) 将响应数据块一块块发回
            S-->>-C: (流式) 返回 OpenAI 格式的响应
        end
    end
```

1.  **建立连接**: 当你在浏览器中打开 LMArena 页面时，**油猴脚本**会立即与**本地 FastAPI 服务器**建立一个持久的 **WebSocket 连接**。
    > **注意**: 当前架构假定只有一个浏览器标签页在工作。如果打开多个页面，只有最后一个连接会生效。
2.  **接收请求**: **OpenAI 客户端**向本地服务器发送标准的聊天请求，并在请求体中指定 `model` 名称。
3.  **任务分发**: 服务器接收到请求后，会根据 `model` 名称从 `models.json` 查找对应的模型ID，然后将请求转换为 LMArena 需要的格式，并附上一个唯一的请求 ID (`request_id`)，最后通过 WebSocket 将这个任务发送给已连接的油猴脚本。
4.  **执行与响应**: 油猴脚本收到任务后，会直接向 LMArena 的 API 端点发起 `fetch` 请求。当 LMArena 返回流式响应时，油猴脚本会捕获这些数据块，并将它们一块块地通过 WebSocket 发回给本地服务器。
5.  **响应中继**: 服务器根据每块数据附带的 `request_id`，将其放入正确的响应队列中，并实时地将这些数据流式传输回 OpenAI 客户端。

## 📖 API 端点

### 获取模型列表

*   **端点**: `GET /v1/models`
*   **描述**: 返回一个与 OpenAI 兼容的模型列表，该列表从 `models.json` 文件中读取。

### 聊天补全

*   **端点**: `POST /v1/chat/completions`
*   **描述**: 接收标准的 OpenAI 聊天请求，支持流式和非流式响应。

### 图像生成 (已集成)

*   **端点**: `POST /v1/chat/completions`
*   **描述**: 文生图功能现已完全集成到主聊天端点中。要生成图片，只需在请求体中指定一个图像模型（例如 `"model": "dall-e-3"`），然后像发送普通聊天消息一样发送请求即可。服务器会自动识别并处理。
*   **请求示例**:
    ```bash
    curl http://127.0.0.1:5102/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "dall-e-3",
        "messages": [
          {
            "role": "user",
            "content": "A futuristic cityscape at sunset, neon lights, flying cars"
          }
        ],
        "n": 1
      }'
    ```
*   **响应示例 (与普通聊天一致)**:
    ```json
    {
      "id": "img-as-chat-...",
      "object": "chat.completion",
      "created": 1677663338,
      "model": "dall-e-3",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "![A futuristic cityscape at sunset, neon lights, flying cars](https://...)"
          },
          "finish_reason": "stop"
        }
      ],
      "usage": { ... }
    }
    ```

## 📂 文件结构

```
.
├── .gitignore                  # Git 忽略文件
├── api_server.py               # 核心后端服务 (FastAPI) 🐍
├── id_updater.py               # 一键式会话ID更新脚本 🆔
├── model_updater.py              # 手动模型列表更新脚本 📋
├── models.json                 # 核心模型映射表 (需手动维护) 🗺️
├── available_models.json       # 可用模型参考列表 (自动生成) 📄
├── model_endpoint_map.json     # [高级] 模型到专属会话ID的映射表 🎯
├── requirements.txt            # Python 依赖包列表 📦
├── README.md                   # 就是你现在正在看的这个文件 👋
├── config.jsonc                # 全局功能配置文件 ⚙️
├── modules/
│   └── update_script.py        # 自动更新逻辑脚本 🔄
└── TampermonkeyScript/
    └── LMArenaApiBridge.js     # 前端自动化油猴脚本 🐵
```

**享受在 LMArena 的模型世界中自由探索的乐趣吧！** 💖

## 🧭 Docker+noVNC 浏览器自动化模式（命令行无头优先，遇 Cloudflare 切换到网页端可视操作）

本模式通过 Docker 启动一个带 WebDriver 与 noVNC 的 Chrome 实例，默认以“自动化+无头优先”的方式运行；当检测到 LMArena 的 Cloudflare 质询/认证时，会提示你打开 noVNC 网页进行人工操作，完成后自动回到无头自动化流程。

- 相关文件：
  - 启动器脚本：[`scripts/docker_browser_runner.py`](scripts/docker_browser_runner.py:1)
  - 一键启动（Windows）：[`run_docker_browser.bat`](run_docker_browser.bat:1)
  - 注入的用户脚本来源：[`TampermonkeyScript/LMArenaApiBridge.js`](TampermonkeyScript/LMArenaApiBridge.js:1)
  - 后端服务：[`api_server.py`](api_server.py:1)
  - Python 依赖：[`requirements.txt`](requirements.txt:1)

### 先决条件

- 已安装并运行 Docker Desktop（Windows 11）
- 本地已运行 LMArena Bridge 后端（默认端口 5102/5103）
  - 启动后端：  
    ```bash
    python api_server.py
    ```
- 首次安装依赖：  
  ```bash
  pip install -r requirements.txt
  ```

### 启动方式 A（推荐，Windows 一键脚本）

```bash
.\run_docker_browser.bat --url https://lmarena.ai/
```

- 首次运行会自动拉取镜像 `selenium/standalone-chrome:latest`，并映射 4444(WebDriver)/7900(noVNC)
- 脚本会连接 WebDriver，向所有新文档注入用户脚本（等价 Tampermonkey），随后访问 `--url` 指定页面

当命令行提示检测到 Cloudflare 质询时，会打印 noVNC 访问地址：
- 打开浏览器访问：`http://localhost:7900/?autoconnect=1&resize=scale&password=secret`
- 在 noVNC 页面中手动完成人机验证
- 回到命令行，按回车继续，即可恢复无头自动化流程

### 启动方式 B（Python 直接运行）

```bash
python scripts\docker_browser_runner.py --url https://lmarena.ai/
```

可选参数：
- `--image` 自定义镜像（默认 `selenium/standalone-chrome:latest`）
- `--name` 容器名称（默认 `lm_cf_browser`）
- `--keep-container` 退出时保留容器（默认退出即停止并清理容器）
- `--self-test` 启动后执行连通性自检；会通过本机 `POST /internal/request_model_update` 指令，等待浏览器回传页面后由后端更新 `available_models.json`，用于验证“容器浏览器 ⇄ 油猴脚本 ⇄ 本机后端”的通路是否畅通
- `--test-timeout` 自检的最大等待秒数（默认 45）

### 连通性自检（可选）

- 前置条件：本机后端已运行并监听 `http://127.0.0.1:5102`，且页面标题出现“✅”（表示脚本已连上 WebSocket）。
- 执行命令：
  ```bash
  .\run_docker_browser.bat --url https://lmarena.ai/ --self-test
  ```
- 判定标准：控制台出现“available_models.json 已更新，连通性自检通过”。若超时：
  - 检查网络/安全软件是否拦截 `host.docker.internal:5102/5103`
  - 打开 noVNC 后在容器内刷新 LMArena 页面（F5）
  - 确保页面标题出现“✅”标记

### 工作机制说明

- 用户脚本注入
  - 启动器通过 Chrome CDP 的 `Page.addScriptToEvaluateOnNewDocument` 将用户脚本在每个新文档的 document_start 注入，无需安装浏览器扩展
  - 为兼容容器网络，脚本中的本机地址会自动改写为 `host.docker.internal`：
    - `ws://localhost:5102` → `ws://host.docker.internal:5102`
    - `http://127.0.0.1:5103` → `http://host.docker.internal:5103`
  - 仅在 `*.lmarena.ai` 域自动生效，避免影响其他网站

- Cloudflare 检测与切换
  - 页面含 `challenges.cloudflare.com`/`cf-chl`/`turnstile` 等特征即判定需要人工介入
  - 启动器提示你打开 noVNC，完成验证后回车继续

- 会话保持
  - 验证通过后，继续以无头自动化方式访问目标页面；容器内浏览器与主机的后端通过 `host.docker.internal` 进行通信

### 常用操作

- 指定不同的起始页面：
  ```bash
  .\run_docker_browser.bat --url https://lmarena.ai/arena
  ```
- 保留容器用于长期观察（需手动停止）：
  ```bash
  python scripts\docker_browser_runner.py --keep-container
  docker rm -f lm_cf_browser
  ```

### 故障排查

- 访问 noVNC 空白/连接失败
  - 确认 Docker 容器正在运行（名称默认为 `lm_cf_browser`）
  - 检查端口是否被占用（7900/noVNC、4444/WebDriver）
- 容器内脚本连接不到本地后端
  - 确认 `api_server.py` 在本机运行且监听 `127.0.0.1:5102`
  - Windows 下 `host.docker.internal` 应可解析到宿主机；若网络策略限制，请放开 5102/5103 本机入站访问
- 一直提示 Cloudflare 验证
  - 在 noVNC 中刷新并重试；确保图形化验证已真正完成后，再回到命令行回车继续

### 启动方式 C（docker-compose）

- 适用场景：希望用 Compose 常驻启动带 WebDriver 与 noVNC 的容器浏览器，由宿主再运行引导器完成“连接 + Userscript 注入 + Cloudflare 处理”。
- 相关文件：
  - Compose 清单：[`docker-compose.yml`](docker-compose.yml:1)
  - 引导器：[`scripts/docker_browser_runner.py`](scripts/docker_browser_runner.py:1)
  - 后端服务：[`api_server.py`](api_server.py:1)

步骤
1) 启动后端（建议先开着）
   ```bash
   python api_server.py
   ```
2) 使用 Compose 启动容器浏览器
   ```bash
   docker compose up -d browser
   ```
   - 将启动一个名为 lm_cf_browser 的容器并映射 4444(WebDriver)/7900(noVNC)
   - 清单已包含 `extra_hosts: host.docker.internal:host-gateway` 以便容器访问宿主 5102/5103
3) 运行引导器连接远端 WebDriver、注入 Userscript 并导航
   ```bash
   # 推荐带自检，确认“容器浏览器 ⇄ Userscript ⇄ 本地后端”链路畅通
   python scripts\docker_browser_runner.py --url https://lmarena.ai/ --self-test --keep-container
   ```
   说明：
   - 引导器会检测到名为 `lm_cf_browser` 的容器已在运行，故不会重复创建
   - 若遇 Cloudflare，人机会在终端提示打开 noVNC：  
     http://localhost:7900/?autoconnect=1&amp;resize=scale&amp;password=secret
   - 完成人工验证后回车继续；标题出现“✅”代表 Userscript 已连上本地 WebSocket

常用操作
- 查看日志（容器侧）
  ```bash
  docker compose logs -f browser
  ```
- 停止/销毁
  ```bash
  docker compose stop browser
  docker compose down
  ```

可选：持久化浏览器配置（保留登录/Cookie）
- 需要在 [`docker-compose.yml`](docker-compose.yml:1) 的 `services.browser` 下自行添加（示例，按需开启）：
  ```yaml
  volumes:
    - chrome-config:/home/seluser/.config/google-chrome
    - chrome-cache:/home/seluser/.cache
  ```
  并在文件末尾添加：
  ```yaml
  volumes:
    chrome-config:
    chrome-cache:
  ```
- 这样重启容器后仍能保留会话与缓存（注意隐私与空间占用）。
