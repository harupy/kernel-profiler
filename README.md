# Kernel Profiling

A Python script to profile top public kernels on Kaggle.

## Setup

Download ChromeDriver [here](https://chromedriver.chromium.org).

## How to run

```bash
# clone the repo.
git clone https://github.com/harupy/kernel-profiling
cd kernel-profiling

# copy chromedriver
mv /path/to/chromedriver .

# Install pipenv (optional).
pip install pipenv

# Install dependencies.
pipenv install

# Activate the pipenv shell.
pipenv shell

# Run the script.
python profile_kernels.py -c titanic

# Result will be written to "result.md"
```
