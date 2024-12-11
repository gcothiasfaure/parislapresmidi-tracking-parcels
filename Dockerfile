FROM python:3.12
COPY source-code /app/source-code
WORKDIR /app/source-code
RUN mkdir /app/output
RUN pip install -r requirements.txt
CMD ["python", "main.py"]