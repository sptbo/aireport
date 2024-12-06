import os
import logging
import time
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
    source_file_paths = []
    for file in files:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension in ['.xls', '.xlsx', '.csv']:
            try:
                # 尝试读取文件，检查文件是否可正常读取
                if file_extension == '.csv':
                    df = pd.read_csv(file.name)
                elif file_extension in ['.xls', '.xlsx']:
                    df = pd.read_excel(file.name, engine='openpyxl')  # 手动指定引擎
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
        # 确认源数据文件路径并读取源数据文件
        dataframes = []
        for file_path in source_file_paths:
            file_extension = os.path.splitext(file_path)[1]
            try:
                if file_extension == '.csv':
                    df = pd.read_csv(file_path)
                elif file_extension in ['.xls', '.xlsx']:
                    df = pd.read_excel(file_path, engine='openpyxl')  # 手动指定引擎
                dataframes.append(df)
            except Exception as e:
                logging.error(f"读取文件 {file_path} 时出错：{e}")
                return f"读取文件 {file_path} 时出错，请检查文件是否正确。"

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

        # 将上传文件的路径和文件名包含在提示词中
        prompt_with_files = f"{prompt}\n\n源数据文件路径：{source_file_paths}\n模板文件路径：{template_file_path}"
        optimized_prompt = optimize_prompt(prompt_with_files)
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
            result = execute_code(code, dataframes, source_file_paths, template_file_path)
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

    full_prompt = f"""你身为大模型提示词领域的专家以及精通 Python 语言编程的专家，请对>>>和<<<间的用户提示词进行优化处理：
        >>>
        {prompt}
        <<<
        
        要求如下：
        1.优化的目标在于使大模型能够凭借优化后的提示词精准无误地编写出可完成特定数据处理任务的 Python 代码。
        2.要充分考虑到数据处理任务的各个细节以及 Python 编程的规范与高效性要求，确保大模型能准确理解并生成符合预期的代码逻辑。
        3.优化后的提示词步骤清晰，包含所有必要的信息，并遵循 Python 编程的最佳实践。
        4.只对>>>与<<<之间的内容进行优化,注意不要遗漏内容。
        5.确保文件路径完整可用，不要使用“...”等省略。
        6.保留“源数据文件路径”和“模板文件路径”。
        7.只对提示词的表述方式进行优化，不要生成代码或示例代码。
        8.只返回>>>与<<<之间优化的内容，保留">>>"和"<<<"符号，不要返回其他任何内容。
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
        code_match = re.search(r'>>>(.*?)<<<', optimized_prompt, re.DOTALL)
        if code_match:
            optimized_prompt = code_match.group(1).strip()
        else:
            logging.warning("未找到优化后的提示词内容，使用原始提示词。")
            optimized_prompt = prompt
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
        # code_qf = QianfanLLMEndpoint(model='Mixtral-8x7B-Instruct')
        code_qf = QianfanLLMEndpoint(model='ERNIE-4.0-8K')
        

        code_role_prompt = f"""
        你是一位专业精湛的 Python 代码开发大师，在数据加工处理领域拥有深厚造诣与丰富经验。能够精准高效地运用 Python 语言进行各类复杂数据加工任务的代码编写与优化。
        请根据以下提示词生成Python代码：
            \n{prompt}\n
            
        要求如下：
            -.只保留提示词中与生成代码有关的内容，忽略其他内容。   
            -.生成的代码应能准确完成提示词中描述的数据加工任务。
            -.生成的代码应遵循 Python 编程的最佳实践，确保代码的可读性、可维护性和高效性。
            -.生成的代码应尽量简洁和完整，避免冗余和不必要的复杂度。
            -.生成的代码不要包含 Python 无法处理的字符。
            -.生成的代码中不要包含任何恶意代码或后门。
            -.生成的代码中不要包含任何违反法律法规的内容。
            -.只生成代码，全部完整的代码以```python开头，以```结尾，不要生成其他任何内容。
            -.注意生成的代码能够正确打开、读取、处理和保存文件，不要生成无法运行的代码。
            -.不要生成过时的代码。
            -.使用绝对路径，不要使用相对路径。
            -.注意转义字符的正确使用。比如路径使用"\\"而不是"\"。
            -.生成的代码中使用半角符号，不要使用全角符号。
            -.生成代码后，反思和检查生成代码是否正确、完整（```python和```是否完整），是否符合以上要求。如果有问题，重新生成。每次生成后都需要对代码进行反思和检查。如果尝试5次后仍然不能生成正确代码，则返回“无法生成符合要求的代码。”。
            
            
            以下是代码是否生成完整的示例：
                代码生成完整示例（正确）：
                    ```python
                    import pandas as pd

                    # 读取表 1 和 表 2
                    table1 = pd.read_excel(r'C:\\Users\\Administrator\\AppData\\Local\\Temp\\gradio\\2ebff9572c1be998c7a33a376837075a278dddc11f03c39427bbd7cb44287bc0\\1.xlsx')
                    table2 = pd.read_excel(r'C:\\Users\\Administrator\\AppData\\Local\\Temp\\gradio\\2e20a0abe51bb10fede921bf3c9c3cfab7088e668351f2cdd319b7f5436a1f51\\2.xlsx')

                    # 以姓名作为关键列进行关联整合
                    merged_table = pd.merge(table1, table2, on='姓名', how='inner')

                    # 计算最终工资
                    merged_table['最终工资'] = merged_table['工资系数'] * merged_table['基本工资']

                    # 将结果保存到输出表
                    output_path = r'C:\\Users\\Administrator\\AppData\\Local\\Temp\\gradio\\347ef12beb97a6473346d5ac100a0930ff8abe74c631887f38d5e0be2bb77fd8\\out.xlsx'
                    merged_table.to_excel(output_path, index=False)
                    ```
            
                代码生成不完整示例（错误）：
                    ```python
                    import pandas as pd
        """
        logging.info(f"代码模型交互的完整提示词：\n{code_role_prompt}\n")    

        prompt_template = PromptTemplate.from_template(code_role_prompt)
        chain = LLMChain(llm=code_qf, prompt=prompt_template)

        max_retries = 5
        for attempt in range(max_retries):
            response = chain.invoke({})
            code = response['text']
            logging.info(f"代码模型生成的完整内容：\n{code}\n")

            # 提取代码部分
            code_match = re.search(r'```python(.*?)```', code, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                logging.info(f"提取的代码部分：\n{code}\n")
                break
            else:
                logging.warning(f"尝试 {attempt + 1}/{max_retries}: 未找到代码部分，重新生成代码。")
                # sleep 10 秒
                time.sleep(10)

        if not code_match:
            logging.error("无法生成符合要求的代码。")
            return "无法生成符合要求的代码。"

        # 将全角标点替换为半角。
        code = code.replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?').replace('；', ';').replace('：', ':').replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'").replace('（', '(').replace('）', ')').replace('【', '[').replace('】', ']').replace('《', '<').replace('》', '>').replace('、', '')
        logging.info(f"代码模型返回的内容（清理后）：\n{code}\n")
        logging.info("与代码模型交互完成。")
        return code
    except Exception as e:
        logging.error(f"与代码模型交互时出错：{e}")
        return "与代码模型交互时出错，请检查网络连接或模型配置。"

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
        # 将数据框字典转换为本地变量
        locals().update(dataframes)

        # 替换代码中的文件路径
        for i, file_path in enumerate(source_file_paths):
            code = code.replace(f"'{i+1}.xlsx'", f"'{file_path}'")
        code = code.replace("'out.xlsx'", f"'{template_file_path}'")

        # 执行代码
        exec(code, globals(), locals())

        # 获取执行结果
        result = locals().get('merged_table', None)  # 假设生成的代码中将结果存储在 merged_table 变量中
        if result is None:
            logging.warning("代码执行后未找到结果，请检查代码是否正确赋值给 merged_table 变量。")
            return "代码执行后未找到结果，请检查代码是否正确赋值给 merged_table 变量。"

        logging.info(f"代码执行完成，得到结果:\n{result}\n")
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
    # logging.info("开始保存结果到模板文件...")
    # if isinstance(result, pd.DataFrame):
    #     df = result
    # else:
    #     try:
    #         df = pd.DataFrame(result)
    #     except Exception as e:
    #         logging.error(f"无法将结果转换为 DataFrame：{e}")
    #         return "无法将结果转换为 DataFrame，请检查代码执行结果。"

    output_file_name = os.path.splitext(template_file_path)[0] + '.xlsx'
    # try:
    #     with pd.ExcelWriter(output_file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    #         df.to_excel(writer, sheet_name='Sheet1', index=False)
    #         writer.close()
    # except FileNotFoundError:
    #     logging.error(f"文件 {output_file_name} 不存在，尝试创建文件。")
    #     df.to_excel(output_file_name, index=False, engine='openpyxl')

    # logging.info(f"结果已成功保存到 {output_file_name}。")
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
                source_file_paths = upload_source_files(source_files)
                template_file_path = upload_template_file(template_file)
                return process_files(prompt, source_file_paths, template_file_path)

            process_button.click(handle_process, inputs=[prompt_input, source_files_upload, template_file_upload], outputs=gr.File(label="输出文件"))

# 启动Gradio应用
demo.launch()