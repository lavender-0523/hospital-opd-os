"""
hospital_os/synchronization.py
Process Synchronization & Mutex Locks.

Implements thread-safe token generation for multiple hospital reception desks,
protecting the shared counter using Mutual Exclusion (Mutex Lock).
Also includes a race condition simulator demonstrating what happens WITHOUT a lock.
"""

import threading
import time
from typing import List, Tuple, Dict


class TokenDispenser:
    """
    Hospital Reception Token Dispenser using Mutex Lock.

    Shared Resource (Critical Section): self.token_counter
    Protection Mechanism: threading.Lock (Mutex)
    """

    def __init__(self, initial_token: int = 100):
        self.token_counter = initial_token
        self.lock = threading.Lock()
        self.log_history: List[Dict] = []

    def generate_token(self, receptionist_name: str, delay: float = 0.05) -> int:
        """
        Thread-safe token generator.
        Entry Section: Acquire Lock
        Critical Section: Read & Increment shared token_counter
        Exit Section: Release Lock
        """
        # Entry Section
        with self.lock:
            # Critical Section
            self.token_counter += 1
            new_token = self.token_counter
            log_entry = {
                "desk": receptionist_name,
                "token": new_token,
                "timestamp": time.time(),
                "status": "Safe (Mutex Acquired)",
            }
            self.log_history.append(log_entry)
            print(
                f"[{receptionist_name}] Entered Critical Section -> Generated Token #{new_token}"
            )
            time.sleep(delay)
        # Exit Section
        return new_token

    def reset(self, initial_token: int = 100):
        with self.lock:
            self.token_counter = initial_token
            self.log_history.clear()


class RaceConditionSimulator:
    """
    Demonstrates race condition behavior when mutual exclusion is NOT enforced.
    Threads simultaneously read, sleep, and write back, illustrating why Mutex is vital.
    """

    def __init__(self, initial_token: int = 100):
        self.unsafe_counter = initial_token
        self.generated_tokens: List[Tuple[str, int]] = []

    def unsafe_generate(self, desk_name: str, delay: float = 0.02) -> int:
        # Deliberately unsafe read-modify-write without lock
        current = self.unsafe_counter
        time.sleep(delay)  # Context switch window: another thread reads same value!
        current += 1
        self.unsafe_counter = current
        self.generated_tokens.append((desk_name, current))
        print(f"[UNSAFE {desk_name}] Read-Modify-Write -> Issued Token #{current}")
        return current


def run_concurrency_test(desks: List[str] = None, tokens_per_desk: int = 2) -> Dict:
    """
    Runs multi-threaded concurrency demonstration across reception desks.
    Returns results verifying mutual exclusion integrity.
    """
    if desks is None:
        desks = ["Desk-A", "Desk-B"]

    dispenser = TokenDispenser(initial_token=100)
    threads = []
    results: List[Tuple[str, int]] = []
    lock_records = threading.Lock()

    def worker(name: str):
        for _ in range(tokens_per_desk):
            tok = dispenser.generate_token(name)
            with lock_records:
                results.append((name, tok))

    print("\n" + "=" * 65)
    print("DEMO: CONCURRENCY & CRITICAL SECTION (MUTEX LOCKED)")
    print(f"Desks: {', '.join(desks)} | Tokens per desk: {tokens_per_desk}")
    print("=" * 65)

    start_time = time.time()
    for name in desks:
        t = threading.Thread(target=worker, args=(name,), name=f"Thread-{name}")
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    duration = time.time() - start_time

    token_numbers = [tok for _, tok in results]
    unique_tokens = set(token_numbers)
    has_duplicates = len(unique_tokens) != len(token_numbers)

    print("-" * 65)
    print(f"Total Tokens Generated : {len(token_numbers)}")
    print(f"Unique Token Numbers   : {len(unique_tokens)}")
    print(f"Execution Duration     : {duration:.3f}s")
    if not has_duplicates:
        print(">> Mutex verified: SUCCESS! No duplicate token numbers assigned.\n")
    else:
        print(">> WARNING: Duplicate tokens detected!\n")

    return {
        "status": "PASS" if not has_duplicates else "FAIL",
        "has_duplicates": has_duplicates,
        "tokens": results,
        "final_counter": dispenser.token_counter,
        "duration": duration,
    }


def run_race_condition_demo(desks: List[str] = None, tokens_per_desk: int = 3) -> Dict:
    """
    Demonstrates race condition when Mutex lock is disabled.
    """
    if desks is None:
        desks = ["Unsafe-Desk-1", "Unsafe-Desk-2"]

    sim = RaceConditionSimulator(initial_token=100)
    threads = []

    print("\n" + "=" * 65)
    print("DEMO: RACE CONDITION (WITHOUT MUTEX LOCK - FOR COMPARISON)")
    print("=" * 65)

    def worker(name: str):
        for _ in range(tokens_per_desk):
            sim.unsafe_generate(name)

    for name in desks:
        t = threading.Thread(target=worker, args=(name,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    token_numbers = [tok for _, tok in sim.generated_tokens]
    unique_tokens = set(token_numbers)
    duplicates = len(token_numbers) - len(unique_tokens)

    print("-" * 65)
    print(f"Total Requests Processed : {len(token_numbers)}")
    print(f"Distinct Tokens Assigned : {len(unique_tokens)}")
    print(f"Duplicate Conflicts      : {duplicates}")
    print(">> Notice: Without Mutex, simultaneous access causes data corruption!\n")

    return {
        "has_duplicates": duplicates > 0,
        "duplicates": duplicates,
        "tokens": sim.generated_tokens,
        "final_counter": sim.unsafe_counter,
    }
