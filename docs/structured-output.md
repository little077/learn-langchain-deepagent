# 结构化输出：LangChain 在 OpenAI 兼容 API 上的三种实现

> 环境：langchain 1.5.2 / langchain-openai 1.8.5 / pydantic 2.14.4
> 模型：`qwen3.8-omni-flash`（阿里云 MaaS，`.../compatible-mode/v1`）
> 本文所有请求参数都是从这套版本里实际打印出来的，不是推测。

## 0. 一句话结论

让模型返回一个对象（而不是散文），LangChain 有三条路：

| 方式 | 写法 | 请求里真正生效的参数 | 本质 |
|---|---|---|---|
| 原生结构化输出 | `response_format=ProviderStrategy(ContactInfo)` | `response_format={"type":"json_schema",...}` | 服务端按 schema 生成 JSON |
| 函数调用 | `response_format=ToolStrategy(ContactInfo)` | `tool_choice="required"` + 一个伪造的工具 | 把 schema 伪装成工具参数 |
| 让 LangChain 自己选 | `response_format=ContactInfo` | 上面二者之一（自动探测） | `AutoStrategy` |

三种方式最终都会得到一个 `ContactInfo` 对象，但**向服务端提出的要求完全不同**。踩 400 的坑，根源就在于选了哪条路。

---

## 1. 路线 A：函数调用（ToolStrategy）

### 机制

模型本身只会产生两种东西：文本，或 `tool_calls`。`ToolStrategy` 利用后者：

1. 把 `ContactInfo` 的字段定义变成一个**假工具**，名字就叫 `ContactInfo`；
2. 把它和真实工具（`ask_user`）一起塞进请求的 `tools`；
3. 再把 `tool_choice` 钉死，迫使模型必须调用工具。

源码里的两步转换（`langchain/agents/factory.py`）：

```python
# 1) factory.py：ToolStrategy 分支
tool_choice = "any" if structured_output_tools else request.tool_choice
request.model.bind_tools(final_tools, tool_choice=tool_choice, ...)

# 2) langchain_openai/chat_models/base.py：发请求前的转换
elif tool_choice == "any":
    tool_choice = "required"
```

所以最终 HTTP 请求体里的关键字段是：

```json
{
  "tools": [
    { "type": "function", "function": { "name": "ContactInfo", "parameters": { ... } } },
    { "type": "function", "function": { "name": "ask_user", "parameters": { ... } } }
  ],
  "tool_choice": "required"
}
```

模型返回的 `tool_calls[].function.arguments` 是 JSON 字符串，LangChain 反序列化后交给 Pydantic 校验，通过就写进 `structured_response`。

### 校验失败怎么办

`ToolStrategy(ContactInfo, handle_errors=True)`：Pydantic 抛出的 `ValueError` 会被包成工具执行结果回给模型，让模型改参数重试。这也是它比"提示词里写请输出 JSON"更可靠的地方——错误有地方可去。

### 对服务端的要求

- 模型支持 function calling；
- **允许客户端强制 `tool_choice`**。

第二条正是本仓库 400 的来源，见第 4 节。

---

## 2. 路线 B：原生结构化输出（ProviderStrategy）

### 机制

不碰 `tool_choice`，也不伪造工具。它利用 OpenAI 兼容协议里另一个参数 `response_format`，把 JSON Schema 直接交给服务端：

```python
# ProviderStrategy.to_model_kwargs() 的实际输出
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "ContactInfo",
      "schema": {
        "properties": {
          "name":    {"type": "string", ...},
          "phone":   {"type": "string", ...},
          "address": {"type": "string", ...}
        },
        "type": "object"
      }
    }
  }
}
```

由服务端在解码阶段约束输出，客户端拿到的就是一段符合 schema 的 JSON。

### 对服务端的要求

- 服务商实现了 `response_format.type = "json_schema"` 这条协议。
- 不同厂商支持程度不同：有的只支持 `{"type":"json_object"}`（只保证是合法 JSON，不保证字段），有的要求模型版本；
- 部分模型不支持"同时挂工具 + 原生结构化输出"。LangChain 源码里对 Gemini 3 以前版本专门做了规避，说明这在行业内是普遍限制。

**这条路线能不能用，取决于服务商，不取决于 LangChain。** 本仓库所用的 endpoint 实测支持（思考模式下也正常）。

---

## 3. 路线 C：直接传 schema（AutoStrategy）

写法最短：

```python
create_agent(..., response_format=ContactInfo)
```

LangChain 会包一层 `AutoStrategy`，然后**猜**你的模型支持哪种方式（`_supports_provider_strategy`）：

1. 先看 `model.profile` 里有没有 `structured_output` 能力标记；
2. 没有标记，就拿模型名去匹配一份白名单：gpt-4.1 / 4o / 5.x、claude 4.5+、grok-4 等；
3. 匹配上 → 走 `ProviderStrategy`；匹配不上 → **回落 `ToolStrategy`**。

对本仓库的模型实测：

