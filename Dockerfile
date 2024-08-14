# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app


# Copy the requirements file into the container
COPY backend/requirements.txt /app/requirements.txt

# Print the contents of requirements.txt
RUN cat /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend


COPY backend/prompt_templates.txt /app/backend/prompt_templates.txt


# Copy the entire project directory contents into the container at /app
COPY . /app


RUN mkdir -p /app/output

# List the contents of /app/backend to verify the copy
RUN ls -l /app/backend > /app/output/backend_contents.txt


# List the contents of /app to verify the copy
RUN ls -l /app/ > /app/output/app_contents.txt

#ENV PYTHONPATH=/app/backend

ENV OPENAI_API_KEY='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'
ENV AZURE_STORAGE_ACCOUNT_KEY="zmqOkCX2zsNeVktkutoi6w1l15jh09MQF3YclqwJaMu9vUsD9q45vWJ2OPyrwGXww4TkZOsfWE0u+AStIlrgGQ==" 


# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables
#ENV APP_MODULE=backend.main:app
ENV APP_MODULE=backend.dummymain:app
ENV ENVIRONMENT=production



# Run uvicorn server
#CMD ["uvicorn", "$APP_MODULE", "--host", "0.0.0.0", "--port", "80"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]

