FROM python:3.12
COPY source-code /app/source-code
RUN mkdir /app/output
RUN pip install -r /app/source-code/requirements.txt
CMD ["python", "/app/source-code/main.py"]