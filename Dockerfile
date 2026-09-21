FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wpt/ wpt/

USER 10001
CMD ["python", "-c", "from wpt.parameter_observer import PrimarySideObserver; print('WPT Resonant Observer Online.')"]