import logging
import textwrap
import pandas as pd
import os

def execute_code(code, dataframes, source_file_paths, template_file_path):
    """
    执行代码模型生成的代码的函数
    :param code: 代码模型生成的代码
    :param dataframes: 源数据文件的数据框字典
    :param source_file_paths: 源数据文件路径列表
    :param template_file_path: 模板文件路径
    :return: 执行代码后的结果
    """
    code = textwrap.dedent(code)
    logging.info("开始执行代码模型生成的代码...")

    try:
        locals().update(dataframes)

        for i, file_path in enumerate(source_file_paths):
            code = code.replace(f"'{i+1}.xlsx'", f"'{file_path}'")
        code = code.replace("'out.xlsx'", f"'{template_file_path}'")

        exec(code, globals(), locals())

        result = locals().get('merged_table', None)
        if result is None:
            logging.warning("代码执行后未找到结果，请检查代码是否正确赋值给 merged_table 变量。")
            return "代码执行后未找到结果，请检查代码是否正确赋值给 merged_table 变量。"

        logging.info(f"代码执行完成，得到结果:\n{result}\n")
        return result
    except Exception as e:
        logging.error(f"执行代码时出错：{e}")
        return "执行代码时出错，请检查代码或 dataframes是否正确。"