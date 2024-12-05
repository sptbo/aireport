import os
import logging
import gradio as gr
import pandas as pd
import re
import textwrap
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import QianfanLLMEndpoint

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置凭证信息
os.environ["QIANFAN_AK"] = "JRLvQvdUbRXWtYG1hKmbrkwY"
os.environ["QIANFAN_SK"] = "RhFqbIO1tDTEgzpEIkqHKa4LpQOQu1vq"

def upload_source_files(files):
    """
    上传源数据文件的函数
    :param files: 要上传的文件列表
    :return: 上传结果提示信息
    """
    logging.info("开始上传源数据文件...")
    source_files = []
    for file in files:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension in ['.xls', '.xlsx', '.csv']:
            try:
                # 尝试读取文件，检查文件是否可正常读取
                if file_extension == '.csv':
                    df = pd.read_csv(file.name)
                elif file_extension in ['.xls', '.xlsx']:
                    df = pd.read_excel(file.name, engine='openpyxl')  # 手动指定引擎
                source_files.append(df)
            except Exception as e:
                logging.error(f"读取文件 {file.name} 时出错：{e}")
                return f"读取文件 {file.name} 时出错，请检查文件是否正确。"
        else:
            logging.warning(f"不支持的文件类型：{file_extension}")
            return f"不支持的文件类型：{file.extension}"
    logging.info("源数据文件上传成功。")
    return source_files

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
            # 尝试读取文件，检查文件是否可正常读取
            if file_extension == '.csv':
                df = pd.read_csv(file.name)
            elif file_extension in ['.xls', '.xlsx']:
                df = pd.read_excel(file.name, engine='openpyxl')  # 手动指定引擎
            logging.info("模板文件上传成功。")
            return file.name
        except Exception as e:
            logging.error(f"读取文件 {file.name} 时出错：{e}")
            return f"读取文件 {file.name} 时出错，请检查文件是否正确。"
    else:
        logging.warning(f"不支持的模板文件类型。")
        return "不支持的模板文件类型。"

def process_files(prompt, source_files, template_file_path):
    """
    处理文件的主函数，使用统一收集的信息进行处理，包括读取源数据文件、优化提示词、调用代码模型生成代码、执行代码并保存结果
    :param prompt: 提示词
    :param source_files: 源数据文件路径列表
    :param template_file_path: 模板文件路径
    :return: 结果文件路径以便下载或错误提示信息
    """
    logging.info("开始处理文件...")

    try:
        # 确认源数据文件路径并读取源数据文件
        dataframes = []
        for df in source_files:
            dataframes.append(df)

        # 确认模板文件路径
        if not template_file_path:
            logging.error("未上传模板文件，请上传后再试。")
            return "未上传模板文件，请上传后再试。"

        # 再次确认模板文件是否可读取
        try:
            file_extension = os.path.splitext(template_file_path)[1]
            if file_extension == '.csv':
                pd.read_csv(template_file_path)
            elif file_extension in ['.xls', '.xlsx']:
                pd.read_excel(template_file_path, engine='openpyxl')  # 手动指定引擎
        except Exception as e:
            logging.error(f"读取模板文件 {template_file_path} 时出错：{e}")
            return "读取模板文件时出错，请检查文件是否正确。"

        if not prompt:
            logging.error("提示词未设置，请先设置提示词再处理文件。")
            return "提示词未设置，请先设置提示词再处理文件。"
        optimized_prompt = optimize_prompt(prompt)
        logging.info("提示词优化完成。")

        # 调用代码模型生成代码
        try:
            code = call_model(optimized_prompt)
            logging.info("代码模型生成代码完成。")
        except Exception as e:
            logging.error(f"调用代码模型生成代码时出错：{e}")
            return "调用代码模型生成代码时出错，请检查网络或模型设置。"

        # 执行代码生成结果
        try:
            result = execute_code(code, dataframes)
            logging.info("代码执行完成，得到结果。")
        except Exception as e:
            logging.error(f"执行代码生成结果时出错：{e}")
            return "执行代码生成结果时出错，请检查代码或数据是否正确。"

        # 按照用户指令将结果写到模板文件的相应位置
        output_file_path = save_result(result, template_file_path)
        logging.info("结果已保存到模板文件。")

        # 返回结果文件路径以便下载
        return output_file_path
    except Exception as e:
        logging.error(f"处理文件时出错：{e}")
        return "处理文件出错，请检查日志。"

