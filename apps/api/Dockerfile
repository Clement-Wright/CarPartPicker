FROM python:3.13-slim

WORKDIR /workspace

COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

COPY apps/api /workspace/apps/api
COPY data /workspace/data

ENV PYTHONPATH=/workspace/apps/api

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

