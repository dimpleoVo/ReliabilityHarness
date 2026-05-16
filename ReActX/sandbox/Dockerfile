FROM python:3.11-slim

WORKDIR /app

# 只安装 Python 依赖（不装 docker CLI）
COPY sandbox/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 拷贝 sandbox 服务代码
COPY sandbox /app/sandbox

ENV PYTHONPATH=/app

# 启动 sandbox service
CMD ["uvicorn", "sandbox.main:app", "--host", "0.0.0.0", "--port", "9000"]