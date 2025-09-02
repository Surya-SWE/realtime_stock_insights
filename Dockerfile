# 1. Use an official lightweight Python runtime as a parent image
FROM python:3.12-slim

# 2. Copy the application files into the container
COPY . .

# 3. Install uv, the fast Python package installer and resolver
RUN pip install uv

# 4. Create a virtual environment using uv and install dependencies
RUN uv venv

# 5. Install the required Python packages inside the virtual environment
RUN uv pip install --no-cache-dir -r requirements.txt

# 6. Make port 8080 available to the world outside this container
EXPOSE 8080

# 7. Define environment variable to ensure Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# 8. Run the application using the Python interpreter from the virtual environment
CMD [".venv/bin/python3.12", "-u", "app.py"]