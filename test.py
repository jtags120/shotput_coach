import time

one_morbillion = 1_000_000
while True:
    print(float(time.perf_counter_ns()) / one_morbillion)