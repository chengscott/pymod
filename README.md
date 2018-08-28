# pymod

## Installation

```shell
pip install pymod
```

### config search path

1. `/usr/local/etc/pymod`
2. ` ~/.config/pymod`
3. `.`

## Usage

### shell

- invoke shell function under `profile.d`

```shell
pymod info
pymod use cuda cudnn
```

### direct

- take advantage of command substitution

#### bash

```shell
$(pymod use cuda cudnn)
```

#### fish

```shell
eval (pymod use cuda cudnn)
```
