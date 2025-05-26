#!/usr/bin/env python3
"""
client_stats.py  –  benchmark 100 gRPC calls and summarise latency stats
"""

import time
import statistics as st
import grpc
from grpc import StatusCode
import calculator_pb2, calculator_pb2_grpc

SERVER_ADDR = "localhost:50051"     # change to LAN IP if needed
REQUESTS    = 100
TIMEOUT_SEC = 2                     # per‑call deadline (s)

def main() -> None:
    latencies_ms = []               # successful calls only
    failures     = 0

    with grpc.insecure_channel(SERVER_ADDR) as channel:
        stub = calculator_pb2_grpc.CalculatorStub(channel)

        for i in range(1, REQUESTS + 1):
            try:
                t0 = time.perf_counter()
                reply = stub.Add(
                    calculator_pb2.AddRequest(a=i, b=i), timeout=TIMEOUT_SEC
                )
                dt = (time.perf_counter() - t0) * 1_000  # → ms
                latencies_ms.append(dt)

            except grpc.RpcError as err:
                failures += 1
                code = err.code()
                # Optional: print per‑failure details
                print(f"[{i:03}]  RPC failed: {code.name} – {err.details()}")

    # ----- summary -----
    success = len(latencies_ms)
    print("\n=== RPC BENCHMARK SUMMARY ===")
    print(f"Target server      : {SERVER_ADDR}")
    print(f"Total requests     : {REQUESTS}")
    print(f"Successful replies : {success}")
    print(f"Failures           : {failures}")

    if success:
        print("\nLatency (ms) for successful calls:")
        print(f"  mean   : {st.mean(latencies_ms):7.2f}")
        print(f"  median : {st.median(latencies_ms):7.2f}")
        print(f"  min    : {min(latencies_ms):7.2f}")
        print(f"  max    : {max(latencies_ms):7.2f}")
        # 95th‑percentile, if ≥ 20 samples
        if success >= 20:
            p95 = st.quantiles(latencies_ms, n=100)[94]
            print(f"  95th % : {p95:7.2f}")

if __name__ == "__main__":
    main()
