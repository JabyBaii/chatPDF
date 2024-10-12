# 启动后端
print_message "正在启动chroma服务器..."
if [[ "$OS" == "WINDOWS" ]]; then
    chroma run --path ./chroma_db &
else
    chroma run --path ./chroma_db &
fi