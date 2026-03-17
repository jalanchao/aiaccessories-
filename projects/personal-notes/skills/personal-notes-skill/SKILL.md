---
name: my-notes
description: 个人 Obsidian 笔记助手，专为个人 vault 定制的上层封装 skill。自动路由内容到正确工作流：技术文章/研报 → PARA 总结沉淀（7步流程）；arXiv 论文 → Paper 精细归档（L1-L5分级）；投资观察/研报 → Finance 记录（月度日记或专题）；快速想法/todo → Personal 日志；个人健康 → Personal 日志。具备自组织能力，每次操作后更新 vault 内 vault-guide.md 积累知识，随 vault 同步到所有设备。触发场景：保存文章、总结内容、归档论文、记录投资观察、快速捕获想法、整理 vault、询问笔记应该放在哪里。
---

# My Notes

## 启动协议

每次使用时，**必须先执行**：

1. 运行 `date '+%Y-%m-%d %H:%M'` 获取当前日期和时间，作为后续所有时间推断的基准
2. 读取 skill 目录下的 `config.json`，获取 `vault_root` 和 `vault_guide`
3. 读取 `{vault_root}/{vault_guide}`（即 vault-guide.md），加载当前方法论和模块规范
4. 基于用户输入内容路由到对应工作流

> 若 vault-guide.md 不存在，执行末尾的**初始化流程**。

---

## 内容路由

| 输入信号 | 工作流 |
|---------|--------|
| arxiv URL / arXiv ID / 学术论文 | → Paper 工作流 |
| 金融研报 / 市场分析 / 会议纪要 / 机构观点 / 投资记录 | → Finance 工作流 |
| 技术文章 / 博客 / 普通文章 / 视频字幕 / 非结构化文本 | → PARA 总结工作流 |
| 快速想法 / todo / 草稿 | → Personal 工作流 |
| 待读链接 | → TEMP 工作流 |
| 个人健康 / 锻炼 / 饮食 / 生活记录 | → Personal 工作流 |
| 内容模糊 / 多类型 | → 展示判断理由，请用户确认 |

路由后，从 vault-guide.md 对应模块方法节读取具体执行规则。

---

## 工作流执行

### PARA 总结工作流
按 vault-guide.md 中「PARA 模块」的 7 步流程执行：
1. 若输入是 URL，先用 `obsidian:defuddle` 提取内容
2. 若含字幕/非结构化文本，先按「raw_text_formater 流程」处理
3. 依次完成元信息、摘要、关注模块、摘录、适用/风险
4. **第6步：生成分类和路径建议，停下来请用户确认，不得跳过**
5. 确认后：`obsidian create` 创建文件，追加更新 `PARA/index.md`

### Finance 工作流
从 vault-guide.md「Finance 模块」读取规则后：
- 时效性观察/记录 → 追加到当月 `Finance/stock/YYYY-M.md`
- 深度研究/机构研报 → 在 `PARA/Resources/金融/` 下按规则新建文件
- **严格依据原文，不允许推断，不允许添加原文未提及的内容**

### Paper 工作流
从 vault-guide.md「Paper 模块」读取规则后：
1. 提取 arXiv ID（格式：`YYMM.NNNNN`）
2. **先确认：L 级别（L1-L5）和领域分类**
3. 生成完整 frontmatter + 结构化正文
4. 创建文件：`Paper/{领域}/{年}/{月}/{arxiv_id}v{N} - {title_slug}.md`
5. 更新 `Paper/_Index/Level-{N}.md`

### TEMP 工作流
快速执行，无需确认：
- 追加到 `TEMP/see_this.md`，或按内容性质新建 TEMP 下文件
- 格式：`\n## YYYY-MM-DD HH:MM\n{内容}`

### Personal 工作流
追加到对应文件（锻炼计划、体重饮食记录等），无需确认。

**Todo 格式规则：**
- 无时间要求：`- [ ] {内容}`
- 有时间要求：使用 Reminder 插件格式 `- [ ] {内容} (@YYYY-MM-DD HH:MM)`

**时间推断：** 用户说"今晚20点"/"明天早上"等相对时间，结合步骤1查询到的当前时间转换为绝对时间写入。

**Todo 统一追加到** `Personal/todo.md`，格式：
```
\n## YYYY-MM-DD\n- [ ] ...
```
同日期下有多条时合并在同一 `## YYYY-MM-DD` 节下，不重复创建标题。

**时间排序规则：** 同一日期节内，有 `(@时间)` 的条目按时间升序排列，无时间的条目排在有时间的条目之后。追加新 todo 时，读取现有内容，按此规则插入到正确位置，而非简单追加到末尾。

---

## 自更新协议

**每次操作完成后**，检查以下条件，满足则更新 vault-guide.md：

| 条件 | 操作 |
|------|------|
| 新建了目录 | 更新 vault-guide.md「结构快照 → 当前目录树」 |
| 遇到模糊情况，已经用户确认 | 将决策追加到对应模块的「先例记录」小节 |
| 用户修改了命名/分类约定 | 更新对应模块方法节的规则 |

更新时，同步更新文件头部注释中的日期：
```
<!-- 最后更新：YYYY-MM-DD -->
```

---

## 初始化流程

**当 vault-guide.md 不存在时执行：**

1. 用 obsidian-cli 列出 vault 目录结构
2. 基于扫描结果填充「结构快照」节
3. 其余内容使用内置模板
4. 展示草稿，请用户确认后写入 `{vault_root}/PARA/vault-guide.md`

---

## obsidian-cli 常用命令速查

```bash
# 读取文件（支持 path= 精确路径）
obsidian read path="PARA/index.md"

# 创建文件（silent 不打开，overwrite 覆盖）
obsidian create name="标题" content="内容" path="PARA/Resources/.../文件名.md" silent

# 追加内容
obsidian append path="Finance/stock/2026-3.md" content="\n## 2026-03-06\n内容"

# 搜索
obsidian search query="关键词" limit=10

# 读取日记
obsidian daily:read
obsidian daily:append content="- [ ] 任务"
```

底层依赖：`obsidian:obsidian-cli`、`obsidian:obsidian-markdown`、`obsidian:defuddle`

---

## CLI 可用性与 Fallback

<!-- Evolution: 2026-03-13 | source: ep-2026-03-13-001 | pattern: date_query_before_todo + time_ordered_todos -->
<!-- 问题：启动协议未显式查询当前时间，依赖系统context；todo无时间排序规则 -->
<!-- 修复：启动协议步骤1改为运行date命令；Personal工作流增加时间升序排列规则 -->

<!-- Evolution: 2026-03-10 | source: ep-2026-03-10-001 | pattern: cli_availability_check_before_use -->

**obsidian CLI 不一定已安装。** 使用前必须验证：

```bash
which obsidian   # 若无输出，则 CLI 不可用
```

### Fallback 策略（CLI 不可用时）

| 操作 | obsidian CLI | Fallback |
|------|-------------|---------|
| 读取文件 | `obsidian read path="..."` | `Read` 工具，路径 `{vault_root}/...` |
| 创建文件 | `obsidian create ...` | `Write` 工具 |
| 追加内容 | `obsidian append ...` | `Read` → `Edit` 工具 |
| 搜索 | `obsidian search ...` | `Grep` 工具，在 `{vault_root}` 下搜索 |

> **重要**：skill 缓存目录（`.claude/plugins/cache/...`）只存放 skill 文档，**不含** CLI 二进制。不要从 skill 路径推断工具安装位置。有 `vault_root` 时，直接文件操作同样可靠，优先考虑 fallback 而非猜测路径。
