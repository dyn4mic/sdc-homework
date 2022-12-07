FROM python:3.8
LABEL maintainer="markuspaasche"
# copy files from the host to the container filesystem. 
# For example, all the files in the current directory
# to the  `/app` directory in the container
COPY . /app
COPY ./openssl.cnf /etc/ssl/
#  defines the working directory within the container
WORKDIR /app
# run commands within the container. 
# For example, invoke a pip command 
# to install dependencies defined in the requirements.txt file. 
RUN pip install -r requirements.txt
# provide a command to run on container start. 
# For example, start the `app.py` application.
#CMD ["/bin/bash","./startup.sh"]
#CMD ["cat","/etc/ssl/openssl.cnf"]
CMD ["python","startup.py"]
