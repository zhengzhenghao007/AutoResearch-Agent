# 第一阶段验证记录

日期：2026-09-17。环境：Windows，项目现有 Python 3.12 虚拟环境。验证针对本地单用户文献/PDF MVP，不代表生产部署或科学结论正确。

最终离线回归：**44 passed，1 条依赖弃用提示，7.71 秒**。

## 自动验证

- 离线 pytest：真实生成 PDF 的页码、截断、空白/错误文件；假网络返回、重定向拒绝和大小上限；解析进程超时。
- Evidence：精确引文、页码和来源；缺失字段分区；缺失实验不补齐；LLM 伪造引文被拒绝；两篇论文保留独立引用。
- Store：JSON 往返、未知版本拒绝、原子替换失败保留旧文件；篡改引文、引用、review、selection、生成建议来源均被拒绝。
- API/CLI：真实 service + 临时 store 的上传/读取；旧 `/api/papers` 响应契约；CLI 子进程 import/show。只有网络和 LLM 使用 fake。
- 四个旧在线 provider 演示从默认收集隔离；未作为“通过的单元测试”计数。
- `compileall` 及 `git diff --check` 通过。Git 的 Windows 换行提示不表示差异校验失败。

命令：`python -m pytest tests -q -p no:cacheprovider --basetemp <全新临时目录>`。本机 pytest 默认临时目录出现沙箱 ACL 拒绝，使用获授权的离线执行和独立临时目录完成测试。

## 真实网络 smoke

对 `vision-language robot navigation` 搜索得到 2 篇 arXiv 候选；显式选择其中 1 篇，成功下载、解析并提取 66 条原文 claim，字面来源校验通过。测试记录保存于独立临时目录，不是用户正式研究记录。未调用真实收费 LLM，未将字面校验解释为科学真实性证明。

## ChatGPT 协作审查

复用既有 AutoResearch-Agent 对话，ChatGPT 直接读取工作区和发布的测试输出。

1. 第一轮：修复 missing_fields 一致性、生成类型规则、本地路径泄露；引入 PDF 子进程和超时。
2. 第二轮：补充跨对象存储校验、结构化 suggestion Claim、父子解析器大小限制一致性。
3. 最终轮：ChatGPT 返回 `STATE: DONE`，确认本地单用户文献/PDF MVP 无阻塞项。审查读取了 41 项测试的记录及随后上传保留修复；最终本地回归扩展到 44 项通过。

## 已知限制

来源校验只检查保存的页面文字与引用，不是语义蕴含评估或防篡改签名。规则分类需要人工复核，可能漏提/误分。真实 LLM provider 路径仅以 fake 结构化响应测试。现有 FastAPI/Starlette 测试环境有一条 httpx 弃用提示，测试仍通过。

用户实验数据导入、自动 hypothesis、OCR、全文写作、前端证据界面、并发事务和公共服务安全隔离属于后续阶段。未修改用户原有 frontend 或 requirements-dev.txt，未提交或推送 Git。
