FROM python:3.8
LABEL maintainer="alance@uoregon.edu"
COPY . /website
WORKDIR /website
RUN pip install -r requirements.txt
CMD ["python", "website.py"]
