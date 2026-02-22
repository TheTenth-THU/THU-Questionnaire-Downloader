import subprocess
import os
from DrissionPage import ChromiumPage, ChromiumOptions

import logging
from rich.console import Console
from rich.logging import RichHandler

import datetime
import re
import json
import pypandoc


console = Console()
NEWLINE = "\n"


logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)


def verify_password(page: ChromiumPage, questionnaire: str, password: str) -> dict:
    url = f"https://wenjuan.tsinghua.edu.cn/setting/result/{questionnaire}/"
    
    # 访问查询首页，监听获取 appkey 和 signature
    try:
        # 设置网络请求监听
        page.listen.start(f'sr/api/{questionnaire}/validate/') 
        logging.info(f"打开查询首页...")
        logging.debug(f"- url: {url}")
        page.get(url)
        
        res = page.listen.wait(timeout=10)
        logging.info(f"捕获网络请求: \n- target: sr/api/{questionnaire}/validate/\n- url: {res.url}")
        logging.debug(f"- method: {res.method}\n- status: {res.response.status}")

        # GET
        if 'appkey' in res.request.params:
            appkey = res.request.params['appkey']
            signature = res.request.params.get('signature')
        # POST
        if isinstance(res.request.post_data, dict) and 'appkey' in res.request.post_data:
            appkey = res.request.post_data['appkey']
            signature = res.request.post_data.get('signature')
        logging.debug(f"获取到 appkey 和 signature：\n- appkey: {appkey}\n- signature: {signature}")
        page.listen.stop()
    
    except Exception as e:
        logging.exception(f"访问查询首页出错：\n- url: {url}\n- error: {e}")
        return {}
    
    # 填写密码并提交
    try:
        # 设置网络请求监听
        page.listen.start(f'sr/api/{questionnaire}/query/')
        ele_input = page.ele('xpath://input[@placeholder="请输入访问密码"]')
        ele_input.input(password)
        ele_button = page.ele('text:验证并查询')
        ele_button.click()
        logging.info(f"已输入密码并提交。")

        res = page.listen.wait(timeout=10)
        logging.info(f"捕获网络请求: \n- target: sr/api/{questionnaire}/query/\n- url: {res.url}")
        logging.debug(f"- status: {res.response.status}\n- response: {json.dumps(res.response.body, ensure_ascii=False, indent=2)}")
        page.listen.stop()
        logging.info(f"密码验证完成。")

    except Exception as e:
        if 'res' in locals() and hasattr(res, 'response') and hasattr(res.response, 'body'):
            logging.exception(f"提交密码出错：\n- error: {e}\n- response: {json.dumps(res.response.body, ensure_ascii=False, indent=2)}")
        else:
            logging.exception(f"提交密码出错：\n- error: {e}\n- response: No response captured.")
        return {}

    return {
        "appkey": appkey,
        "signature": signature
    }


