FROM python:3.12
WORKDIR /app
COPY source-code /app/source-code
RUN pip install -r requirements.txt
CMD ["python", "/app/main.py"]