FROM python:3.13

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./shortener_app /app

EXPOSE 8000
CMD ["uvicorn", "app.shortener_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
