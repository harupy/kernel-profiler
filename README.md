# Kernel Profiler

![Upload](https://github.com/harupy/kernel-profiler/workflows/Upload/badge.svg)

Profile top scoring public kernels on Kaggle.

## How to create a development environment

```bash
conda create -n <env_name> python=3.7
conda activate <env_name>

pip install -r requirements.txt -r requirements-dev.txt
```

## How to run

```bash
python entrypoint.py -c titanic
```

## Lint

```bash
flake8 .
black --check .
```
