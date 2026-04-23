# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Install necessary libraries for data analysis
RUN pip install --no-cache-dir pandas matplotlib seaborn numpy

# Create a directory for outputs (graphs)
RUN mkdir -p /app/exports/figures

# This container will wait for code execution commands via standard input or volume mounts
# For now, we'll keep it simple: it runs a script and exits.
CMD ["python"]