def optimize_prompt(prompt):
    """
    优化提示词的函数，目前仅返回原提示词，可在此添加优化逻辑
    :param prompt: 原始提示词
    :return: 优化后的提示词
    """
    llm = QianfanLLMEndpoint(model='ERNIE-Speed-128K')
    logging.info(f"原始提示词：\n{prompt}\n")

    full_prompt = f"""你身为大模型提示词领域的专家以及精通 Python 语言编程的高手，请对>>>和<<<间的用户提示词进行优化处理：
        >>>
        \n{prompt}\n
        <<<
        要求如下：
        1.优化的目的在于使大模型能够凭借优化后的提示词精准无误地编写出可完成特定数据处理任务的 Python 代码。
        2.要充分考虑到数据处理任务的各个细节以及 Python 编程的规范与高效性要求，确保大模型能准确理解并生成符合预期的代码逻辑。
        3.优化后的提示词步骤清晰，包含所有必要的信息，并遵循 Python 编程的最佳实践。
        4.只对>>>与<<<之间的内容进行优化，不要生成代码。
        5.对于优化后的内容，只返回>>>与<<<之间的内容，不要返回其他任何内容。
        6.优化后的内容以第一人称描述。
        """
    
    logging.info(f"优化前的提示词模板：\n{full_prompt}\n")

    logging.info("开始优化提示词...")
    try:
        prompt_template = PromptTemplate.from_template(full_prompt)
        chain = LLMChain(llm=llm, prompt=prompt_template)
        x = chain.run({})
        # logging.info(f"chain.run:\n{x}\n")
        optimized_prompt = x
        logging.info(f"提权>>> <<<前：\n{optimized_prompt}\n")
        # 截取optimized_prompt中>>>和<<<之间的内容
        optimized_prompt = re.search(r'>>>(.*?)<<<', optimized_prompt, re.DOTALL).group(1).strip()
    except Exception as e:
        logging.error(f"优化提示词时出错：{e}")
        optimized_prompt = prompt
    
    logging.info(f"提示词优化完成，优化后的提示词：\n{optimized_prompt}\n")
    return optimized_prompt

def call_model(prompt):
    """
    调用代码模型生成代码的函数
    :param prompt: 优化后的提示词
    :return: 代码模型生成的代码
    """
    logging.info("开始与代码生成代码模型交互...")

    try:
        code_llm = QianfanLLMEndpoint(model='Mixtral-8x7B-Instruct')

        code_role_prompt = "你是一位专业精湛的 Python 代码开发大师，在数据加工处理领域拥有深厚造诣与丰富经验，能够精准高效地运用 Python 语言进行各类复杂数据加工任务的代码编写与优化。请根据以下提示词生成Python代码：\n\n"
        full_prompt = code_role_prompt + prompt
        logging.info(f"代码模型交互的完整提示词：\n{full_prompt}\n")    

        prompt_template = PromptTemplate.from_template(full_prompt)
        chain = LLMChain(llm=code_llm, prompt=prompt_template)
        response = chain.invoke({})
        code = response['text']
        logging.info(f"代码模型生成的完整内容：\n{code}\n")

        # 提取代码部分
        code_match = re.search(r'```python(.*?)```', code, re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
            logging.info(f"提取的代码部分：\n{code}\n")
        else:
            logging.warning("未找到代码部分，返回代码模型生成的完整内容。")
            code = response['text']

        logging.info(f"代码模型返回的内容（清理前）：\n{code}\n")

        # 清理可能存在的非法字符（如中文标点等）
        code = ''.join(char for char in code if ord(char) < 128)
        logging.info(f"代码模型返回的内容（清理后）：\n{code}\n")

        logging.info("与代码模型交互完成。")
        return code
    except Exception as e:
        logging.error(f"与代码模型交互时出错：{e}")
        return "与代码模型交互时出错，请检查网络连接或模型配置。"

def execute_code(code, dataframes):
    """
    执行代码模型生成的代码的函数
    :param code: 代码模型生成的代码
    :param dataframes: 源数据文件的数据框字典
    :return: 执行代码后的结果
    """
    code = textwrap.dedent(code)
    logging.info("开始执行代码模型生成的代码...")

    try:
        # 将数据框字典转换为本地变量
        locals().update(dataframes)

        # 执行代码
        exec(code, globals(), locals())

        # 获取执行结果
        result = locals().get('result', None)
        logging.info("代码执行完成，得到结果。")
        return result
    except Exception as e:
        logging.error(f"执行代码时出错：{e}")
        return "执行代码时出错，请检查代码或 dataframes是否正确。"

def save_result(result, template_file_path):
    """
    将结果保存到模板文件的函数
    :param result: 执行代码后的结果
    :param template_file_path: 模板文件路径
    :return: 无
    """
    logging.info("开始保存结果到模板文件...")
    if isinstance(result, pd.DataFrame):
        df = result
    else:
        try:
            df = pd.DataFrame(result)
        except Exception as e:
            logging.error(f"无法将结果转换为 DataFrame：{e}")
            return "无法将结果转换为 DataFrame，请检查代码执行结果。"

    output_file_name = os.path.splitext(template_file_path)[0] + '_output.xlsx'
    df.to_excel(output_file_name, index=False, engine='openpyxl')
    logging.info(f"结果已成功保存到 {output_file_name}。")
    return output_file_name

# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# 智能报表")
    with gr.Row():
        with gr.Column():
            source_files_upload = gr.File(file_count="multiple", label="上传源数据文件")
            template_file_upload = gr.File(file_count="single", label="上传输出文件模板")
            prompt_input = gr.Textbox(lines=5, label="输入提示词")
            process_button = gr.Button("生成报表")

            def handle_process(prompt, source_files, template_file):
                source_files_paths = upload_source_files(source_files)
                template_file_path = upload_template_file(template_file)
                return process_files(prompt, source_files_paths, template_file_path)

            process_button.click(handle_process, inputs=[prompt_input, source_files_upload, template_file_upload], outputs=gr.File(label="输出文件"))

# 启动Gradio应用
demo.launch()