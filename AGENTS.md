# AGENTS.md

> 这个文件是给 AI 编码助手的仓库说明，同时也是本仓库的学习日志。
> 用户要求提交或总结时，先完整读一遍本文件，再按下面的流程执行。

## 仓库目标

这是一个按天学习 LangChain / LangGraph 的最小项目。每天只引入一个知识点，保持代码始终可运行。

学习内容由用户决定。AI 不要替用户决定“今天学什么”，也不要凭空补写学习结论。

## 目录速览

```text
core/      公共底座：配置、模型、ReasoningChatModel
tools/     模型可调用的工具：ask_user / get_current_time / web_search
agent/     智能体装配与终端运行
```

- `core/llm.py` 默认返回 `ReasoningChatModel`，用于提取 `reasoning_content`。
- 模型配置一律来自 `.env` 的 `LLM_*`：`core/config.py` 负责读取和解析，`core/llm.py` 只透传。代码里不要硬编码温度、超时、重试次数、模型名或地址。
- `agent/graph.py` 用 `create_agent()` 组装模型、工具和系统提示词。
- `agent/run.py` 是终端对话入口，负责 `ask_user` 的 interrupt / resume。
- `agent/contact_graph.py` 只挂 `ask_user`，用 `ToolStrategy(ContactInfo)` 输出结构化联系方式。
- `agent/contact_schema.py` 定义 `ContactInfo` 的 Pydantic 校验。
- `langgraph.json` 是 `langgraph dev` / Studio 的入口清单，当前注册了 `agent` 和 `contact_agent`。
- `start-dev.cmd` 是 Windows 启动脚本，强制 `PYTHONUTF8=1`。

## Tag 约定

- `day00`：最小可运行骨架。
- `dayNN`：第 NN 天学习结束时的代码快照。
- 一天一个 tag；tag 一旦创建，不移动、不删除、不覆盖。
- 提交信息格式：`dayNN: <中文主题>`，例如 `day01: 结构化输出`。
- 日常学习直接在 `main` 上提交；分支只用于同一天的多方案实验，不用于按天记录。

## 学习日志

### 总览

| Tag | 主题 | 一句话总结 | 日期 |
|---|---|---|---|
| day00 | 最小骨架 | 搭好 core/tools/agent 三层，接入 3 个工具，支持 ask_user 暂停/恢复 | 2026-11-22 |
| day01 | 结构化输出 | 独立联系方式图对比 ToolStrategy / ProviderStrategy，定位思考模式下 tool_choice 的 400 | 2026-11-22 |

### day00 - 最小骨架

- 日期：2026-11-22
- 一句话：搭好最小可运行的 LangChain + LangGraph 项目，包含 3 个工具和思维链提取。
- 改了什么：创建 `core/`、`tools/`、`agent/`；加入 `ask_user`、`get_current_time`、`web_search`；加入 `langgraph.json` 和 `start-dev.cmd`。
- 为什么：为后续按天学习 LangChain / LangGraph 知识点提供稳定基线。
- 怎么验证：`.\start-dev.cmd` 启动本地服务，打开 Studio；终端运行 `python main.py`。
- 结论/坑：Windows 下 `langgraph dev` 必须启用 `PYTHONUTF8=1`，否则会因 GBK 编码读取文件报错；`.env` 不提交。
- 相关文件：`core/`、`tools/`、`agent/`、`langgraph.json`、`start-dev.cmd`。

### day01 - 结构化输出

