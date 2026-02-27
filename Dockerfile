FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY train.py infer.py find_unsafe.py get_styles.py ./

RUN useradd -m -u 1000 dummyuser && chown -R dummyuser /app
USER dummyuser

CMD ["sh", "-c", "python ${SCRIPT}"]
