# 本机启动与使用

这个项目可以完全在你的电脑上运行，不需要购买或部署服务器。本地网页地址为
http://127.0.0.1:3000，后端地址为 http://127.0.0.1:8000。

## 这台电脑如何启动

项目目录：`D:\GitHubProjects\AutoResearch-Agent`。依赖已安装，无需每次重新安装。
打开两个 PowerShell 终端，并保持它们运行。

第一个终端启动后端：

```powershell
Set-Location D:\GitHubProjects\AutoResearch-Agent
$env:AUTORESEARCH_DEPLOYMENT='0'
$env:AUTORESEARCH_STORAGE='json'
$env:PYTHON_DOTENV_DISABLED='1'
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

第二个终端启动网页：

```powershell
Set-Location D:\GitHubProjects\AutoResearch-Agent\frontend
$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8000'
npm run dev -- --hostname 127.0.0.1 --port 3000
```

打开 http://127.0.0.1:3000。看到 `Local workspace · Saved on this computer` 和 **Literature workbench**
即可使用。默认本地模式自动连接，不显示令牌输入框。
停止时在两个终端分别按 `Ctrl+C`。关闭服务不会删除已保存记录。
如果端口已被占用，先打开网页检查是否已经启动，不要重复启动第二份服务。

上述配置不加载项目 `.env` 中的模型配置。普通检索、PDF 分析、引用、统计和文稿编辑
不需要 API key；不要勾选模型发送选项或点击模型审查按钮，即不会启动付费模型审查。
检索和下载论文需要联网，本地 PDF、已保存记录及统计可以离线使用。

## 推荐的操作顺序

1. **文献库 Library**：在 **Research topic** 输入研究主题，
   点击 **Find papers**。例如 `id:1706.03762` 可检索《Attention Is All You Need》。
2. **选择并分析**：勾选需要的论文，再点 **Analyze selected papers**。检索本身不会分析
   所有候选论文。也可以通过 **PDF file → Add PDF** 上传自己的文字型 PDF。
3. **阅读与证据 Reading & evidence**：选择论文、搜索摘录或筛选类别；点选摘录，旁边显示
   引文和所在页的完整提取文本。高级审核按需展开。**Literal source checks passed** 只表示原文引用核对，不是科研结论认证。
4. **保存与重开**：记录自动保存，左侧 **Your research** 可以重开；带 `?run=` 的链接也可以收藏。
   **New record** 开始另一个记录。搜索会创建新记录。
5. **比较 Compare**：查看各篇论文的证据矩阵；**Read evidence** 跳回原文。需要导入自己的实验数据时，
   展开 **Optional: your experimental observations**，在 **User experiment observations** 选择 JSON 或 CSV。
   CSV 需要明确填写数据标题、列名和单位；使用 **Import observations** 导入，再点
   **Load data checks and statistics** 查看描述统计及样本引用。缺失值保持缺失，不会生成实验结果。
6. **写作 Writing**：点 **Preview chapter draft** 查看草稿；在 **Manuscript editor**
   填写 **Revision reason**，点 **Initialize from current preview** 初始化。章节与引用选项按需展开。
   编辑后填写原因并 **Save manuscript revision**。缺少的实验材料会保留占位，事实句需要引用依据。
7. **导出**：文献库展开 **Library tools: references, duplicates and screening**，通过 **Load citation JSON / Load BibTeX** 查看和下载引文。完整文稿需要你检查
   当前版本，展开 **Review and export**，在 **Human approval** 填写审阅信息并明确批准，之后点 **Download approved manuscript**。
   这个导出批准是对当前文稿的操作，不会把项目的人工科学评测标记为通过。

旧版界面移至 `/legacy`，本地主入口只显示四区工作台。

## 先体验完整案例

```powershell
.\.venv\Scripts\python.exe examples/conformal-prediction/reproduce.py --install
```

从项目根目录执行后，打开输出的链接，或刷新 **Your research**。这会安装三篇开放许可论文的
研究记录副本，无需下载或模型密钥。依次体验文献库、阅读、比较、写作。
[案例说明、原始输出与错误记录](../examples/conformal-prediction/README.md)保留了真实遗漏和误分类，
不会把引文核对通过当成科学验证。

## 数据在哪里

默认 JSON 模式把记录保存在项目的 `data/research_runs/`，文稿修订也由该存储目录管理。
这些数据不上传到 GitHub。备份时先停止后端，再复制整个目录。

P5 后台任务也可以在本机使用，不需要服务器。若需要，停止后端后改为：

```powershell
$env:AUTORESEARCH_STORAGE='sqlite'
$env:AUTORESEARCH_DATA_ROOT='D:\GitHubProjects\AutoResearch-Agent\data\deployment'
```

然后用原后端命令启动。网页会显示 **Queue search / Queue analysis** 和任务列表，支持取消、
重试及显式打开结果。此模式的数据在 `data/deployment/users/local/`；不会自动显示旧 JSON
记录。已有数据可按 [迁移说明](p5-deployment.md) 显式导入。保持 `AUTORESEARCH_DEPLOYMENT=0`，
本机使用不需要配置用户令牌。

## 已验证的实际流程（2026-10-21）

- 本机浏览器通过正式 API 检索、选择、下载并分析《Attention Is All You Need》明确版本
  `1706.03762v7`：15 页、23 条原文证据和 23 条关联结论，保存和刷新重开通过。
- 独立临时记录用两篇明确标注的合成论文，验证检索、分析、CSV 导入、原始文件下载、
  描述统计、样本引用、文稿编辑/历史/保存、演示批准和 Markdown 下载。
- 检查新修订使旧批准失效、手机宽度无横向溢出、无浏览器运行错误。
- 演示批准只存在于临时测试记录；没有批准真实论文文稿，没有运行付费模型，
  人工科学评测仍未评测。测试演示数据不混入默认研究记录。
