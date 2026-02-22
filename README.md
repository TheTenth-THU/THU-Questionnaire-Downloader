# THU-Questionnaire-Downloader

**THU-Questionnaire-Downloader** 是一个专为[清华大学调查问卷系统 (https://wenjuan.tsinghua.edu.cn)](https://wenjuan.tsinghua.edu.cn) 设计的自动化数据采集工具。它能够自动登录、抓取问卷数据，并智能下载包括图片和清华云盘视频在内的多媒体附件，最终生成包含完整信息的 Markdown 和 PDF 汇总报告，极大地简化了多媒体问卷数据的整理工作。

## 主要功能 Fᴇᴀᴛᴜʀᴇs

核心功能涵盖了从数据获取到报告生成的全流程：
-   **自动交互**：利用 `DrissionPage` 自动完成问卷网的登录与密码验证，支持按日期范围筛选数据。
-   **媒体下载**：不仅能保存普通的文本回答，还能自动识别并下载问卷中的图片附件，以及调用 [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader) 下载存储在清华云盘的视频文件。
-   **报告生成**：自动生成结构化的 `booking_info.md` 汇总文件，嵌入本地文件链接，借助 Pandoc 自动导出 PDF 版本。

**`thu_questionnaire_downloader.py` 中的程序流程和报告结构仅作为示例，请注意结合问卷查询页面的实际结构进行调整。**

## 文件结构 Fɪʟᴇ Sᴛʀᴜᴄᴛᴜʀᴇ

项目保持了扁平简洁的文件结构：
-   `main.py`: **入口脚本**。负责读取配置、调度下载任务、生成最终报告。
-   `thu_questionnaire_downloader.py`: **核心逻辑**。包含爬虫实现、数据解析、资源下载及 Markdown 生成逻辑。
-   `config.json`: **配置文件**。存储用户凭证、目标问卷信息及路径设置。
-   `output/`: **默认输出目录**。包含生成的 `booking_info.md`、PDF 报告以及按条目分类的资源子文件夹。

## 使用方法 Usᴀɢᴇ

### 安装 Iɴsᴛᴀʟʟᴀᴛɪᴏɴ

开发在 Python 3.12.9 环境中完成，据 AI 分析理论上 Python 3.8+ 都能兼容，但建议使用最新版本以获得最佳性能和兼容性。

1.  克隆仓库并进入目录。
2.  安装依赖：
    ```bash
    pip install DrissionPage rich pypandoc requests
    ```
3.  准备外部工具 [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader) 用于视频下载。

若需 PDF 生成，还需安装 [Pandoc](https://pandoc.org/installing.html)。未安装 Pandoc 将导致 PDF 转换失败，但 Markdown 文件仍会正常生成。

### 配置 Cᴏɴғɪɢᴜʀᴀᴛɪᴏɴ

在根目录创建 `config.json`，参考以下格式（注意 Windows 路径需使用 `/` 或 `\\`）：

```json
{
    "questionnaire": 问卷查询链接的标识,
    "password": 查询密码,
    "downloader_script_dir": "E:/Path/To/THU-Cloud-Downloader",
    "date_start": "2023-10-01",  
    "date_length": 7,
    "save_dir": "E:/Output/Directory"
}
```

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| _questionnaire_ | `str` | 问卷查询链接中的标识部分，来自对外查询链接 `https://wenjuan.tsinghua.edu.cn/setting/result/{questionnaire}/` |
| _password_ | `str` | 问卷查询链接设置的查询密码 |
| _downloader_script_dir_ | `str` | [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader) 的脚本目录路径 |
| _date_start_ | `str` | 查询起始日期，格式为 `YYYY-MM-DD`；默认为当前日期 `datetime.date.today()` |
| _date_length_ | `int` | 查询日期长度（天数）；默认为 7，表示查询从 `date_start` 起（含）向后 7 天内的数据 |
| _save_dir_ | `str` | 问卷数据和资源的保存目录路径；默认为当前目录下的 `output` 文件夹 |

直接运行 `python main.py` 即可启动自动化任务。

## 注意事项 Pʀᴇᴄᴀᴜᴛɪᴏɴs

-   **路径格式**：在 `config.json` 中配置 Windows 路径时，务必使用双反斜杠 `\\` 或单正斜杠 `/`，否则会引发 JSON 解析错误。
-   **编码问题**：项目已处理 Windows 控制台编码问题，但若仍遇乱码报错，请尝试设置环境变量 `PYTHONIOENCODING=utf-8`。
-   **外部依赖**：视频下载依赖 [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader)，请确保该脚本路径配置正确且可独立运行。
-   **Markdown 预览**：生成的 Markdown 文件路径采用 `<file:///>` 协议，其他编辑器可能表现不同。