```text
profile: None
supports provider strategy: False
```

`qwen3.8-omni-flash` 不在白名单里，于是"让 LangChain 自己选"实际选中的是 `ToolStrategy`——照样 400。

**结论：直接传 schema 并不等于"自动选对"，它只认识 LangChain 内置的那份名单。** 用国产模型时，显式写 `ProviderStrategy` 或 `ToolStrategy` 反而更可控。

---

## 4. 踩坑实录：400 是怎么来的

完整链路：

```text
create_agent(response_format=ToolStrategy(ContactInfo))
  → factory.py: tool_choice = "any"
  → langchain_openai: "any" → "required"
  → HTTP 请求: tool_choice = "required"
  → 服务端（思考模式）: 400 The tool_choice parameter does not support
                        being set to required or object in thinking mode
```

触发条件只有一条：**`LLM_ENABLE_THINKING=true`（或不设置，服务端默认开思考）**。

两个容易看错方向的细节，都是实测出来的：

### 细节 1：报错的只有 `required`，指定函数名是"静默失败"

| 请求的 `tool_choice` | 思考模式下表现 |
|---|---|
| `"auto"` | 正常，模型按需调工具 |
| `"required"` | **400**（就是本文的报错） |
| `{"type":"function","function":{"name":"ContactInfo"}}` | 不报错，但返回里没有 `tool_calls` |

如果只试了函数名那种写法，会看到"模型不调用工具"，很容易误判成提示词问题或模型能力问题，其实是服务端把强制项悄悄忽略了。

### 细节 2：`required` 是"每次请求"都带，不是只在最后一轮

`tool_choice` 是单次 HTTP 请求的参数，不存在"全局开启"的状态。但在 `ToolStrategy` 配置的 agent 里，**每一轮模型调用**都会重新绑定 `required`，包括 `ask_user` 追问的那些轮次。

这带来两个推论：

1. **多轮追问仍然可用**——`required` 只要求"调某个工具"，`tools` 里还有 `ask_user`，模型在信息不全时可以选 `ask_user`；
2. **但模型不能纯文本回复**——每一轮都必须调用某个工具。如果你希望中间某轮只说一句话，这个配置做不到。

（另一个角度：`required` 并不是"第一轮就强制输出 `ContactInfo`"。具体调哪个工具由模型决定，只是必须调一个。）

---

## 5. 三种方式横向对比

| 维度 | ToolStrategy | ProviderStrategy | 直接传 schema |
|---|---|---|---|
| 本质 | 伪造工具 + 强制 tool_choice | 服务端按 json_schema 解码 | 自动探测 |
| 关键请求参数 | `tool_choice: "required"` | `response_format: {json_schema}` | 取决于探测结果 |
| 对服务端的要求 | 支持 function calling 且允许强制 | 支持 json_schema | 两者之一 |
| 能否与 ask_user 等多轮工具共存 | 能（required 下模型自选） | 能（若服务商支持 tools + structured 并存） | 看探测结果 |
| 校验失败重试 | 内置 `handle_errors` | 由客户端解析异常，重试逻辑需自己兜 | 同所选策略 |
| 思考模式兼容性（本 endpoint） | **400** | **正常** | **400**（回落 ToolStrategy） |
| 可控性 | 高 | 高 | 低（依赖内置名单） |

---

## 6. 本仓库怎么选

| 目标 | 选择 |
|---|---|
| 学结构化输出 + 保留思维链 | `ProviderStrategy(ContactInfo)`（本 endpoint 已实测可用） |
| 学函数调用机制本身 | `ToolStrategy`，同时把 `LLM_ENABLE_THINKING=false` |
| 换到只有函数调用能力的服务商 | `ToolStrategy` + 关思考 |
| 换到 OpenAI 官方模型 | 直接传 `ContactInfo` 也可以，白名单认得 |

注意 `agent` 和 `contact_agent` 共用同一份 `.env`，`LLM_ENABLE_THINKING` 是全局开关：关掉思考能救 `ToolStrategy`，但 `main.py` 的 `[思考]` 输出也会一起消失。

---

## 7. 验证记录

| 实验 | 配置 | 结果 |
|---|---|---|
| `tool_choice="auto"` | thinking=true | 正常返回 `tool_calls` |
| `tool_choice="required"` | thinking=true | 400（本文报错） |
| `tool_choice=<函数名对象>` | thinking=true | 200，但 `tool_calls` 为空 |
| `ToolStrategy` + contact_agent | thinking=true | 400 |
| `ToolStrategy` + contact_agent | thinking=false | 返回 `ContactInfo(name='张三', ...)` |
| `ProviderStrategy` + contact_agent | thinking=true | 返回 `ContactInfo(name='张三', ...)` |
| `_supports_provider_strategy(model)` | qwen3.8-omni-flash | `False` |

未验证：`ProviderStrategy` 在"缺字段需要多轮 ask_user 追问"时的完整表现；不同服务商对 `json_schema` 的兼容差异。