def get_questionnaire_data(page: ChromiumPage, questionnaire: str, date: str) -> list:
    url = f"https://wenjuan.tsinghua.edu.cn/setting/result/verify/{questionnaire}"
    page.get(url)

    try:
        # 设置网络请求监听
        page.listen.start(f'sr/api/{questionnaire}/search/')
        logging.info(f"监听查询 {date} 预约数据...")
        logging.debug(f"- url: {url}\n- date: {date}")
        ele_date = page.ele('xpath://input[@placeholder="选择日期"]')
        ele_date.click()
        ele_date.clear()
        ele_date.input(date)
        logging.debug(f"已输入日期：{date}")
        ele_title = page.ele('tag:h3')
        ele_title.click()   # 点击标题以触发日期选择框的关闭和数据的刷新
        logging.debug("已点击标题以触发日期选择框的关闭和数据的刷新")
        page.wait(1)        # 等待选择框关闭
        ele_button = page.ele('xpath://button[contains(., "查询")]')
        logging.debug(f"选中按钮：{ele_button.html}")
        ele_button.click()
        logging.debug(f"已点击查询按钮")

        res = page.listen.wait(timeout=10)
        logging.info(f"捕获网络请求：\n- target: sr/api/{questionnaire}/search/\n- url: {res.url}")
        logging.debug(f"- method: {res.method}\n- status: {res.response.status}\n- response: {json.dumps(res.response.body, ensure_ascii=False, indent=2)}")
        page.listen.stop()
        
    except Exception as e:
        if 'res' in locals() and hasattr(res, 'response') and hasattr(res.response, 'body'):
            logging.exception(f"查询数据出错：\n- url: {url}\n- error: {e}\n- response: {json.dumps(res.response.body, ensure_ascii=False, indent=2)}")
        else:
            logging.exception(f"查询数据出错：\n- url: {url}\n- error: {e}\n- response: No response captured.")
        return []

    # 解析数据
    if 'data' not in res.response.body or res.response.body['data'].get('totalCount', 0) == 0:
        logging.warning(f"未查询到 {date} 数据。")
        logging.debug(f"- date: {date}\n- totalCount: {res.response.body.get('data', {}).get('totalCount', 0)}")
        return []
    
    result = res.response.body['data']['query_result']
    logging.info(f"查询到数据：\n- date: {date}\n- totalCount: {res.response.body['data']['totalCount']}")
    logging.debug(f"- data: {json.dumps(result, ensure_ascii=False, indent=2)}")

    for item in result:
        for upload in [8, 11]:
            if item['questions'][upload]['answer'] != '':
                # 获取文件链接
                logging.info(f"正在获取文件链接...\n- respond index: {item['seq']}\n- question index: {upload}\n- file_name: {item['questions'][upload]['answer']}")
                page.listen.start(f'wjxt/file/rspd/upload_file/')
                file_name = item['questions'][upload]['answer']
                ele_preview = page.ele(f'xpath://div[contains(text(), "{file_name}")]/span[@class="preview"]')
                ele_preview.click()
                res_img = page.listen.wait(timeout=10)
                if res_img and res_img.response and res_img.response.status == 200:
                    logging.info(f"捕获网络请求：\n- target: wjxt/file/rspd/upload_file/\n- url: {res_img.url}")
                    logging.debug(f"- method: {res_img.method}\n- status: {res_img.response.status}")
                    item['questions'][upload]['base64'] = res_img.response.body
                else:
                    logging.warning(f"未捕获到文件请求：\n- target: wjxt/file/rspd/upload_file/\n- file_name: {file_name}\n- response: No response captured or non-200 status.")
                page.listen.stop()
                ele_close = page.ele('xpath://div[contains(text(), "附件预览")]/button[@aria-label="Close"]')
                ele_close.click()
            else:
                logging.debug(f"该问题未上传文件：\n- respond index: {item['seq']}\n- question index: {upload}\n- answer: {item['questions'][upload]['answer']}")

    return result


