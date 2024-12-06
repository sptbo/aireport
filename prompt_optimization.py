import logging
import re
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import QianfanLLMEndpoint
from config_loader import config

def optimize_prompt(prompt):
    """
    优化提示词的函数，目前仅返回原提示词，可在此添加优化逻辑
    :param prompt: 原始提示词
    :return: 优化后的提示词
    """
    llm = QianfanLLMEndpoint(model=config['model']['name'])
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
        chain = prompt_template | llm
        x = chain.invoke({})
        optimized_prompt = x
        logging.info(f"提权>>> <<<前：\n{optimized_prompt}\n")
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