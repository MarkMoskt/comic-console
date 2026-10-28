# 接口契约

本文件是 Cola 对外接口的完整约定。**本仓库只提供契约，不提供实现**：

- `GET /` 与 `GET /api/status` 返回 200，用于展示结构；
- 其余所有接口在契约桩中一律返回 `501 Not Implemented`，语义见 §1.4；
- 字段名可以按你的系统调整，**语义与边界**建议保持一致。

## 1. 通用约定

### 1.1 传输

- 编码：UTF-8；请求与响应均为 `application/json`（首页为 `text/html`）。
- 路径：所有接口以 `/api/` 开头；末尾斜杠可省略。
- 方法：只读用 `GET`，写入用 `POST`；未定义的方法返回 `405`。

### 1.2 会话

控制台不设密码。登录走**已有的即时通讯信道**：

1. 页面选择身份，`POST /api/login/request`；
2. 对应的机器人通过微信给主人发一个一次性确认码；
3. 主人在微信里回「同意」或直接回码；
4. 页面轮询 `GET /api/login/poll`，通过后服务端种一枚有时效的签名 Cookie；
5. 之后所有 `/api/*`（登录流除外）都要求有效 Cookie，否则 `401`。

约束：确认码有效期 5 分钟；同一身份 60 秒内最多发起 3 次；`rid` 一次性；只扫最近的信道日志，不回溯历史。

### 1.3 错误信封

```json
{ "error": "unauthorized", "message": "登录已过期", "endpoint": "/api/status" }
```

常用 `error`：`unauthorized`（401）、`forbidden`（403）、`not_found`（404）、
`method_not_allowed`（405）、`bad_request`（400）、`rate_limited`（429）。

### 1.4 `501` 的语义

```json
{ "error": "not_implemented", "endpoint": "/api/diary", "docs": "docs/API.md",
  "message": "接口约定已公开，实现请自行完成。" }
```

`501` 不是故障，是契约桩的默认回答：**接口存在、字段已知、实现不在本仓库**。
你实现某个接口后，它应当返回 200 与本文档描述的结构，而不是 501。

## 2. 认证

### `POST /api/login/request`

请求：

```json
{ "identity": "owner-a" }
```

响应 `200`：

```json
{ "rid": "c0a8f3e2", "expires_in": 300, "channel": "channel-a" }
```

`identity` 只能是配置里声明的身份之一（见 `config.example.json` 的 `agents[].owner`）。

### `GET /api/login/poll?rid=<rid>`

响应 `200`：

```json
{ "status": "pending" }
```

`status` ∈ `pending` / `approved` / `denied` / `expired`。`approved` 时响应同时带 `Set-Cookie`。

### `POST /api/login/logout`

响应 `200`：`{ "ok": true }`，并清除 Cookie。

## 3. 状态与只读接口

### `GET /api/status`

```json
{
  "name": "Cola",
  "series": "Comic",
  "version": "contract-only",
  "service": "stub",
  "implemented": false,
  "uptime_s": 12,
  "rss_mb": 0,
  "channels": [
    { "id": "channel-a", "name": "Assistant A", "peer": "Owner A",
      "messages": 0, "today_messages": 0, "last_seen": "" }
  ],
  "counts": {
    "messages": 0,
    "facts": 0,
    "memory_blocks": 0,
    "diary_entries": 0,
    "stickers": 0
  },
  "diary": { "a": 0, "b": 0, "total": 0, "latest": "" }
}
```

语义：

| 字段 | 含义 |
| --- | --- |
| `channels[].messages` | 该通道累计消息数 |
| `channels[].last_seen` | 该通道最后一次活动时间（ISO 8601，未知为空串） |
| `counts.facts` | 从对话中抽取的事实条数 |
| `counts.memory_blocks` | 向量知识库的分块数（每次文档变更后重算） |
| `counts.diary_entries` | 日记总篇数 |
| `diary.latest` | 最近一篇日记的日期 |

`implemented: false` 表示当前是契约桩；真实实现应当返回 `true`，并给出真实计数。
控制台首页的「知识库块数」应当直接取 `counts.memory_blocks`，**不要在前端写死**。

### `GET /api/diary?who=<agent>&date=<YYYY-MM-DD>`

`date` 缺省取最新一篇。响应：

```json
{
  "who": "a", "date": "2026-10-28", "title": "今天的小事",
  "body": "……", "score": 0.72, "band": "平稳", "words": 860
}
```

### `GET /api/diary/list?who=<agent>`

```json
{ "who": "a", "dates": ["2026-10-28", "2026-10-27"] }
```

### `GET /api/diary/calendar?month=<YYYY-MM>`

```json
{ "month": "2026-10", "days": [
  { "date": "2026-10-28", "who": "a", "band": "平稳", "score": 0.72, "words": 860 }
] }
```

### `GET /api/emotion/history?days=14`

```json
{ "days": [
    { "date": "2026-10-28", "a": 0.72, "b": 0.61, "messages": 42 }
  ],
  "triggers": { "a": ["散步", "新店"], "b": ["加班"] } }
```

`score` 为 0–1，`band` 为离散档位（示例：低落 / 平稳 / 愉快）。

### `GET /api/events?limit=15`

```json
{ "events": [ { "ts": "2026-10-28T18:00:00+08:00", "level": "info", "text": "服务已启动" } ] }
```

### `GET /api/traffic?days=7`

