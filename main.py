from thu_questionnaire_downloader import main
import json

if __name__ == "__main__":
    """ 使用配置文件运行主函数。
    
    在配置文件 `config.json` 中指定以下参数：
    - `questionnaire` (str): 问卷查询链接的标识符
    - `password` (str): 问卷查询的密码
    - `downloader_script_dir` (str): THU-Cloud-Downloader 脚本所在目录
    - `date_start` (str, optional): 查询的起始日期，格式为 "YYYY-MM-DD"，默认为当前日期
    - `date_length` (int, optional): 查询的日期范围长度（天数），默认为 7 天
    - `save_dir` (str, optional): 下载文件的保存目录，默认为当前目录下的 "output" 文件夹
    """
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    main(**config)