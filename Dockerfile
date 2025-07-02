FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y git

RUN git clone https://github.com/Sophiehsin/mcp.git .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.baseUrlPath=smart-plan"]

USER 1000
