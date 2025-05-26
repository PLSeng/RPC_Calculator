#!/usr/bin/env python3
"""
Interactive gRPC client for the demo calculator service
"""

import time
import grpc
from grpc import StatusCode
import calculator_pb2 as pb
import calculator_pb2_grpc as rpc

SERVER_ADDR = "localhost:50051"   # change to LAN IP if needed
TIMEOUT_SEC = 2

# ───────────────────────── helpers ─────────────────────────
def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("  Please enter a valid integer.")

def print_menu() -> str:
    print("\nChoose an operation:")
    print(" 1) Add            (x + y)")
    print(" 2) Subtract       (x - y)")
    print(" 3) Multiply       (x * y)")
    print(" 4) Divide         (x / y)")
    print(" 5) Power          (x^n)")
    print(" 6) Factorial      (n!)")
    print(" q) Quit")
    return input("Your choice: ").strip().lower()

def show_latency(t0: float) -> None:
    dt_ms = (time.perf_counter() - t0) * 1_000
    print(f"  (round-trip ≈ {dt_ms:.2f} ms)")


# ───────────────────────── main ─────────────────────────
def main() -> None:
    try:
        with grpc.insecure_channel(SERVER_ADDR) as channel:
            stub = rpc.CalculatorStub(channel)

            while True:
                choice = print_menu()

                if choice == "q":
                    print("Bye!")
                    break

                try:
                    if choice == "1":       # Add
                        x = ask_int("  x = ")
                        y = ask_int("  y = ")
                        t0 = time.perf_counter()
                        rep = stub.Add(pb.BinaryRequest(x=x, y=y),
                                       timeout=TIMEOUT_SEC)
                        print(f"  Result: {rep.result}")
                        show_latency(t0)

                    elif choice == "2":     # Subtract
                        x = ask_int("  x = ")
                        y = ask_int("  y = ")
                        t0 = time.perf_counter()
                        rep = stub.Subtract(pb.BinaryRequest(x=x, y=y),
                                            timeout=TIMEOUT_SEC)
                        print(f"  Result: {rep.result}")
                        show_latency(t0)

                    elif choice == "3":     # Multiply
                        x = ask_int("  x = ")
                        y = ask_int("  y = ")
                        t0 = time.perf_counter()
                        rep = stub.Multiply(pb.BinaryRequest(x=x, y=y),
                                            timeout=TIMEOUT_SEC)
                        print(f"  Result: {rep.result}")
                        show_latency(t0)

                    elif choice == "4":     # Divide
                        x = ask_int("  dividend (x) = ")
                        y = ask_int("  divisor  (y) = ")
                        t0 = time.perf_counter()
                        rep = stub.Divide(pb.BinaryRequest(x=x, y=y),
                                          timeout=TIMEOUT_SEC)
                        print(f"  Quotient : {rep.quotient}")
                        print(f"  Remainder: {rep.remainder}")
                        show_latency(t0)

                    elif choice == "5":     # Power
                        base = ask_int("  base     = ")
                        exp  = ask_int("  exponent = ")
                        t0 = time.perf_counter()
                        rep = stub.Power(pb.PowerRequest(base=base,
                                                         exponent=exp),
                                         timeout=TIMEOUT_SEC)
                        print(f"  Result: {rep.result}")
                        show_latency(t0)

                    elif choice == "6":     # Factorial (server-streaming)
                        n = ask_int("  n = ")
                        t0 = time.perf_counter()
                        print("  Streaming results:")
                        for step in stub.Factorial(pb.UnaryRequest(n=n),
                                                   timeout=TIMEOUT_SEC):
                            print(f"    {step.step}! = {step.accumulator}")
                        show_latency(t0)

                    else:
                        print("  Invalid selection. Try again.")

                except grpc.RpcError as err:
                    code = err.code()
                    if code == StatusCode.UNAVAILABLE:
                        print(f"[ERROR] Cannot reach server at {SERVER_ADDR}. "
                              "Is it running?")
                    elif code == StatusCode.DEADLINE_EXCEEDED:
                        print(f"[ERROR] Call exceeded {TIMEOUT_SEC}s timeout.")
                    else:
                        print(f"[ERROR] RPC failed: {code.name} – "
                              f"{err.details()}")

    except KeyboardInterrupt:
        print("\nInterrupted, exiting…")


if __name__ == "__main__":
    main()
