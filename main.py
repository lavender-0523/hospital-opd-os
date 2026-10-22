"""
Hospital OPD Resource & Patient Management System
Operating System Scheduling & Process Synchronization Simulator (COOS Mini Project)
"""

import sys
import threading
import time
import webbrowser
from hospital_os.patient import Patient
from hospital_os.synchronization import (
    TokenDispenser,
    run_concurrency_test,
    run_race_condition_demo,
)
from hospital_os.schedulers import (
    PreemptivePriorityScheduler,
    RoundRobinScheduler,
    FCFSScheduler,
    compress_gantt,
)
from hospital_os.metrics import (
    calculate_metrics,
    display_results,
    print_comparison_table,
)

# ==========================================================
# 1. SYNCHRONIZATION: TOKEN GENERATOR (Mutex Lock)
# ==========================================================
token_counter = 100
token_lock = threading.Lock()  # Mutex Lock for Critical Section


def generate_token(receptionist_name):
    global token_counter
    # Entry Section: Acquire Lock
    with token_lock:
        # Critical Section: Shared variable modified
        token_counter += 1
        new_token = token_counter
        print(
            f"[{receptionist_name}] Entered Critical Section -> Generated Token #{new_token}"
        )
        time.sleep(0.05)
    # Exit Section: Lock released automatically
    return new_token


def test_concurrency():
    print("\n" + "=" * 65)
    print("DEMO: CONCURRENCY & CRITICAL SECTION (2 RECEPTIONISTS)")
    print("=" * 65)
    t1 = threading.Thread(target=lambda: [generate_token("Desk-A") for _ in range(2)])
    t2 = threading.Thread(target=lambda: [generate_token("Desk-B") for _ in range(2)])
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(">> Mutex verified: No duplicate token numbers assigned.\n")


# ==========================================================
# 2. SCHEDULING WRAPPERS
# ==========================================================
def run_priority_scheduling(patient_list):
    scheduler = PreemptivePriorityScheduler(aging_threshold=5, verbose=True)
    result = scheduler.run(patient_list)
    display_results(
        result["patients"],
        result["gantt"],
        result["total_time"],
        algorithm_name="PREEMPTIVE PRIORITY (AGING)",
    )
    return result


def run_round_robin(patient_list, time_quantum=2):
    scheduler = RoundRobinScheduler(time_quantum=time_quantum, verbose=True)
    result = scheduler.run(patient_list)
    display_results(
        result["patients"],
        result["gantt"],
        result["total_time"],
        algorithm_name=f"ROUND ROBIN (TQ={time_quantum})",
    )
    return result


def run_comparative_benchmark(patient_list):
    """Executes Priority, Round Robin (TQ=2, TQ=3), and FCFS for comprehensive comparison."""
    p_sched = PreemptivePriorityScheduler(aging_threshold=5, verbose=False)
    rr2_sched = RoundRobinScheduler(time_quantum=2, verbose=False)
    rr3_sched = RoundRobinScheduler(time_quantum=3, verbose=False)
    fcfs_sched = FCFSScheduler(verbose=False)

    res_p = p_sched.run(patient_list)
    res_rr2 = rr2_sched.run(patient_list)
    res_rr3 = rr3_sched.run(patient_list)
    res_fcfs = fcfs_sched.run(patient_list)

    print_comparison_table([res_p, res_rr2, res_rr3, res_fcfs])


def add_custom_patient(patient_list):
    """Allows user to dynamically add a patient to the simulation batch."""
    print("\n--- ADD CUSTOM PATIENT ---")
    try:
        token_id = int(input("Enter Token ID (e.g., 105): ").strip())
        name = input("Enter Patient Name: ").strip()
        age = int(input("Enter Age: ").strip())
        print("Select Category: 1) Emergency  2) Senior  3) Normal")
        cat_choice = input("Choice (1-3): ").strip()
        category = (
            "Emergency"
            if cat_choice == "1"
            else ("Senior" if cat_choice == "2" else "Normal")
        )
        arrival_time = int(input("Enter Arrival Time (AT >= 0): ").strip())
        burst_time = int(input("Enter Burst / Consultation Time (BT >= 1): ").strip())

        new_p = Patient(token_id, name, age, category, arrival_time, burst_time)
        patient_list.append(new_p)
        print(f">> Patient T{token_id} ({name}, {category}) added successfully!\n")
    except ValueError:
        print(">> Error: Invalid numeric input. Patient was not added.\n")


