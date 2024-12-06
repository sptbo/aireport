import gradio as gr
from upload import upload_source_files, upload_template_file
from main import process_files

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