```json
{ "days": [ { "date": "2026-10-28", "in": 120, "out": 340, "brain": 300, "usage": 12000 } ] }
```

`in` / `out` 为微信收发条数，`brain` 为触发大脑的轮次，`usage` 为 token 用量（没有就填 0）。

### `GET /api/memory?q=<query>`

不带 `q` 时只回概览；带 `q` 时附检索命中。

```json
{
  "overview": { "messages": 12800, "facts": 240, "memory_blocks": 175, "decay_days": 30 },
  "hits": {
    "facts": [ { "text": "主人 A 喜欢周末散步", "score": 0.83, "ts": "2026-10-20" } ],
    "kb": [ { "text": "……", "source": "handbook.docx", "score": 0.79 } ]
  }
}
```

### `GET /api/chatlog/list?who=<agent>` · `GET /api/chatlog?who=<agent>&date=<YYYY-MM-DD>`

```json
{ "who": "a", "date": "2026-10-28",
  "lines": [ { "ts": "2026-10-28T09:12:00+08:00", "role": "user", "text": "早" } ] }
```

`role` ∈ `user` / `assistant` / `system`。只读，不允许通过接口写入。

## 4. 对话

### `POST /api/chat`

```json
{ "who": "a", "text": "今天有点累", "clear": false }
```

响应：

```json
{ "reply": "那就早点睡，我把灯留一盏。", "bubbles": ["那就早点睡，", "我把灯留一盏。"], "model": "your-model" }
```

- `bubbles` 是按句切分后的多条消息，一条气泡一句；不想切分就回单元素数组；
- `clear: true` 只清空**当前登录身份 × 当前 agent** 的上下文，不动另一个人的；
- 上下文按「agent × 登录身份」分键，两个身份互不可见。

### `POST /api/repair`

```json
{ "who": "a", "action": "reload-context" }
```

响应：`{ "ok": true, "actions": ["reload-context"] }`。
仅限主人身份调用，用于修掉某一路会话的坏状态；不允许触碰另一个身份的数据。

## 5. Agent 工具契约

以下是**大脑可调用的工具**（进程内，不是 HTTP 接口）。名字与参数是约定，实现自便。

| 工具 | 参数 | 行为边界 |
| --- | --- | --- |
| `web_search` | `query`, `limit?` | 只返回标题、链接、摘要；不抓全文 |
| `web_fetch` | `url` | 轻量抓取，直取正文；只去公网 `http(s)`；超时即失败，不重试 |
| `browser` | `action`, `url?`, `selector?`, `text?` | 见下方细则 |
| `memory_add` | `text`, `scope?` | 写入事实层；同一事实不重复堆积 |
| `memory_search` | `query`, `limit?` | 事实层 + 向量库联合召回，按相关度与时效排序 |
| `diary_write` | `date`, `body` | 一天一篇；重复写入视为修订，不生成第二篇 |
| `diary_read` | `date?` | 读某天或最近一篇 |
| `schedule_add` | `when`, `text` | 一次性提醒；时间必须可解析，否则拒绝而不是猜 |
| `schedule_list` / `schedule_cancel` | — / `id` | 只允许查看与撤销自己的提醒 |
| `send_file` / `receive_file` | `path` / `name` | 文件桥；只允许配置白名单目录，禁止穿越 |
| `sticker` | `category` | 从类别随机取一张；没有合适类别就不发 |

### `browser` 细则

`action` ∈ `navigate` · `snapshot` · `click` · `fill` · `press` · `back` · `forward` · `select` · `close`。

约定（**这是边界，不是建议**）：

1. **只去公网。** 只放行 `http` / `https` 的公网地址；本机、内网、链路本地、云元数据地址、
   `file:` / `data:` / `javascript:` 一律拒绝。点按、回车、前进后退之后，必须按**落地地址**再判一次——
   重定向和页面里的链接同样可能把你带进内网。
2. **一次一个。** 同一时刻只允许一个网页动作；拿不到就立刻回「正忙」，不要排队硬等。
3. **有预算。** 开页面前看内存余量与动作时长上限，不够就如实回「暂不可用」，让大脑改用轻量抓取。
4. **先快照再点按。** 点或填之前先取最新快照拿元素编号；拿旧编号去点只会白等一次超时。
5. **失败要说话。** 拒绝与超时都要返回明确原因，不要静默重试——重试会把一次失败放大成一片泛洪。

## 6. 版本与兼容

- 契约只做**增量**变更：加字段、加可选参数；不删字段、不改语义。
- 破坏性变更必须换路径（例如 `/api/v2/...`），旧路径保留一个版本周期。
- 本仓库的契约对应线上 Comic v2.5.2；`Comic` 是版本系列，`Cola` 是项目名。

## 7. 实现清单

- [ ] 一个进程内可用的会话存储（按 agent × 身份分键）
- [ ] 登录流：一次性码、5 分钟过期、60 秒 3 次限流、签名 Cookie
- [ ] 状态与只读接口（先做 `/api/status`，前端所有数字都从它来）
- [ ] 事实层与向量库（写入去重、检索衰减）
- [ ] 日记生成与情绪打分（一天一篇、可修订、可回看）
- [ ] 对话接口（多句切分、上下文隔离、清空只清自己那份）
- [ ] 工具层（抓取 / 浏览器 / 提醒 / 文件 / 表情）
- [ ] 浏览器闸门（公网判定、单任务、内存与时长预算、落地地址复核）
- [ ] 控制台页面（状态、记忆、日记、情绪、事件、谱系）