def display_current_patients(patient_list):
    print("\n--- CURRENT OPD PATIENTS BATCH ---")
    print(f"{'Token':<6} | {'Name':<16} | {'Age':<4} | {'Category':<10} | {'AT':<3} | {'BT':<3} | {'Priority':<8}")
    print("-" * 65)
    for p in patient_list:
        print(
            f"T{p.token_id:<5} | {p.name:<16} | {p.age:<4} | {p.category:<10} | "
            f"{p.arrival_time:<3} | {p.burst_time:<3} | {p.priority:<8}"
        )
    print("-" * 65 + "\n")


# ==========================================================
# 3. MAIN EXECUTION & INTERACTIVE MENU
# ==========================================================
if __name__ == "__main__":
    # Test concurrency first (Process Synchronization)
    test_concurrency()

    # Default batch of OPD patients
    opd_patients = [
        Patient(101, "Ramesh", 28, "Normal", arrival_time=0, burst_time=6),
        Patient(102, "Sita Devi", 70, "Senior", arrival_time=1, burst_time=4),
        Patient(103, "Kabir (Trauma)", 35, "Emergency", arrival_time=2, burst_time=3),
        Patient(104, "Amit", 24, "Normal", arrival_time=3, burst_time=5),
    ]

    while True:
        print("=" * 55)
        print("       HOSPITAL OPD SYSTEM (COOS MINI PROJECT)")
        print("=" * 55)
        print("1. Preemptive Priority (Emergency first + Aging)")
        print("2. Round Robin (Diagnostics Lab TQ=2)")
        print("3. Concurrency & Mutex Lock Test")
        print("4. Race Condition Demo (Without Mutex - Flaw Demo)")
        print("5. Comparative Benchmark (Priority vs RR vs FCFS)")
        print("6. View / Add Patients in OPD Batch")
        print("7. Launch Visual Web Simulator in Browser")
        print("8. Exit")
        print("=" * 55)
        choice = input("Enter choice (1-8): ").strip()

        if choice == "1":
            run_priority_scheduling(opd_patients)
        elif choice == "2":
            tq_input = input("Enter Time Quantum (default 2): ").strip()
            tq = int(tq_input) if tq_input.isdigit() and int(tq_input) > 0 else 2
            run_round_robin(opd_patients, time_quantum=tq)
        elif choice == "3":
            run_concurrency_test(["Desk-A", "Desk-B", "Desk-C"], tokens_per_desk=2)
        elif choice == "4":
            run_race_condition_demo(["Desk-Unsafe-1", "Desk-Unsafe-2"], tokens_per_desk=3)
        elif choice == "5":
            run_comparative_benchmark(opd_patients)
        elif choice == "6":
            display_current_patients(opd_patients)
            sub = input("Do you want to add a new patient? (y/n): ").strip().lower()
            if sub == "y":
                add_custom_patient(opd_patients)
        elif choice == "7":
            print("Starting local web visualizer server...")
            try:
                import subprocess
                subprocess.Popen([sys.executable, "server.py"], cwd=".")
                time.sleep(1)
                webbrowser.open("http://localhost:8000")
                print(">> Visualizer launched at http://localhost:8000")
            except Exception as e:
                print(f">> Please open web/index.html in your browser or run 'python server.py'. Error: {e}")
        elif choice == "8":
            print("Exiting Hospital OPD System. Goodbye!")
            break
        else:
            print("Invalid input! Please enter a number between 1 and 8.")
