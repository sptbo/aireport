import logging
import re
import time
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import QianfanLLMEndpoint
from config_loader import config

def call_model(prompt):
    """
    调用代码模型生成代码的函数
    :param prompt: 优化后的提示词
    :return: 代码模型生成的代码
    """
    logging.info("开始与代码生成代码模型交互...")

    try:
        code_qf = QianfanLLMEndpoint(model=config['model']['name'])
        
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

            code_match = re.search(r'```python(.*?)```', code, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                logging.info(f"提取的代码部分：\n{code}\n")
                break
            else:
                logging.warning(f"尝试 {attempt + 1}/{max_retries}: 未找到代码部分，重新生成代码。")
                time.sleep(10)

        if not code_match:
            logging.error("无法生成符合要求的代码。")
            return "无法生成符合要求的代码。"

        code = code.replace('，', ',').replace('。', '.').replace('！', '!').replace('？', '?').replace('；', ';').replace('：', ':').replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'").replace('（', '(').replace('）', ')').replace('【', '[').replace('】', ']').replace('《', '<').replace('》', '>').replace('、', '')
        logging.info(f"代码模型返回的内容（清理后）：\n{code}\n")
        logging.info("与代码模型交互完成。")
        return code
    except Exception as e:
        logging.error(f"与代码模型交互时出错：{e}")
        return "与代码模型交互时出错，请检查网络连接或模型配置。"