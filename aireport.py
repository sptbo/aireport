import os
import logging
import gradio as gr
import pandas as pd
import unicodedata
import re
import textwrap
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import QianfanLLMEndpoint

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局变量
UPLOADED_FILES = []
SOURCE_FILES = []
TEMPLATE_FILE = None
PROMPT = ""
COLLECTED_INFO = {}  # 用于统一收集信息的字典

# 设置凭证信息
os.environ["QIANFAN_AK"] = "JRLvQvdUbRXWtYG1hKmbrkwY"
os.environ["QIANFAN_SK"] = "RhFqbIO1tDTEgzpEIkqHKa4LpQOQu1vq"


def save_uploaded_file(file):
    """
    保存上传的文件到当前目录
    :param file: 上传的文件对象
    :return: 保存后的文件路径
    """
    current_path = os.getcwd()
    file_path = os.path.join(current_path, file.name)
    with open(file_path, 'wb') as f:
        f.write(file.data)
    return file_path


def upload_source_files(files):
    """
    上传源数据文件的函数
    :param files: 要上传的文件列表
    :return: 上传结果提示信息
    """
    logging.info("开始上传源数据文件...")
    global SOURCE_FILES
    for file in files:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension in ['.xls', '.xlsx', '.csv']:
            file_path = save_uploaded_file(file)
            if any(file_path == f for f in SOURCE_FILES):
                logging.warning("文件名相同，不能上传。")
                return "文件名相同，不能上传。"
            try:
                # 尝试读取文件，检查文件是否可正常读取
                if file_extension == '.csv':
                    pd.read_csv(file_path)
                elif file_extension in ['.xls', '.xlsx']:
                    pd.read_excel(file_path)
                SOURCE_FILES.append(file_path)
            except Exception as e:
                logging.error(f"读取文件 {file_path} 时出错：{e}")
                return f"读取文件 {file_path} 时出错，请检查文件是否正确。"
        else:
            logging.warning(f"不支持的文件类型：{file_extension}")
            return f"不支持的文件类型：{file.extension}"
    logging.info("源数据文件上传成功。")


def upload_template_file(file):
    """
    上传模板文件的函数
    :param file: 要上传的文件
    :return: 上传结果提示信息
    """
    logging.info("开始上传模板文件...")
    global TEMPLATE_FILE
    file_extension = os.path.splitext(file.name)[1]
    if file_extension in ['.xls', '.xlsx', '.csv']:
        file_path = save_uploaded_file(file)
        try:
            # 尝试读取文件，检查文件是否可正常读取
            if file_extension == '.csv':
                pd.read_csv(file_path)
            elif file_extension in ['.xls', '.xlsx']:
                pd.read_excel(file_path)
            TEMPLATE_FILE = file_path
            logging.info("模板文件上传成功。")
            COLLECTED_INFO['template_file'] = file_path  # 直接将模板文件路径存入收集信息的字典
            return "模板文件上传成功。"
        except Exception as e:
            logging.error(f"读取文件 {file_path} 时出错：{e}")
            return f"读取文件 {file_path} 时出错，请检查文件是否正确。"
    else:
        logging.warning(f"不支持的模板文件类型。")
        return "不支持的模板文件类型。"


def collect_info():
    """
    统一收集信息的函数，在点击提交键后被触发
    :return: 无，将信息收集到全局变量COLLECTED_INFO中
    """
    global COLLECTED_INFO, SOURCE_FILES, TEMPLATE_FILE, PROMPT
    COLLECTED_INFO['source_files'] = SOURCE_FILES
    COLLECTED_INFO['template_file'] = TEMPLATE_FILE
    logging.info("信息收集完成。")


