FROM python:3.7.7

WORKDIR /kernel-profiler

RUN apt-get update

ENV PATH="/:${PATH}"

# Install Chrome.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list && \
    cat /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# Download chromedriver.
RUN CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && rm chromedriver_linux64.zip

# Volume will override the working directory and erase chromedriver.
# To avoid that, move it to the root.
RUN mv chromedriver /

# Install kerne-profiler and enable command line interface.
COPY . .
RUN pip install -e .

ENTRYPOINT profile
