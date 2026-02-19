FROM python:3.11-slim

WORKDIR /app

# Copy requirements from root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything into the container
COPY . .

# Ensure Python looks inside the /app/app folder for modules
ENV PYTHONPATH=/app/app

# Run the script located inside the app folder
CMD ["python", "app/btc_data_collector.py"]