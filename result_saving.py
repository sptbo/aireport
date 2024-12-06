import logging
import os
import pandas as pd

def save_result(result, template_file_path):
    """
    将结果保存到模板文件的函数
    :param result: 执行代码后的结果
    :param template_file_path: 模板文件路径
    :return: 无
    """
    output_file_name = os.path.splitext(template_file_path)[0] + '.xlsx'
    return output_file_name 