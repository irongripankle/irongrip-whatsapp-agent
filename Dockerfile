FROM python:3.12-slim

WORKDIR /app

COPY irongrip_whatsapp_agent.py .

RUN pip install --no-cache-dir flask twilio

ENV PORT=5000

EXPOSE 5000

CMD ["python", "irongrip_whatsapp_agent.py"]
