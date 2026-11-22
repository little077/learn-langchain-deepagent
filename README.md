# langchain-python

一个最小可运行的 **LangChain 1.x + LangGraph** 示例，包含：

- OpenAI 兼容接口（默认阿里云百炼）
- 3 个工具：`ask_user`、`get_current_time`、`web_search`
- `ask_user` 的 human-in-the-loop 暂停/恢复
- 自定义 `ReasoningChatModel`，提取 `reasoning_content` 思维链
- `langgraph.json` 接入 `langgraph dev` / Studio

## 目录结构

```text
langchain-python/
├─ core/                       # 公共底座：配置 + 模型
│  ├─ config.py                # 读取 .env，检查 LLM_API_KEY
│  ├─ llm.py                   # 创建 ReasoningChatModel
│  └─ reasoning_chat_model.py  # 扩展 ChatOpenAI，提取思维链
├─ tools/                      # 模型可以调用的工具
│  ├─ ask_user.py              # 暂停图，等待用户回答
│  ├─ current_time.py          # 返回当前时间
│  └─ web_search.py            # ddgs 网页搜索
├─ agent/                      # 智能体装配与运行
│  ├─ graph.py                 # 模型 + 工具 + 提示词 → 图
│  └─ run.py                   # 终端对话循环
├─ main.py                     # 终端入口
├─ start-dev.cmd               # Windows 启动脚本（强制 UTF-8）
├─ langgraph.json              # langgraph dev / Studio 入口清单
├─ pyproject.toml              # 依赖与打包配置
├─ AGENTS.md                   # AI 提交说明 + 按天学习日志
├─ README.md
├─ .env.example                # 可公开的环境变量模板
├─ .env                        # 真实密钥（已被 .gitignore）
├─ .gitignore
├─ .python-version
└─ .venv/                      # 项目专用虚拟环境
```

## 各目录职责

### `core/`：公共底座

这里放“所有模块都会用到的东西”，不参与具体业务对话。

- `config.py`
  - 从根目录 `.env` 读取配置。
  - 校验 `LLM_API_KEY` 是否为空。
  - 提供 `Settings` 数据类，避免各模块到处 `os.getenv`。
- `llm.py`
  - 对外只暴露 `build_model()`。
  - 返回 `ReasoningChatModel`，默认使用百炼的 OpenAI 兼容地址。
  - 以后要换 DeepSeek、OpenAI 或其他兼容服务，只改 `.env`，不用改业务代码。
- `reasoning_chat_model.py`
  - 继承 `langchain_openai.ChatOpenAI`。
  - 官方 `ChatOpenAI` 不提取第三方扩展字段 `reasoning_content`，这个类把它补上。
  - 非流式：重写 `_create_chat_result`。
  - 流式：重写 `_convert_chunk_to_generation_chunk`。
  - 思维链最终进入 `message.content_blocks`，类型为 `reasoning`。
  - `output_version = "v1"`，让 LangSmith 能直接渲染内容块。
  - 注册为 `openai_reasoning`，可用于 `init_chat_model("openai_reasoning:...")`；当前主流程直接实例化该类，不依赖注册。

### `tools/`：模型能做的动作

每个工具都是一个普通 Python 函数，用 `@tool` 装饰后交给模型。

模型看到的不是源码，而是：

- 工具名
- 参数类型
- docstring（工具说明）

所以 docstring 要写清楚“什么时候调用、参数是什么、返回什么”。

| 工具 | 作用 | 是否需要 Key |
|---|---|---|
| `ask_user` | 向用户提问并暂停图，等用户回答后继续 | 否 |
| `get_current_time` | 返回 `Asia/Shanghai` 当前日期和时间 | 否 |
| `web_search` | 用 `ddgs` 做网页搜索，返回标题、链接、摘要 | 否 |

`ask_user` 依赖 LangGraph 的 `interrupt()`：

1. 模型发起 `ask_user` 工具调用。
2. 工具内部调用 `interrupt({...})`。
3. 图暂停，状态由 checkpointer 保存。
4. 终端或 Studio 拿到用户回答后，用 `Command(resume=answer)` 恢复。
5. 工具返回回答，模型继续生成最终回复。

### `agent/`：智能体装配与运行

- `graph.py`
  - 用 `create_agent()` 把模型、工具、系统提示词拼成一张图。
  - 对外暴露 `graph` 变量，供 `langgraph.json` 引用。
  - 这里**不传 checkpointer**：`langgraph dev` 的 Agent Server 自己管理持久化；本地脚本才需要自己传。
- `run.py`
  - 终端对话循环。
  - 本地运行时创建 `InMemorySaver`，并生成一个 `thread_id`。
  - 捕获结果里的 `__interrupt__`，提示用户输入，再用 `Command(resume=...)` 恢复。
  - 打印最终回答，并在有思维链时打印 `[思考] ...`。

### 根目录文件

- `main.py`：终端入口，调用 `agent.run.main()`。
- `langgraph.json`：告诉 `langgraph dev` 加载哪个图、使用哪个 env 文件。
- `pyproject.toml`：依赖清单和包声明，类似前端的 `package.json`。
- `.env`：本地环境变量，**不要提交到 Git**。
- `.venv/`：项目专用虚拟环境，类似 `node_modules`，但 Python 的隔离更彻底。

## 一次对话怎么流动

```text
main.py
  └─ agent/run.py
       └─ agent/graph.py
            ├─ core/llm.py → ReasoningChatModel → OpenAI 兼容接口
            └─ tools/
                 ├─ ask_user.py
                 ├─ current_time.py
                 └─ web_search.py
```

普通问题：

```text
用户 → 模型 → 直接回答
```

