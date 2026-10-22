"""
hospital_os/metrics.py
Formats Gantt charts, metrics tables, and calculates operating system performance metrics:
- Average Waiting Time (AWT)
- Average Turnaround Time (ATAT)
- Average Response Time (ART)
- Doctor / Resource Utilization (%)
- Throughput (Patients / unit time)
"""

from typing import List, Dict, Any
from .patient import Patient


def calculate_metrics(patients: List[Patient], total_time: int) -> Dict[str, float]:
    """Calculates all key scheduling metrics."""
    n = len(patients)
    if n == 0 or total_time == 0:
        return {
            "awt": 0.0,
            "atat": 0.0,
            "art": 0.0,
            "utilization": 0.0,
            "throughput": 0.0,
        }

    total_wt = sum(p.waiting_time for p in patients)
    total_tat = sum(p.turnaround_time for p in patients)
    total_burst = sum(p.burst_time for p in patients)
    total_rt = sum(p.response_time for p in patients)

    return {
        "awt": total_wt / n,
        "atat": total_tat / n,
        "art": total_rt / n,
        "utilization": (total_burst / total_time) * 100,
        "throughput": n / total_time,
        "total_time": total_time,
    }


def display_results(
    patients: List[Patient],
    gantt: List,
    total_time: int,
    algorithm_name: str = "SCHEDULING ALGORITHM",
):
    """
    Renders the ASCII Gantt Chart, Patient Metrics Table, and Statistical Summary
    matching the user's output specification.
    """
    print(f"\n--- GANTT CHART ({algorithm_name}) ---")
    if not gantt:
        print("[No execution intervals recorded]")
    else:
        bar = "|"
        timeline = "0"
        for item in gantt:
            pid, start, end = item[0], item[1], item[2]
            label = f" T{pid} " if pid != "IDLE" else " IDLE "
            bar += label + "|"
            timeline += " " * (len(label) - len(str(end))) + str(end)
        print(bar)
        print(timeline)

    # Print Metrics Table
    print("\n--- METRICS TABLE ---")
    print(
        f"{'Token':<6} | {'Name':<16} | {'Category':<10} | {'AT':<3} | {'BT':<3} | {'CT':<3} | {'TAT':<4} | {'WT':<3} | {'RT':<3}"
    )
    print("-" * 73)

    for p in patients:
        print(
            f"T{p.token_id:<5} | {p.name:<16} | {p.category:<10} | "
            f"{p.arrival_time:<3} | {p.burst_time:<3} | {p.completion_time:<3} | "
            f"{p.turnaround_time:<4} | {p.waiting_time:<3} | {p.response_time:<3}"
        )

    print("-" * 73)
    stats = calculate_metrics(patients, total_time)

    print(f"Average Waiting Time (AWT)       : {stats['awt']:.2f}")
    print(f"Average Turnaround Time (ATAT)   : {stats['atat']:.2f}")
    print(f"Average Response Time (ART)      : {stats['art']:.2f}")
    print(f"Doctor / Resource Utilization    : {stats['utilization']:.2f}%")
    print(f"System Throughput                : {stats['throughput']:.3f} patients/unit time\n")


def print_comparison_table(results: List[Dict[str, Any]]):
    """
    Prints a side-by-side comparative benchmark table across multiple scheduling algorithms.
    """
    print("\n" + "=" * 78)
    print("  COMPARATIVE PERFORMANCE ANALYSIS (OS ALGORITHM BENCHMARK)")
    print("=" * 78)
    print(
        f"{'Algorithm':<32} | {'AWT':<7} | {'ATAT':<7} | {'ART':<7} | {'Utilization':<11} | {'Total Time':<10}"
    )
    print("-" * 78)

    for res in results:
        m = calculate_metrics(res["patients"], res["total_time"])
        print(
            f"{res['algorithm']:<32} | {m['awt']:<7.2f} | {m['atat']:<7.2f} | "
            f"{m['art']:<7.2f} | {m['utilization']:<10.2f}% | {m['total_time']:<10}"
        )
    print("=" * 78 + "\n")