- 日期：2026-11-22
- 一句话：把联系方式收集做成独立图，对比 ToolStrategy 与 ProviderStrategy 两种结构化输出，并定位思考模式下 tool_choice 引起的 400。
- 改了什么：
  - 新增 `agent/contact_schema.py`：`ContactInfo` 只做最简校验，姓名/地址必须是字符串，电话必须纯数字。
  - 新增 `agent/contact_graph.py`：只挂 `ask_user`，用 `ToolStrategy(ContactInfo)` 输出结构化结果；在 `langgraph.json` 注册 `contact_agent`。
  - `core/config.py` / `core/llm.py`：模型配置全部改为从 `.env` 读取，新增 `LLM_TEMPERATURE`、`LLM_MAX_TOKENS`、`LLM_TIMEOUT`、`LLM_MAX_RETRIES`、`LLM_ENABLE_THINKING`；删除温度/超时/重试次数和模型名、地址的硬编码。
  - `.env.example` 补齐参数模板（英文注释，避免 GBK 读取问题）；README 更新环境变量、读取链路和 400 排错。
  - 新增 `docs/structured-output.md`：三种结构化输出实现的底层差异与踩坑记录。
- 为什么：学习结构化输出在 OpenAI 兼容 API 上的不同实现路径，同时把模型参数集中到 `.env` 管理。
- 怎么验证：`ruff check .` 通过；`contact_agent` 在 `LLM_ENABLE_THINKING=false` 下返回 `ContactInfo`，在 `true` 下复现 400；`ProviderStrategy` 在思考模式下正常返回；`tool_choice="auto"` 在思考模式下能正常调用工具。
- 结论/坑：思考模式不接受强制 `tool_choice`（`required` 或指定函数对象报 400）；`ToolStrategy` 内部正是把 `tool_choice` 设成 `"any"` 再被转成 `"required"`，因此与之冲突；指定具体函数名时服务端不报错但静默不返回 `tool_calls`。直接传 schema 会走 `AutoStrategy`，但内置白名单不含 qwen 模型，最终仍回落到 `ToolStrategy`。
- 相关文件：`agent/contact_schema.py`、`agent/contact_graph.py`、`langgraph.json`、`core/config.py`、`core/llm.py`、`.env.example`、`README.md`、`docs/structured-output.md`。

### 每日记录模板

```markdown
### dayNN - <主题>

- 日期：
- 一句话：
- 改了什么：
- 为什么：
- 怎么验证：
- 结论/坑：
- 相关文件：
```

## AI 提交前流程

用户说“提交 / 打个 tag / 帮我总结今天”时，按顺序执行：

1. 运行 `git status --short`，确认哪些文件真的改了。
2. 运行 `git describe --tags --abbrev=0`，找到上一个 tag。
3. 运行 `git diff --stat <上一个tag>..HEAD` 和 `git diff <上一个tag>..HEAD`，读实际改动。
4. 读取用户本次说明，确认今天的学习主题；用户没说就根据 diff 推断，并在日志里标注“推断”。
5. 更新本文件的“总览”表和当天详情；只写实际看到的内容。
6. 生成提交信息和当天的总结，先给用户看。
7. 用户确认后提交，再创建 annotated tag：

   ```bash
   git tag -a dayNN -m "dayNN: <主题>"
   ```

8. 如果用户还没给 day 编号，按现有 tag 顺延；不确定时先问，不要猜。

## 总结输出格式

给用户的每日总结固定用这个结构：

```markdown
## dayNN - <主题>

**一句话**：今天做了什么。

**改了什么**：按文件或模块列 2-5 条。

**为什么**：解决什么问题，或验证什么机制。

**怎么验证**：实际运行了什么命令，结果如何；没跑就写“未验证”。

**结论/坑**：今天真正学到的机制、踩到的坑、下一步。
```

要求：

- 不编造学习结论。
- 不把“代码改了”写成“已经掌握”。
- 没有验证结果就明确写“未验证”。
- 用户没提供动机时，写“待补充”或“推断”，不要替用户编理由。

## 禁止事项

- 不提交 `.env`、`.venv/`、`*.egg-info/`、缓存目录。
- 不把真实 API Key、LangSmith Key、代理密码写进文档或提交信息。
- 不移动、删除、覆盖已有 tag。
- 不执行 `git reset --hard`、`git push --force`、改写历史等破坏性操作。
- 用户没有明确要求时，不自动提交、不自动打 tag。

## 常用验证命令

```powershell
.\start-dev.cmd
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\ruff.exe check .
```
