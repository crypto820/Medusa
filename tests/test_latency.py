import pytest
import time
import requests

_TARGET_URL = "https://fapi.binance.com/fapi/v1/time"
_TEST_TIMES = 50


def test_lantency():
    latency_list = []
    for _ in range(_TEST_TIMES):
        start = time.perf_counter()
        try:
            res = requests.get(_TARGET_URL)
        except Exception as e:
            print(e)
            print(f"error, timeout = {time.perf_counter() - start}")
        latency_list.append(time.perf_counter() - start)
    latency_list.sort()
    print(latency_list)
    

if __name__ == '__main__':
    pytest.main()