需要工具：

```text
用户 → 模型 → 工具调用 → 工具结果 → 模型 → 最终回答
```

需要用户补充信息：

```text
用户 → 模型 → ask_user → interrupt 暂停
     → 用户回答 → Command(resume=...) → 工具返回 → 模型 → 最终回答
```

## 环境变量

第一次使用先复制模板：

```powershell
Copy-Item .env.example .env
```

然后编辑根目录 `.env`：

| 变量 | 是否必填 | 说明 |
|---|---|---|
| `LLM_API_KEY` | **必填** | 百炼、DeepSeek 或任何 OpenAI 兼容服务的 Key |
| `LLM_BASE_URL` | 已给默认 | 百炼地址：`https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | 已给默认 | 模板用 `qwen-plus`；换成账号已开通的模型即可 |
| `LANGSMITH_TRACING` | 可选 | 改成 `true` 才上传 trace |
| `LANGSMITH_API_KEY` | 可选 | LangSmith Key |
| `LANGSMITH_PROJECT` | 可选 | LangSmith 项目名 |
| `HTTPS_PROXY` / `HTTP_PROXY` | 可选 | 网页搜索不通时再配代理 |

换 DeepSeek 的示例：

```dotenv
LLM_API_KEY=你的 DeepSeek Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

注意：

- `.env` 的注释是英文，不是漏翻译。Windows 下 `langgraph dev` 会按 GBK 读取 `.env`，中文注释可能导致 `UnicodeDecodeError`。
- 不要把 Key 发到聊天或提交到 Git。
- `langgraph dev` 以 `.env` 为准；只在终端临时设置环境变量，可能被 `.env` 里的空值覆盖。
- `HTTPS_PROXY` / `HTTP_PROXY` 是进程级代理，配了之后模型和 LangSmith 请求也会走它，不只影响网页搜索。

## 学习日志与 AI 提交

根目录 [AGENTS.md](AGENTS.md) 是给 AI 的仓库说明，也是按天学习日志。每天结束时，让 AI：

1. 读 `AGENTS.md`
2. 看 `git diff <上一个tag>..HEAD`
3. 更新总览和当天详情
4. 生成总结，再提交 `dayNN: <主题>` 并打 tag

详细规则、每日记录模板和总结格式都在 `AGENTS.md` 里。

## 运行

### 终端对话

```powershell
cd C:\Users\Administrator\Desktop\langchain-python
.\.venv\Scripts\python.exe main.py
```

输入 `exit`、`quit` 或 `q` 退出。

### LangGraph 本地调试

Windows 下直接运行 `langgraph dev` 可能报 `UnicodeDecodeError: 'gbk' codec ...`，这是 Python 默认按 GBK 打开文件导致的，不是项目代码问题。用项目里的启动脚本：

```powershell
cd C:\Users\Administrator\Desktop\langchain-python
.\start-dev.cmd
```

它等价于先设置 UTF-8，再启动服务：

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\langgraph.exe dev
```

需要换端口或加参数时，直接传给脚本：

```powershell
.\start-dev.cmd --port 2025 --no-browser
```

启动后会打印：

- API 地址：`http://127.0.0.1:2024`
- Studio UI 地址：`https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

`langgraph.json` 不是 LangSmith 的配置文件。它只是本地 LangGraph 服务的入口清单；LangSmith 是独立的 trace 平台。两者配合使用：

- `langgraph dev` 会启动本地 API，并打印 Studio UI 地址。
- Studio 网页端托管在 `smith.langchain.com`，首次打开需要登录 LangSmith；登录不等于必须填 API Key。
- 要把每次模型/工具调用上传成 trace：设置 `LANGSMITH_TRACING=true` 和 `LANGSMITH_API_KEY`。

### 重新安装依赖

如果 `.venv` 被删除或换机器：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## 思维链说明

只有提供方真的返回 `reasoning_content` 时才有思维链。例如部分 Qwen3 思考模型会返回；OpenAI 官方接口不一定返回。

- 有返回：`ReasoningChatModel` 把它放进 `content_blocks`，终端打印 `[思考] ...`，LangSmith 也能渲染。
- 没返回：不会报错，只是没有 reasoning block，正常回答仍然可用。

## 代码检查（可选）

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

## 验收建议

填好 Key 后，依次试：

1. `现在几点了？` → 应调用 `get_current_time`
2. `帮我搜一下 LangGraph 最新教程，给链接` → 应调用 `web_search`
3. `先问我叫什么名字，再用名字跟我打招呼` → 应触发 `ask_user` 暂停，输入回答后继续

## 常见问题

**`LLM_API_KEY 还没填`**

打开 `.env`，把真实 Key 填到 `LLM_API_KEY=` 后面。`langgraph dev` 也读这个文件。

**模型 404 / 不存在**

`LLM_MODEL` 可能不在你的账号里。换成账号已开通的模型，例如 `qwen-plus`。

**网页搜索超时**

先在 `.env` 里取消代理注释并改成自己的端口：

```dotenv
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890
```

**`langgraph dev` 报 `UnicodeDecodeError: 'gbk' codec ...`**

这是 Windows 的默认文件编码问题，不是项目代码问题。用 `.\start-dev.cmd`，或先执行：

```powershell
$env:PYTHONUTF8 = "1"
```

Studio 显示 `Failed to initialize Studio` / `Failed to fetch`，通常也是因为后端服务已经因这个错误崩了。修好编码后重启服务，再刷新 Studio。

**终端打印中文报 `UnicodeEncodeError`**

`agent/run.py` 已把标准输出切到 UTF-8。如果仍然出现，先执行：

```powershell
chcp 65001
```
