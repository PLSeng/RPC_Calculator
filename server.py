#!/usr/bin/env python3
"""
server.py – gRPC demo server with colour-coded per-call logging
Compatible with demo.proto (Calculator + Stats services)
"""
import math
import socket
import statistics as st
import time
from concurrent import futures
from typing import Iterator, Tuple

import grpc
import calculator_pb2 as pb
import calculator_pb2_grpc as rpc

# ───────────────────────────────
# ANSI colour helpers
# ───────────────────────────────
BLUE, GREEN, RED, RESET = "\033[34m", "\033[32m", "\033[31m", "\033[0m"
blue  = lambda t: f"{BLUE}{t}{RESET}"
green = lambda t: f"{GREEN}{t}{RESET}"
red   = lambda t: f"{RED}{t}{RESET}"

# ───────────────────────────────
# Server address info
# ───────────────────────────────
SERVER_PORT = 50051
SERVER_IP   = socket.gethostbyname(socket.gethostname())

# ───────────────────────────────
# Logging helpers
# ───────────────────────────────
def _parse_peer(peer: str) -> Tuple[str, str]:
    """Extract ip,port from strings like 'ipv4:127.0.0.1:54321'."""
    if peer.startswith(("ipv4:", "ipv6:")):
        peer = peer.split(":", 1)[1]
    ip, port = peer.rsplit(":", 1)
    return ip.strip("[]"), port

def log_req(method: str, ctx, msg: str) -> None:
    ip, port = _parse_peer(ctx.peer())
    ts = time.strftime("%H:%M:%S")
    print(blue(f"[{ts}]  {ip}:{port:>5} → {SERVER_IP}:{SERVER_PORT} "
               f"{method:<18} {msg}"))

def log_rep(method: str, ctx, msg: str, ok: bool = True) -> None:
    ip, port = _parse_peer(ctx.peer())
    ts = time.strftime("%H:%M:%S")
    colour = green if ok else red
    print(colour(f"[{ts}]  {SERVER_IP}:{SERVER_PORT} → {ip}:{port:>5} "
                 f"{method:<18} {msg}"))

# ───────────────────────────────
# Calculator service
# ───────────────────────────────
class CalculatorServicer(rpc.CalculatorServicer):

    # Unary RPCs ------------------------------------------------------
    def Add(self, req: pb.BinaryRequest, ctx):
        log_req("Add", ctx, f"{req.x} + {req.y}")
        res = pb.BinaryReply(result=req.x + req.y)
        log_rep("Add", ctx, f"= {res.result}")
        return res

    def Subtract(self, req, ctx):
        log_req("Subtract", ctx, f"{req.x} - {req.y}")
        res = pb.BinaryReply(result=req.x - req.y)
        log_rep("Subtract", ctx, f"= {res.result}")
        return res

    def Multiply(self, req, ctx):
        log_req("Multiply", ctx, f"{req.x} * {req.y}")
        res = pb.BinaryReply(result=req.x * req.y)
        log_rep("Multiply", ctx, f"= {res.result}")
        return res

    def Power(self, req: pb.PowerRequest, ctx):
        log_req("Power", ctx, f"{req.base}^{req.exponent}")
        res = pb.BinaryReply(result=pow(req.base, req.exponent))
        log_rep("Power", ctx, f"= {res.result}")
        return res

    def Divide(self, req, ctx):
        log_req("Divide", ctx, f"{req.x} / {req.y}")
        if req.y == 0:
            log_rep("Divide", ctx, "ERROR: div by 0", ok=False)
            ctx.abort(grpc.StatusCode.INVALID_ARGUMENT,
                      "Division by zero is not allowed")
        res = pb.DivideReply(quotient=req.x // req.y, remainder=req.x % req.y)
        log_rep("Divide", ctx, f"q={res.quotient} r={res.remainder}")
        return res

    # Server-streaming RPC -------------------------------------------
    def Factorial(self, req: pb.UnaryRequest,
                  ctx) -> Iterator[pb.FactorialStep]:
        n = req.n
        log_req("Factorial", ctx, f"n={n}")
        if n < 0:
            log_rep("Factorial", ctx, "ERROR: negative", ok=False)
            ctx.abort(grpc.StatusCode.INVALID_ARGUMENT,
                      "Negative factorial is undefined")

        acc = 1
        for k in range(0, n + 1):
            acc = acc * k if k else 1
            step = pb.FactorialStep(step=k, accumulator=acc)
            log_rep("Factorial", ctx, f"{k}! = {acc}")
            yield step
            time.sleep(0.05)      # for demo pacing

# ───────────────────────────────
# Stats service
# ───────────────────────────────
class StatsServicer(rpc.StatsServicer):

    def DescriptiveStats(self, req_iter, ctx):
        vals = []
        for val in req_iter:
            vals.append(val.v)
            log_req("Stats/Value", ctx, f"{val.v}")

        if not vals:
            log_rep("Stats/Reply", ctx, "ERROR: no data", ok=False)
            ctx.abort(grpc.StatusCode.INVALID_ARGUMENT, "No values supplied")

        mean = st.mean(vals)
        var  = st.variance(vals) if len(vals) > 1 else 0.0
        res  = pb.StatsReply(mean=mean, variance=var)
        log_rep("Stats/Reply", ctx, f"mean={mean:.3f} var={var:.3f}")
        return res

# ───────────────────────────────
# Bootstrap & graceful shutdown
# ───────────────────────────────
def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    rpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    rpc.add_StatsServicer_to_server(StatsServicer(), server)

    server.add_insecure_port(f"0.0.0.0:{SERVER_PORT}")
    server.start()
    print(f"gRPC server listening on {SERVER_IP}:{SERVER_PORT} — Ctrl-C to stop\n")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down gracefully …")
        server.stop(grace=5)
        print("Server closed.")

if __name__ == "__main__":
    serve()
