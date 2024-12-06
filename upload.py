import os
import pandas as pd
import logging

def upload_source_files(files):
    """
    上传源数据文件的函数
    :param files: 要上传的文件列表
    :return: 上传结果提示信息
    """
    logging.info("开始上传源数据文件...")
    source_file_paths = []
    for file in files:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension in ['.xls', '.xlsx', '.csv']:
            try:
                if file_extension == '.csv':
                    df = pd.read_csv(file.name)
                elif file_extension in ['.xls', '.xlsx']:
                    df = pd.read_excel(file.name, engine='openpyxl')
                source_file_paths.append(file.name)
            except Exception as e:
                logging.error(f"读取文件 {file.name} 时出错：{e}")
                return f"读取文件 {file.name} 时出错，请检查文件是否正确。"
        else:
            logging.warning(f"不支持的文件类型：{file_extension}")
            return f"不支持的文件类型：{file.extension}"
    logging.info("源数据文件上传成功。")
    return source_file_paths

def upload_template_file(file):
    """
    上传模板文件的函数
    :param file: 要上传的文件
    :return: 上传结果提示信息
    """
    logging.info("开始上传模板文件...")
    file_extension = os.path.splitext(file.name)[1]
    if file_extension in ['.xls', '.xlsx', '.csv']:
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file.name)
            elif file_extension in ['.xls', '.xlsx']:
                df = pd.read_excel(file.name, engine='openpyxl')
            logging.info("模板文件上传成功。")
            return file.name
        except Exception as e:
            logging.error(f"读取文件 {file.name} 时出错：{e}")
            return f"读取文件 {file.name} 时出错，请检查文件是否正确。"
    else:
        logging.warning(f"不支持的模板文件类型。")
        return "不支持的模板文件类型。"