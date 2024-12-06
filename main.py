from prompt_optimization import optimize_prompt
from code_generation import call_model
from code_execution import execute_code
from result_saving import save_result
import logging
import os
import pandas as pd

def process_files(prompt, source_file_paths, template_file_path):
    """
    处理文件的主函数，使用统一收集的信息进行处理，包括读取源数据文件、优化提示词、调用代码模型生成代码、执行代码并保存结果
    :param prompt: 提示词
    :param source_file_paths: 源数据文件路径列表
    :param template_file_path: 模板文件路径
    :return: 结果文件路径以便下载或错误提示信息
    """
    logging.info("开始处理文件...")

    try:
        dataframes = []
        for file_path in source_file_paths:
            file_extension = os.path.splitext(file_path)[1]
            try:
                if file_extension == '.csv':
                    df = pd.read_csv(file_path)
                elif file_extension in ['.xls', '.xlsx']:
                    df = pd.read_excel(file_path, engine='openpyxl')
                dataframes.append(df)
            except Exception as e:
                logging.error(f"读取文件 {file_path} 时出错：{e}")
                return f"读取文件 {file_path} 时出错，请检查文件是否正确。"

        if not template_file_path:
            logging.error("未上传模板文件，请上传后再试。")
            return "未上传模板文件，请上传后再试。"

        try:
            file_extension = os.path.splitext(template_file_path)[1]
            if file_extension == '.csv':
                pd.read_csv(template_file_path)
            elif file_extension in ['.xls', '.xlsx']:
                pd.read_excel(template_file_path, engine='openpyxl')
        except Exception as e:
            logging.error(f"读取模板文件 {template_file_path} 时出错：{e}")
            return "读取模板文件时出错，请检查文件是否正确。"

        if not prompt:
            logging.error("提示词未设置，请先设置提示词再处理文件。")
            return "提示词未设置，请先设置提示词再处理文件。"

        prompt_with_files = f"{prompt}\n\n源数据文件路径：{source_file_paths}\n模板文件路径：{template_file_path}"
        optimized_prompt = optimize_prompt(prompt_with_files)
        logging.info("提示词优化完成。")

        try:
            code = call_model(optimized_prompt)
            logging.info("代码模型生成代码完成。")
        except Exception as e:
            logging.error(f"调用代码模型生成代码时出错：{e}")
            return "调用代码模型生成代码时出错，请检查网络或模型设置。"

        try:
            result = execute_code(code, dataframes, source_file_paths, template_file_path)
            logging.info("代码执行完成，得到结果。")
        except Exception as e:
            logging.error(f"执行代码生成结果时出错：{e}")
            return "执行代码生成结果时出错，请检查代码或数据是否正确。"

        output_file_path = save_result(result, template_file_path)
        logging.info("结果已保存到模板文件。")

        return output_file_path
    except Exception as e:
        logging.error(f"处理文件时出错：{e}")
        return "处理文件出错，请检查日志。"