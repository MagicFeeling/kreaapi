FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY train.py infer.py find_unsafe.py get_styles.py ./

CMD ["sh", "-c", "python ${SCRIPT}"]
