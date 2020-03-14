FROM python:3.7.6

RUN apt-get update && apt-get install -y xvfb

ENV PATH="/:${PATH}"

# Install Chrome.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list && \
    cat /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# https://stackoverflow.com/questions/53902507/unknown-error-session-deleted-because-of-page-crash-from-unknown-error-cannot/53970825
RUN sudo mount -t tmpfs -o rw,nosuid,nodev,noexec,relatime,size=512M tmpfs /dev/shm


# Install Chrome Driver.
RUN CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && rm chromedriver_linux64.zip

# Install Python dependencies.
COPY ./requirements.txt .
COPY ./requirements-dev.txt .
RUN pip install -r requirements.txt -r requirements-dev.txt

COPY entrypoint.py /entrypoint.py
ENTRYPOINT python /entrypoint.py
