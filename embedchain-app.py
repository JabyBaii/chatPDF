import os
from embedchain import App
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

_bot = App()

# 添加不同的数据源
_bot.add("https://en.wikipedia.org/wiki/Elon_Musk")
_bot.add("https://www.forbes.com/profile/elon-musk")
_bot.add("https://en.wikipedia.org/wiki/OpenAI")
# 添加本地数据源，例如pdf、csv文件等。
# _bot.add("/path/to/file.pdf")

# 查询
response = _bot.query("埃隆·马斯克今天的净资产是多少？")
print(response)
# 答：埃隆·马斯克如今的净资产是3037亿美元。
response = _bot.query("OpenAI 是一家怎样的公司？")
print(response)