def process_files(prompt):
    """
    处理文件的主函数，使用统一收集的信息进行处理，包括读取源数据文件、优化提示词、调用大模型生成代码、执行代码并保存结果
    :return: 结果文件路径以便下载或错误提示信息
    """
    global COLLECTED_INFO
    logging.info("开始处理文件...")

    try:
        # 确认源数据文件路径并读取源数据文件
        source_files = []
        for file_path in COLLECTED_INFO['source_files']:
            file_extension = os.path.splitext(file_path)[1]
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
                logging.info(f"成功读取CSV文件 {file_path}")
            elif file_extension in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
                logging.info(f"成功读取Excel文件 {file_path}")
            source_files.append(df)

        # 确认模板文件路径
        template_file_path = COLLECTED_INFO.get('template_file')
        if not template_file_path:
            logging.error("未上传模板文件，请上传后再试。")
            return "未上传模板文件，请上传后再试。"

        # 再次确认模板文件是否可读取
        try:
            file_extension = os.path.splitext(template_file_path)[1]
            if file_extension == '.csv':
                pd.read_csv(template_file_path)
            elif file_extension in ['.xls', '.xlsx']:
                pd.read_excel(template_file_path)
        except Exception as e:
            logging.error(f"读取模板文件 {template_file_path} 时出错：{e}")
            return "读取模板文件时出错，请检查文件是否正确。"

        # 优化提示词
        global PROMPT
        PROMPT = prompt

        if not PROMPT:
            logging.error("提示词未设置，请先设置提示词再处理文件。")
            return "提示词未设置，请先设置提示词再处理文件。"
        optimized_prompt = optimize_prompt(PROMPT)
        logging.info("提示词优化完成。")

        # 调用大模型生成代码
        try:
            code = call_model(optimized_prompt)
            logging.info("大模型生成代码完成。")
        except Exception as e:
            logging.error(f"调用大模型生成代码时出错：{e}")
            return "调用大模型生成代码时出错，请检查网络或模型设置。"

        # 执行代码生成结果
        try:
            result = execute_code(code, source_files)
            logging.info("代码执行完成，得到结果。")
        except Exception as e:
            logging.error(f"执行代码生成结果时出错：{e}")
            return "执行代码生成结果时出错，请检查代码或数据是否正确。"

        # 按照用户指令将结果写到模板文件的相应位置
        save_result(result, template_file_path)
        logging.info("结果已保存到模板文件。")

        # 返回结果文件路径以便下载
        return template_file_path
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
        1.优化的目标在于使得大模型能够凭借优化后的提示词，精准无误地编写出可完成特定数据处理任务的 Python 代码。
        2.要充分考虑到数据处理任务的各个细节以及 Python 编程的规范与高效性要求，确保大模型能准确理解并生成符合预期的代码逻辑。
        3.优化后的提示词步骤清晰，包含所有必要的信息，并遵循 Python 编程的最佳实践。
        4.只输出优化后的提示词，不要输出任何解释或说明。
        """
    
    logging.info(f"优化前的提示词模板：\n{full_prompt}\n")

    logging.info("开始优化提示词...")
    try:
        prompt_template = PromptTemplate.from_template(full_prompt)
        chain = LLMChain(llm=llm, prompt=prompt_template)
        optimized_prompt = chain.run({})['text']
    except Exception as e:
        logging.error(f"优化提示词时出错：{e}")
        optimized_prompt = prompt

    logging.info(f"提示词优化完成，优化后的提示词：\n{optimized_prompt}\n")
    return optimized_prompt


def call_model(prompt):
    """
    调用大模型生成代码的函数
    :param prompt: 优化后的提示词
    :return: 大模型生成的代码
    """
    logging.info("开始与代码生成大模型交互...")

    try:
        code_llm = QianfanLLMEndpoint(model='Mixtral-8x7B-Instruct')

        code_role_prompt = "你是一位专业精湛的 Python 代码开发大师，在数据加工处理领域拥有深厚造诣与丰富经验，能够精准高效地运用 Python 语言进行各类复杂数据加工任务的代码编写与优化。注意生成代码的格式。"

        full_prompt = code_role_prompt + prompt

        prompt_template = PromptTemplate.from_template(full_prompt)
        chain = LLMChain(llm=code_llm, prompt=prompt_template)
        response = chain.invoke({})
        code = response['text']

        # 提取代码部分
        code = re.search(r'```python(.*?)```', code, re.DOTALL)
        if code:
            code = code.group(1).strip()
        else:
            logging.warning("未找到代码部分，返回原始响应内容。")
            code = response['text']

        logging.info(f"大模型生成的代码：\n{code}\n")

        # 清理可能存在的非法字符（如中文标点等）
        code = ''.join(char for char in code if ord(char) < 128)

        # 将文件路径替换为当前目录下的路径
        current_path = os.getcwd()
        for file_path in COLLECTED_INFO['source_files'] + [COLLECTED_INFO['template_file']]:
            relative_path = os.path.relpath(file_path, current_path)
            code = code.replace(file_path, relative_path)

        logging.info("与大模型交互完成。")
        return code
    except Exception as e:
        logging.error(f"与大模型交互时出错：{e}")
        return "与大模型交互时出错，请检查网络连接或模型配置。"


def execute_code(code, dataframes):
    """
    执行大模型生成的代码的函数
    :param code: 大模型生成的代码
    :param dataframes: 源数据文件的数据框字典
    :return: 执行代码后的结果
    """
    code = textwrap.dedent(code)
    logging.info("开始执行大模型生成的代码...")

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
        df = pd.DataFrame(result)
    output_file_name = os.path.splitext(template_file_path)[0] + '_output.xlsx'
    df.to_excel(output_file_name, index=False)
    logging.info("结果已成功保存到模板文件。")

# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# 人造人一号")
    with gr.Row():
        with gr.Column():
            source_files_upload = gr.File(file_count="multiple", label="上传源数据文件")
            source_files_upload.upload(upload_source_files, source_files_upload, show_progress=True)
            template_file_upload = gr.File(file_count="single", label="上传输出文件模板")
            template_file_upload.upload(upload_template_file, template_file_upload, show_progress=True)
            prompt_input = gr.Textbox(lines=5, label="输入提示词")
            process_button = gr.Button("生成报表")
            process_button.click(collect_info, show_progress=True)  # 点击按钮先统一收集信息
            process_button.click(process_files, prompt_input, show_progress=True, outputs=gr.File(label="输出文件"))

# 启动Gradio应用
demo.launch()