from http import HTTPStatus
import dashscope


messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': '请编写一个Python函数 find_prime_numbers，该函数接受一个整数 n 作为参数，并返回一个包含所有小于 n 的质数（素数）的列表。质数是指仅能被1和其自身整除的正整数，如2, 3, 5, 7等。请不要输出代码之外的内容。'}]
response = dashscope.Generation.call(
    model='qwen2.5-coder-32b-instruct',
    messages=messages,
    result_format='message',  
)
if response.status_code == HTTPStatus.OK:
    print(response.output.choices[0].message.content)
else:
    print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
        response.request_id, response.status_code,
        response.code, response.message
    ))