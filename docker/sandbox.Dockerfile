FROM python:3.11-slim

WORKDIR /app

COPY ReActX/sandbox/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY reliability_harness/sandbox /app/reliability_harness/sandbox

ENV PYTHONPATH=/app

CMD ["uvicorn", "reliability_harness.sandbox.main:app", "--host", "0.0.0.0", "--port", "9000"]