def dump_booking_info(seq: int, rid: str, questions: list, save_dir: str, downloader_script_dir: str) -> str:
    """ 将预约信息保存到本地 Markdown 文件中，将相关文件保存到文件夹。
    
    Markdown 文件内容格式为：
    + 按照预约发布日期降序排列，同一天内按照预约序号降序排列；
    + 每个问题的回答单独成一行，文件链接以 Markdown 链接的形式展示，链接文本为文件名，链接地址为下载保存的本地文件路径。

    示例：
    ```
    ## 2026-02-15
    ### {_seq_}: {_rid_}
    联系人：...
    视频基本信息：
    + 预约日期时间：**不定时** ...
    视频封面：...
    视频发布信息：...
    ### {_seq_}: {_rid_}
    ## 2026-02-14
    ```

    若检测到同一预约序号的信息已在本地存在，则覆盖原有信息并更新文件。

    Args:
        seq (int): 预约序号
        rid (str): 预约 ID
        questions (list): 问卷问题列表，每个问题包含问题文本 _title_、回答文本 _answer_；对于上传文件的问题，_answer_ 为文件名，且包含一个 _base64_ 字段表示文件的 Base64 编码内容
        save_dir (str): 保存目录路径，文件将保存到该目录下的 `booking_info.md`，相关文件将保存到该目录下的 `{seq}_{%Y%m%d}\\` 文件夹中。

    Returns:
        file_path (str): 预约信息 Markdown 文件的路径
    """
    file_path = os.path.join(save_dir, "booking_info.md")
    folder_path = os.path.join(save_dir, f"{seq}_{datetime.datetime.strptime(questions[1]['answer'], '%Y-%m-%d').strftime('%Y%m%d')}")
    if os.path.exists(folder_path):
        logging.warning(f"信息文件夹已存在，将写入已有文件夹，可能覆盖原有文件\n- folder path: {folder_path}")
    os.makedirs(folder_path, exist_ok=True)
    logging.info(f"正在保存预约信息：\n- seq: {seq}\n- file path: {file_path}\n- folder path: {folder_path}")
    logging.debug(f"- rid: {rid}\n- questions: {json.dumps(questions, ensure_ascii=False, indent=2, default=lambda x: '<bytes>' if isinstance(x, bytes) else str(x))}")

    # 保存相关文件
    video_path = os.path.join(folder_path, f"{seq}-{questions[5]['answer']}.mp4")
    try:
        download_from_cloud(questions[3]['answer'], folder_path, f"{seq}-{questions[5]['answer']}.mp4", downloader_script_dir)
    except Exception as e:
        logging.exception(f"下载视频文件出错：\n- seq: {seq}\n- link: {questions[3]['answer']}\n- error: {e}")
        video_path = "下载失败"

    cover1_path = os.path.join(folder_path, f"{seq}-{questions[5]['answer']}-cover1.jpg")
    try:
        if questions[7]['answer'] == "此处上传" and 'base64' in questions[8]:
            with open(cover1_path, "wb") as f:
                f.write(questions[8]['base64'])
        elif questions[7]['answer'].startswith("已附在云盘链接中"):
            cover1_original_path = os.path.join(folder_path, questions[7]['answer'].split("文件名：:")[-1])
            if os.path.exists(cover1_original_path):
                os.rename(cover1_original_path, cover1_path)
            else:
                logging.warning(f"封面文件原始路径不存在，无法重命名\n- expected path: {cover1_original_path}")
                cover1_path = cover1_original_path
    except Exception as e:
        logging.exception(f"下载封面文件1出错：\n- seq: {seq}\n- Q8 answer: {questions[7]['answer']}\n- Q9 answer: {questions[8]['answer']}\n- error: {e}")
        cover1_path = "下载失败"

    cover2_path = os.path.join(folder_path, f"{seq}-{questions[5]['answer']}-cover2.jpg")
    try:
        if questions[10]['answer'] == "此处上传" and 'base64' in questions[11]:
            with open(cover2_path, "wb") as f:
                f.write(questions[11]['base64'])
        elif questions[10]['answer'].startswith("已附在云盘链接中"):
            cover2_original_path = os.path.join(folder_path, questions[10]['answer'].split("文件名：:")[-1])
            if os.path.exists(cover2_original_path):
                os.rename(cover2_original_path, cover2_path)
            else:
                logging.warning(f"封面文件原始路径不存在，无法重命名\n- expected path: {cover2_original_path}")
                cover2_path = cover2_original_path
        elif questions[10]['answer'].endswith("无需上传"):
            cover2_path = "无需上传"
    except Exception as e:
        logging.exception(f"下载封面文件2出错：\n- seq: {seq}\n- Q10 answer: {questions[10]['answer']}\n- Q11 answer: {questions[11]['answer']}\n- error: {e}")
        cover2_path = "下载失败"
    
    # 组合预约信息文本
    booking_info = [f"{seq}: _{rid}_"]
    booking_info.append(
        "联系人：" + NEWLINE 
        + NEWLINE.join([f"+ {part.replace(': ', '：')}" for part in questions[0]['answer'].split("<br/>")])
    )
    booking_info.append(
        "视频基本信息：" + NEWLINE
        + f"+ 预约日期时间：{questions[1]['answer']}，**{questions[2]['answer'].replace('定时至：:', '定时至 ')}**" + NEWLINE
        + f"+ 视频文件路径：**{f'[{video_path}](<file:///{video_path}>)' if video_path != '下载失败' else video_path}**" + NEWLINE
        + f"+ 描述文本：\n  > {"\n  > \n  > ".join(questions[4]['answer'].split(NEWLINE))}" + NEWLINE
        + f"+ 短标题：**{questions[5]['answer']}**"
    )
    booking_info.append(
        "视频封面：" + NEWLINE
        + f"+ 个人主页卡片封面 (3:4)：" + NEWLINE
        + f"    + 展示方式：**{questions[6]['answer'][:4]}**" + NEWLINE
        + f"    + 文件路径：**{f'[{cover1_path}](<file:///{cover1_path}>)' 
                               if cover1_path != '下载失败' else cover1_path}**" + NEWLINE
        + f"    + 裁剪说明：**{questions[9]['answer']}**" + NEWLINE
        + f"+ 横屏分享卡片封面 (4:3)：" + NEWLINE
        + f"    + 文件路径：**{f'[{cover2_path}](<file:///{cover2_path}>)' 
                               if cover2_path != '下载失败' and cover2_path != '无需上传' else cover2_path}**" + NEWLINE
        + f"    + 裁剪说明：**{questions[12]['answer']}**"
    )
    booking_info.append(
        "视频发布信息：" + NEWLINE
        + f"+ 合集：**{questions[13]['answer']}**{
            "" if questions[13]['answer'] != "实践纪实" else
            "，确认已通过实践单位、实践组审核" if questions[14]['answer'] and questions[15]['answer'] else
            "，待实践单位、实践组审核"
        }" + NEWLINE
        + f"+ 链接到公众号文章：**{questions[16]['answer']}**"
    )
    booking_info_text = (NEWLINE + NEWLINE).join(booking_info) + NEWLINE + NEWLINE
    
    # 将预约信息写入 Markdown 文件
    if not os.path.exists(file_path):
        logging.warning(f"预约信息文件不存在，将创建新文件\n- file path: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")
    with open(file_path, "r+", encoding="utf-8") as f:
        # 读取原有内容，按 `## ` 和 `### ` 分割出不同预约信息块
        content = f.read()
        date_blocks = re.split(r'(?m)^## ', content) if content else []
        date_block_dict = {}    # { date: [seq_block1, seq_block2, ...], ... }
        for block in date_blocks:
            if not block.strip():
                continue
            lines = block.splitlines()
            if not lines or not lines[0].strip():
                continue
            date = lines[0].strip()     # 日期行
            date_block_dict[date] = re.split(r'(?m)^### ', NEWLINE.join(lines[1:]) 
                                             if len(lines) > 1 else "")
            date_block_dict[date] = [seq_block for seq_block in date_block_dict[date] if seq_block.strip()]
        # 更新当前预约信息到对应日期块
        booking_date = questions[1]['answer']
        if booking_date in date_block_dict:
            # 日期块已存在，更新或添加预约信息
            seq_blocks = date_block_dict[booking_date]
            seq_block_dict = {}     # [ seq_block, ... ] -> { seq_num: seq_block, ... }
            for seq_block in seq_blocks:
                lines = seq_block.splitlines()
                if not lines or not lines[0].strip():
                    continue
                seq_line = lines[0].strip()                     # 预约序号行
                seq_num = int(seq_line.split(":")[0].strip())   # 提取预约序号
                seq_block_dict[seq_num] = seq_block             # 存储原有预约信息块
            # 更新或添加当前预约信息块
            seq_block_dict[seq] = booking_info_text
            # 按预约序号降序排序后重新组合日期块内容
            updated_seq_blocks = [seq_block_dict[num] for num in sorted(seq_block_dict.keys(), reverse=True)]
            date_block_dict[booking_date] = updated_seq_blocks
        else:
            # 日期块不存在，创建新日期块并添加预约信息
            date_block_dict[booking_date] = [booking_info_text]
        logging.debug(f"更新后的条目块内容 date_block_dict：\n{json.dumps(date_block_dict, ensure_ascii=False, indent=2)}")
        # 按日期降序排序后重新组合文件内容
        updated_date_blocks = [f"{date}\n\n### " + "### ".join(date_block_dict[date]) for date in sorted(date_block_dict.keys(), reverse=True)]
        logging.debug(f"更新后的日期块内容 updated_date_blocks：\n{json.dumps(updated_date_blocks, ensure_ascii=False, indent=2)}")
        updated_content = "## " + "## ".join(updated_date_blocks)
        logging.debug(f"更新后的预约信息文件内容 updated_content：\n{updated_content}")
        # 写回文件
        f.seek(0)
        f.write(updated_content)
        f.truncate()

    return file_path


