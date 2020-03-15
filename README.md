# Kernel Profiler

Profile top public kernels on Kaggle.

## Creating a development environment

```bash
conda create -n <env_name> python=3.7
conda activate <env_name>

pip install -r requirements.txt -r requirements-dev.txt
```

## How to run

```bash
python entrypoint.py -m titanic
```

## Code style

```bash
flake8 .
black --check .
```
