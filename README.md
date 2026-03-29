# Medusa
Medusa is a config generator for glider (https://github.com/nadoo/glider)
## Install
```shell
git clone git@github.com:philoinovsky/Medusa.git
pip3 install ./Medusa
```

## Usage
```shell
python3 -m medusa -h
usage: __main__.py [-h] -o OUTPUT [--backend BACKEND] [-c CONFIG] [--clash CLASH]

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
  --backend BACKEND
  -c CONFIG, --config CONFIG
  --clash CLASH
```
## Config
Default config path: `medusa/configs/config.yml`

Tracked demo config: `medusa/configs/config.example.yml`

Run the tracked demo config:
```shell
python3 -m medusa -o glider.conf -c config.example.yml
```

Generate `glider.conf` directly from a Clash config while still using `medusa/configs/glider_template.conf`:
```shell
python3 -m medusa -o glider.conf --clash clash.yaml
```

## Config Template
```yaml
subscriptions_base64:
  - |
    BASE64_ENCODED_SUBSCRIPTION
  - |
    ANOTHER_BASE64_ENCODED_SUBSCRIPTION
```

`subscriptions` 也可以继续用，但现在每一项必须是 base64 字符串，不再支持订阅 URL。