def download_from_cloud(link: str, save_dir: str, save_name: str, downloader_script_dir: str):
    """ 调用 THU-Cloud-Downloader 工具下载文件并保存到本地。
    
    + 若 _link_ 为文件（`f`）共享链接，相当于在命令行中执行以下命令：
    ```
    python thu_cloud_download.py -l {link} -s {save_dir} -n {save_name} -y
    ```
    + 若 _link_ 为文件夹（`d`）共享链接，则下载该文件夹下的所有文件，并将它们保存到 `{save_dir}\\` 目录下，相当于在命令行中执行以下命令：
    ```
    python thu_cloud_download.py \\
        -l {link} \\
        -s {os.path.dirname(os.path.normpath(save_dir))} \\
        -n {os.path.basename(os.path.normpath(save_dir))} \\
        -y
    ```
    然后找到最大的 MP4 文件并重命名为 _save_name_。

    Args:
        link (str): 文件链接
        save_dir (str): 保存目录路径
        save_name (str): 保存文件名，须包含扩展名
    """
    script_dir = os.path.abspath(downloader_script_dir)
    script_path = os.path.join(script_dir, "thu_cloud_download.py")
    script_venv = os.path.join(script_dir, ".venv", "Scripts", "python.exe")

    if not os.path.exists(script_venv):
        raise FileNotFoundError(f"Python executable not found in virtual environment: {script_venv}")
    
    prefix = {'d': 'https://cloud.tsinghua.edu.cn/d/', 'f': 'https://cloud.tsinghua.edu.cn/f/'}
    if link.startswith(prefix['d']):
        share_type = 'd'
        command = [script_venv, script_path, "-l", link, 
                   "-s", os.path.dirname(os.path.normpath(save_dir)), 
                   "-n", os.path.basename(os.path.normpath(save_dir)), "-y"]
    elif link.startswith(prefix['f']):
        share_type = 'f'
        command = [script_venv, script_path, "-l", link, "-s", save_dir, "-n", save_name, "-y"]
    else:
        raise ValueError(f"URL 格式不符合要求，无法识别是文件链接还是文件夹链接\n- link: {link}\n- expected prefix: {prefix['d']} or {prefix['f']}")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(command, cwd=script_dir, capture_output=True, text=True, env=env, encoding="utf-8")
    logging.debug(f"THU-Cloud-Downloader 输出：\n- stdout: {result.stdout}")
    if result.returncode != 0:
        raise RuntimeError(f"THU-Cloud-Downloader 运行错误\n- stderr: {result.stderr}")
    
    # 对于文件夹链接，找到最大的 MP4 文件并重命名为 save_name
    if share_type == 'd':
        downloaded_files = [f for f in os.listdir(save_dir) if f.lower().endswith('.mp4')]
        if not downloaded_files:
            logging.warning(f"未找到下载的 MP4 文件\n- expected directory: {save_dir}")
        largest_file = max(downloaded_files, key=lambda f: os.path.getsize(os.path.join(save_dir, f)))
        largest_file_path = os.path.join(save_dir, largest_file)
        final_save_path = os.path.join(save_dir, save_name)
        os.rename(largest_file_path, final_save_path)


