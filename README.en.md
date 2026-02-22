# THU-Questionnaire-Downloader

**THU-Questionnaire-Downloader** is an automated data collection tool designed specifically for the [Tsinghua University Survey System (https://wenjuan.tsinghua.edu.cn)](https://wenjuan.tsinghua.edu.cn). It automates the process of logging in, scraping survey data, and intelligently downloading multimedia attachments, including images and videos from Tsinghua Cloud. Finally, it generates comprehensive summary reports in Markdown and PDF formats, greatly simplifying the organization of multimedia survey data.

## Features

The core functionality covers the entire process from data acquisition to report generation:
-   **Automated Interaction**: Uses `DrissionPage` to automatically complete login and password verification for the survey site, supporting data filtering by date range.
-   **Multimedia Downloading**: Not only saves plain text responses but also automatically identifies and downloads image attachments in the survey. It also invokes [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader) to download video files stored on Tsinghua Cloud.
-   **Report Generation**: Automatically generates a structured `booking_info.md` summary file, embedded with local file links, and exports a PDF version using Pandoc.

**The program flow and report structure in `thu_questionnaire_downloader.py` are examples only. Please adjust them according to the actual structure of your survey query page.**

## File Structure

The project maintains a flat and concise file structure:
-   `main.py`: **Entry Script**. Responsible for reading configuration, scheduling download tasks, and generating the final report.
-   `thu_questionnaire_downloader.py`: **Core Logic**. Contains the crawler implementation, data parsing, resource downloading, and Markdown generation logic.
-   `config.json`: **Configuration File**. Stores user credentials, target survey information, and path settings.
-   `output/`: **Default Output Directory**. Contains the generated `booking_info.md`, PDF report, and resource subfolders classified by entry.

## Usage

### Installation

Development was done in a Python 3.12.9 environment. According to AI analysis, Python 3.8+ should be compatible, but using the latest version is recommended for best performance and compatibility.

1.  Clone the repository and enter the directory.
2.  Install dependencies:
    ```bash
    pip install DrissionPage rich pypandoc requests
    ```
3.  Prepare the external tool [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader) for video downloading.

If PDF generation is required, you also need to install [Pandoc](https://pandoc.org/installing.html). Without Pandoc, PDF conversion will fail, but the Markdown file will still be generated normally.

### Configuration

Create `config.json` in the root directory, referring to the following format (note that Windows paths must use `/` or `\\`):

```json
{
    "questionnaire": "Questionnaire Identifier",
    "password": "Query Password",
    "downloader_script_dir": "E:/Path/To/THU-Cloud-Downloader",
    "date_start": "2023-10-01",  
    "date_length": 7,
    "save_dir": "E:/Output/Directory"
}
```

| Parameter | Type | Description |
| --- | --- | --- |
| _questionnaire_ | `str` | The identifier part of the survey query link, from the external query link `https://wenjuan.tsinghua.edu.cn/setting/result/{questionnaire}/` |
| _password_ | `str` | The query password set for the survey query link |
| _downloader_script_dir_ | `str` | The script directory path of [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader) |
| _date_start_ | `str` | The query start date, in `YYYY-MM-DD` format; defaults to the current date `datetime.date.today()` |
| _date_length_ | `int` | The query date length (days); defaults to 7, meaning querying data for 7 days starting from `date_start` (inclusive) |
| _save_dir_ | `str` | The directory path to save survey data and resources; defaults to the `output` folder in the current directory |

Run `python main.py` directly to start the automation task.

## Precautions

-   **Path Format**: When configuring Windows paths in `config.json`, make sure to use double backslashes `\\` or single forward slashes `/`, otherwise it will cause JSON parsing errors.
-   **Encoding Issues**: The project handles Windows console encoding issues, but if you still encounter garbled text errors, try setting the environment variable `PYTHONIOENCODING=utf-8`.
-   **External Dependency**: Video downloading relies on [THU-Cloud-Downloader](https://github.com/TheTenth-THU/THU-Cloud-Downloader). Ensure that the script path is configured correctly and it can run independently.
-   **Markdown Preview**: The generated Markdown file paths use the `<file:///>` protocol. Other editors may behave differently.
