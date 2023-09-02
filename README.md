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
usage: __main__.py [-h] -o OUTPUT [--backend BACKEND]

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
  --backend BACKEND, default to glider
```
## Config Template
```yaml
subscriptions:
  - https://your-proxy-subscription-url
  - ...
```