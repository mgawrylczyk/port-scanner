import socket, threading, sys

from queue import Queue
from typing import List
from tqdm import tqdm
import time


def scan_port(target: str, port: int, timeout: float = 1.0) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        sock.close()
        return result == 0
    except socket.gaierror:
        return False
    except Exception:
        return False


def worker(target: str, queue: Queue, open_ports: List[int], lock: threading.Lock, pbar: tqdm):
    while not queue.empty():
        port = queue.get()
        if scan_port(target, port):
            with lock:
                open_ports.append(port)
        with lock:
            pbar.update(1)
        queue.task_done()


def main():
    if len(sys.argv) > 1:
        target = " ".join(sys.argv[1:])
    else:
        target = input("Please provide a target IP address")

    ports_to_scan = range(1, 1025)
    open_ports: List[int] = []
    queue = Queue()
    lock = threading.Lock()

    for port in ports_to_scan:
        queue.put(port)

    print(f"Scanning {len(ports_to_scan)} ports on {target}")
    start_time = time.time()
    with tqdm(
        total=len(ports_to_scan), desc="Scanning ports", unit="port", ncols=80, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} {postfix}"
    ) as pbar:
        thread_count = min(50, len(ports_to_scan) // 10 + 1)
        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=worker, args=(target, queue, open_ports, lock, pbar))
            t.daemon = True
            t.start()
            threads.append(t)
        queue.join()

    elapsed_time = time.time() - start_time
    print(f"\nScan completed in {elapsed_time:.2f} seconds.")
    if open_ports:
        print(f"Open ports on {target}: {', '.join(map(str, open_ports))}")
    else:
        print(f"No open ports found on {target}.")


if __name__ == "__main__":
    main()
