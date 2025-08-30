# Dockerfile

# --- Stage 1: Build Stage ---
# Use an official Python runtime as a parent image
FROM python:3.10-slim as builder

# Set the working directory in the container
WORKDIR /app

# Prevent python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# Install build dependencies
RUN pip install --upgrade pip

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# --- Stage 2: Final Stage ---
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from the wheels, which is faster
RUN pip install --no-cache-dir /wheels/*

# Copy the entire application source code
COPY . .

# Expose the port the app runs on (FastAPI's default is 8000)
EXPOSE 8000

# The default command to run the app.
# We will override this in Dokploy to include migrations.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
