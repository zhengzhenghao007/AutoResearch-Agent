# 扫描 PDF 导入

Library 的 Add PDF 先提取文字层；没有文字但包含图片的页面会自动使用本地 RapidOCR 识别。中文/英文识别模型随依赖安装，识别过程不联网、不调用付费模型、不改动原始 PDF。

正常安装 `requirements.txt` 已包含 OCR。升级已有安装时，在项目目录运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

随后重启 API。若使用只在首次运行安装依赖的旧启动器，也需要执行上述升级步骤。缺少依赖时页面会给出安装提示。

## 处理范围

- 输入最多 20 MiB，默认解析前 50 页；页码保留原 PDF 页码。
- 一次最多识别 20 个无文字的图片页。较长扫描件需先拆分；普通空白页不触发 OCR。
- OCR 子进程最长 10 分钟；上传客户端最多等待 12 分钟，以覆盖原生解析与保存。密集论文可能需要数分钟，请保持页面打开。超时不会自动重试。
- 渲染最长边不超过 2000 像素；原生文字与 OCR 合计不超过一百万字符。Linux OCR 子进程限制 2 GiB 地址空间、540 秒 CPU、64 个文件描述符。Windows 保留进程超时和输入/像素/输出限制，没有等价 OS 内存配额。
- 加密文档仍拒绝；空白或无法识别的文档不生成虚构文本。混合文档保留文字层，仅对图片页补充识别。

## 如何核对

资料卡显示 OCR 页数，Reading 的对应页面显示识别警告。保存的 `document.ocr_pages` 记录识别页码，文本仍按页绑定证据。未使用 OCR 的旧记录不增加序列化字段，以保留已有哈希。

OCR 可能损坏公式、表格、空格、多栏顺序和专有名词。来源校验只能证明引文存在于**识别后的页面文字**，不证明与原始像素逐字一致，更不等于科学结论通过。引用前请打开原 PDF 对照。仅有矢量轮廓且无文字层/图像对象的特殊 PDF 暂不自动 OCR。

实现采用 [RapidOCR 1.x](https://rapidai.github.io/RapidOCRDocs/v1.4.4/install_usage/api/RapidOCR/) 的随包模型及 [pypdfium2](https://pypdfium2.readthedocs.io/en/stable/python_api.html) 页面渲染。
