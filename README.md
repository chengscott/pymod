# pymod

## Installation

```shell
pip install pymod
```

## Usage

- [pymod wiki](https://github.com/chengscott/pymod/wiki)

### Indirect (recommended)

- invoke shell function under `profile.d`

```shell
pymod info
pymod use cuda cudnn
```

### Direct

- take advantage of shell command substitution
  - `bash`: `$(pymod use cuda cudnn)`
  - `fish`: `eval (pymod use cuda cudnn)`

## Features

- search for packages

```bash
pymod info cud
# Did you mean cuda or cudnn or cuda9 ?
pymod info cuda
# Avaiable Package `cuda-10.0` (cuda)
```
