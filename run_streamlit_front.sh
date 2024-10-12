# 启动前端
print_message "正在启动chroma客户端..."
if [[ "$OS" == "WINDOWS" ]]; then
    streamlit run .\chatPDF-ui.py &
else
    streamlit run ./chatPDF-ui.py &
fi