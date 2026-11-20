FROM python:3.10.6-slim

COPY mastershelf /mastershelf
COPY models/best.pt /models/best.pt
COPY raw_data/recipes_clean.csv /raw_data/recipes_clean.csv
COPY requirements.txt /requirements.txt
COPY static /static
COPY setup.py /setup.py

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
libxcb1 \
libgl1 \
libglib2.0-0 \
&& rm -rf /var/lib/apt/lists/*

CMD uvicorn mastershelf.api.fast:app --host 0.0.0.0 --port 9000