def main(questionnaire: str, password: str,
         downloader_script_dir: str, 
         date_start: str = None, date_length: int = 7,
         save_dir: str = None):
    # 初始化浏览器对象
    try:
        co = ChromiumOptions()
        co.headless()
        co.remove_argument('--proxy-server')
        co.set_argument('--no-proxy-server')
        page = ChromiumPage(addr_or_opts=co)

        verify_password(page, questionnaire, password)

        if not date_start:
            date_start = datetime.date.today()
        else:
            date_start = datetime.datetime.strptime(date_start, "%Y-%m-%d").date()

        if not isinstance(date_length, int) or date_length <= 0:
            date_length = 7

        if not save_dir:
            save_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(save_dir):
            logging.warning(f"保存目录不存在，将创建新目录\n- save dir: {save_dir}")

        result = []
        for delta in range(date_length):
            # 查询今天起向后 date_length 天的数据
            date = (date_start + datetime.timedelta(days=delta)).strftime("%Y-%m-%d")
            result.extend(get_questionnaire_data(page, questionnaire, date))

        file_path = ""
        for item in result:
            file_path = dump_booking_info(item['seq'], item['rid'], item['questions'], save_dir, downloader_script_dir)
        if file_path:
            try:
                output = pypandoc.convert_file(file_path, 'pdf', outputfile=file_path.replace(".md", ".pdf"))
            except OSError as e:
                logging.warning(f"Pandoc 转换 PDF 失败，可能是系统中未安装 Pandoc 或相关依赖，或文件路径中包含特殊字符导致转换失败\n- file path: {file_path}\n- error: {e}")

    except Exception as e:
        logging.exception(f"程序出错：\n- error: {e}")
    finally:
        if 'page' in locals():
            page.quit()
        logging.info("页面已关闭，程序结束。")


if __name__ == "__main__":
    main("me2AZ3", downloader_script_dir=r"E:\Programs\Tools\THU-Cloud-Downloader", date_start="2026-02-14")
