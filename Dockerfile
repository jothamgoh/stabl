FROM python:slim

RUN useradd stabl

WORKDIR /home/stabl

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY stabl.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP stabl.py
ENV FLASK_ENV=development

RUN chown -R stabl:stabl ./
USER stabl

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]