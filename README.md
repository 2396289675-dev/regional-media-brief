# 区域媒体情况简报生成器

给区域媒体拜访做摸底用的一句话→成品工具：你说「帮我写浙江媒体情况简报」，它联网调研后直接产出一份可带去拜访的 Word，以及一份可嵌入网站的单文件网页。

初版版式与结构逆向自一份真实的省级媒体简报（陕西），写作颗粒度以该稿为标杆。

## 它产出什么

| 产物 | 命令 | 依赖 | 用途 |
| --- | --- | --- | --- |
| `.docx` | `python3 scripts/build_docx.py` | `python-docx` | 打印、带去拜访、走内部流程 |
| `.html` | `python3 scripts/build_html.py` | 无（纯标准库） | 单文件、零外部请求，可直接 `<iframe>` 嵌进站点或内网页面 |

两份产物同源：同一份 markdown 中间稿，两种渲染。

## 目录结构

```
regional-media-brief/
├── SKILL.md                     技能定义（给 AI 读的：工作流、硬约束、章节骨架）
├── README.md                    本文件（给人读的）
├── install.sh                   一键安装到 ~/.workbuddy/skills/
├── requirements.txt             python-docx（仅 docx 渲染需要）
├── scripts/
│   ├── build_docx.py            markdown -> Word（黑体标题 / 宋体正文 / Table Grid / 页脚页码）
│   └── build_html.py            markdown -> 单文件 HTML（响应式 / sticky 目录 / 打印样式）
├── references/
│   ├── format-spec.md           版式规范与 markdown 标记语法
│   ├── research-checklist.md    调研字段清单与推荐信源（搜什么、去哪搜）
│   └── sample-shanxi.md         陕西简报全文——写作颗粒度与语气的标杆
├── assets/
│   └── 版式样张-陕西.docx        版式还原验证样张
└── examples/
    └── 黑龙江-示例成品.md         真实跑出来的成稿样例
```

## 安装

```bash
cd regional-media-brief
./install.sh
```

装到 `~/.workbuddy/skills/regional-media-brief/`，随后在对话里直接说区域名即可。
已存在同名目录时，旧版本会移到 `/tmp/` 备份（不会留在 skills 目录下造成重复技能）。

## 手动使用（不装技能也能跑）

```bash
# 1. 写 markdown 中间稿（结构照 references/sample-shanxi.md）
# 2. 渲染
python3 scripts/build_docx.py brief.md "~/Downloads/浙江媒体情况简报.docx"
python3 scripts/build_html.py brief.md "~/Desktop/浙江媒体情况简报.html"
```

### markdown 语法子集

渲染器只认这几种，别用别的：

| 写法 | 效果 |
| --- | --- |
| `# 标题` | 封面大标题（全篇一次） |
| `## 标题` / `### 标题` | 二级 / 三级章节（自动生成目录与锚点） |
| `**加粗**` | 段首标签如 `**定位：**` 会被渲染成独立小标 |
| `==红色加粗==` | 现场重点句，全篇控制在 3 处以内 |
| `1. …` | 有序列表 |
| `\| a \| b \|` 连续行 | 表格，首行为表头 |

## 依赖

- Python 3.8+（脚本只用标准库；docx 渲染另需 `python-docx`）
- 无网络依赖、无 API key、不读无关文件
- `build_html.py` 在 macOS / Linux / Windows 上均可运行，产出文件不引任何 CDN

## 硬约束

1. 事实必须可核实、带来源；搜不到就写「待核实」，**不编造领导姓名、财务数字、奖项等级**。
2. 不写推理过程与风险论证长文，语气是成稿。
3. 每篇必须写「腾讯可谈的切入点」，要具体到产品与项目。
4. 涉及政府/官方数据的叙事保持正向建设口径。

## 已知限制

- 渲染器只处理上表列出的语法，复杂 markdown（嵌套列表、代码块、图片）会被当纯文本。
- 中文字体（黑体/宋体）在 Linux 服务器上渲染 docx 时可能缺字，需装中文字体包。
- 调研依赖联网搜索；同一区域一年内最好重跑一次，领导任职与经营数据会变。
