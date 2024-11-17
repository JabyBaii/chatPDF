from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

def openai_one_chat():
    llm = ChatOpenAI(model="gpt-4o-mini")  # 默认是gpt-3.5-turbo
    response = llm.invoke("你是谁")
    print(response.content)

def openai_multi_chat():
    from langchain.schema import (
        AIMessage,  # 等价于OpenAI接口中的assistant role
        HumanMessage,  # 等价于OpenAI接口中的user role
        SystemMessage  # 等价于OpenAI接口中的system role
    )

    llm = ChatOpenAI(model="gpt-4o-mini")  # 默认是gpt-3.5-turbo

    messages = [
        SystemMessage(content="你是一个AI助手，你叫小小助手。"),
        HumanMessage(content="我是小明，我今年18岁。"),
        AIMessage(content="欢迎！"),
        HumanMessage(content="我今年几岁？")
    ]

    ret = llm.invoke(messages)
    print(ret.content)

def qianfan_chat():
    # 其它模型分装在 langchain_community 底包中
    from langchain_community.chat_models import QianfanChatEndpoint
    from langchain_core.messages import HumanMessage
    import os

    llm = QianfanChatEndpoint(
        qianfan_ak=os.getenv('ERNIE_CLIENT_ID'),
        qianfan_sk=os.getenv('ERNIE_CLIENT_SECRET')
    )

    messages = [
        HumanMessage(content="介绍一下你自己")
    ]

    ret = llm.invoke(messages)

    print(ret.content)

# 自定义模板变量
def costom_template_variables():
    from langchain.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI

    # 定义 LLM
    llm = ChatOpenAI()

    template = PromptTemplate.from_template("给我讲个关于{subject}的笑话")
    print("===Template===")
    print(template)
    print("===Prompt===")
    print(template.format(subject='小明'))

    # 通过 Prompt 调用 LLM
    ret = llm.invoke(template.format(subject='小明'))
    # 打印输出
    print(ret.content)

# 自定义模板上下文
def custom_template_context():
    from langchain.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        SystemMessagePromptTemplate,
    )
    from langchain_openai import ChatOpenAI

    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template("你是{product}的客服助手。你的名字叫{name}"),
            HumanMessagePromptTemplate.from_template("{query}"),
        ]
    )

    llm = ChatOpenAI()
    prompt = template.format_messages(
        product="学习帮",
        name="小A",
        query="你是叫什么名字"
    )

    print(prompt)

    ret = llm.invoke(prompt)

    print(ret.content)

# 多轮对话变成模板
def custom_template_message_placeholder():
    from langchain.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        MessagesPlaceholder,
    )
    from langchain_core.messages import AIMessage, HumanMessage

    llm = ChatOpenAI(model="gpt-4o-mini")  # 默认是gpt-3.5-turbo

    # 构建用户问题
    human_prompt = "Translate your answer to {language}."
    human_message_template = HumanMessagePromptTemplate.from_template(human_prompt)

    chat_prompt = ChatPromptTemplate.from_messages(
        # variable_name 是 message placeholder 在模板中的变量名
        # 用于在赋值时使用
        [MessagesPlaceholder("history"), human_message_template]
    )

    # 一轮历史对话
    human_message = HumanMessage(content="Who is Elon Musk?")
    ai_message = AIMessage(
        content="Elon Musk is a billionaire entrepreneur, inventor, and industrial designer"
    )

    # 历史对话构建成模板
    messages = chat_prompt.format_prompt(
        # 对 "history" 和 "language" 赋值
        history=[human_message, ai_message], language="中文"
    )

    print("历史对话模板：\n", messages.to_messages())
    # [HumanMessage(content='Who is Elon Musk?', additional_kwargs={}, response_metadata={}), 
    # AIMessage(content='Elon Musk is a billionaire entrepreneur, inventor, and industrial designer', 
    # additional_kwargs={}, response_metadata={}), 
    # HumanMessage(content='Translate your answer to 中文.', additional_kwargs={}, 
    # response_metadata={})]

    # 调用 LLM
    result = llm.invoke(messages)
    print("调用LLM结果：\n", result.content)

if __name__ == "__main__":
    custom_template_message_placeholder()