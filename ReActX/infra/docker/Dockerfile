FROM python:3.11-slim

WORKDIR /app

# 系统依赖（可选）
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements（你原本的）
COPY requirements.txt /app/requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制整个项目
COPY . /app

# 关键：让 Python 能找到 app
ENV PYTHONPATH=/app/ReActX
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 启动 backend
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]