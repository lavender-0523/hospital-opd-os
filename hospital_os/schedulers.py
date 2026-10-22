"""
hospital_os/schedulers.py
Implements CPU scheduling algorithms mapped to Hospital OPD and Diagnostic Lab operations:
1. Preemptive Priority Scheduling with Aging (Emergency / Triage Room)
2. Round Robin Scheduling (X-Ray & Diagnostic Lab with Time Quantum)
3. First-Come First-Served (FCFS - Baseline OPD)
4. Shortest Remaining Time First (SRTF - Fast Checkup Clinic)
"""

from typing import List, Dict, Any, Optional
from .patient import Patient, PatientState


def compress_gantt(raw_gantt: List) -> List[List]:
    """
    Compresses consecutive time slices allocated to the same patient into one continuous block.
    Example: [(101, 0, 1), (101, 1, 2)] -> [[101, 0, 2]]
    """
    if not raw_gantt:
        return []
    compressed = [[raw_gantt[0][0], raw_gantt[0][1], raw_gantt[0][2]]]
    for pid, start, end in raw_gantt[1:]:
        if pid == compressed[-1][0] and start == compressed[-1][2]:
            compressed[-1][2] = end
        else:
            compressed.append([pid, start, end])
    return compressed


class PreemptivePriorityScheduler:
    """
    Preemptive Priority Scheduling with Aging.
    - Highest urgency = lowest priority number (1: Emergency, 2: Senior, 3: Normal).
    - Emergency arrivals immediately preempt the Doctor if priority is strictly higher.
    - Aging: Prevents starvation of Normal patients by elevating priority when waiting >= aging_threshold.
    """

    def __init__(self, aging_threshold: int = 5, verbose: bool = True):
        self.aging_threshold = aging_threshold
        self.verbose = verbose

    def run(self, patient_list: List[Patient]) -> Dict[str, Any]:
        patients = [p.copy() for p in patient_list]
        current_time = 0
        completed: List[Patient] = []
        raw_gantt: List[tuple] = []
        events: List[Dict[str, Any]] = []
        timeline_ticks: List[Dict[str, Any]] = []
        last_patient: Optional[Patient] = None
        total_patients = len(patients)

        if self.verbose:
            print("\n" + "=" * 65)
            print("RUNNING: PREEMPTIVE PRIORITY SCHEDULING (WITH AGING)")
            print("=" * 65)

        while len(completed) < total_patients:
            # 1. Aging check: boost priority if a waiting patient has waited >= aging_threshold units
            for p in patients:
                if p.arrival_time <= current_time and p.remaining_time > 0:
                    wait_so_far = current_time - p.arrival_time
                    if wait_so_far >= self.aging_threshold and p.priority > 1:
                        old_prio = p.priority
                        p.priority -= 1
                        p.aged_times += 1
                        msg = (
                            f"[AGING at t={current_time}] Token #{p.token_id} ({p.name}) "
                            f"waited {wait_so_far} units -> Priority elevated to {p.priority}"
                        )
                        events.append(
                            {
                                "type": "AGING",
                                "time": current_time,
                                "token_id": p.token_id,
                                "name": p.name,
                                "message": msg,
                                "old_priority": old_prio,
                                "new_priority": p.priority,
                            }
                        )
                        if self.verbose:
                            print(msg)

            # 2. Pick highest priority available patient
            available = [
                p
                for p in patients
                if p.arrival_time <= current_time and p.remaining_time > 0
            ]
            if not available:
                # CPU / Doctor is Idle
                raw_gantt.append(("IDLE", current_time, current_time + 1))
                current_time += 1
                continue

            # Sort by Priority ascending (1 is highest), tie-breaker is Arrival Time
            available.sort(key=lambda x: (x.priority, x.arrival_time))
            current_p = available[0]

            # Record First Response Time
            if current_p.first_response_time is None:
                current_p.first_response_time = current_time
                current_p.response_time = current_time - current_p.arrival_time

            # 3. Detect Preemption
            if (
                last_patient
                and last_patient.token_id != current_p.token_id
                and last_patient.remaining_time > 0
            ):
                preempt_msg = (
                    f"[PREEMPTION at t={current_time}] Emergency Token #{current_p.token_id} "
                    f"preempted Doctor from Token #{last_patient.token_id}"
                )
                events.append(
                    {
                        "type": "PREEMPTION",
                        "time": current_time,
                        "token_id": current_p.token_id,
                        "preempted_id": last_patient.token_id,
                        "message": preempt_msg,
                    }
                )
                if self.verbose:
                    print(preempt_msg)

            # 4. Execute for 1 unit of time
            current_p.state = PatientState.RUNNING
            raw_gantt.append((current_p.token_id, current_time, current_time + 1))

            # Snapshot timeline tick for animation
            timeline_ticks.append(
                {
                    "time": current_time,
                    "running": current_p.token_id,
                    "ready": [
                        p.token_id
                        for p in available
                        if p.token_id != current_p.token_id
                    ],
                }
            )

            current_p.remaining_time -= 1
            last_patient = current_p
            current_time += 1

            # 5. Check if patient consultation is finished
            if current_p.remaining_time == 0:
                current_p.completion_time = current_time
                current_p.turnaround_time = (
                    current_p.completion_time - current_p.arrival_time
                )
                current_p.waiting_time = (
                    current_p.turnaround_time - current_p.burst_time
                )
                current_p.state = PatientState.COMPLETED
                completed.append(current_p)
                events.append(
                    {
                        "type": "COMPLETED",
                        "time": current_time,
                        "token_id": current_p.token_id,
                        "message": f"Token #{current_p.token_id} ({current_p.name}) consultation completed at t={current_time}",
                    }
                )

        compressed = compress_gantt(raw_gantt)
        return {
            "algorithm": "Preemptive Priority (with Aging)",
            "patients": patients,
            "raw_gantt": raw_gantt,
            "gantt": compressed,
            "events": events,
            "timeline": timeline_ticks,
            "total_time": current_time,
        }


class RoundRobinScheduler:
    """
    Round Robin Scheduling.
    Used for shared Hospital Resources like Diagnostic Lab (X-Ray / MRI / Blood Test),
    where each patient gets a fixed Time Quantum (TQ).
    """

    def __init__(self, time_quantum: int = 2, verbose: bool = True):
        self.time_quantum = time_quantum
        self.verbose = verbose

    def run(self, patient_list: List[Patient]) -> Dict[str, Any]:
        patients = [p.copy() for p in patient_list]
        patients.sort(key=lambda x: x.arrival_time)
        queue: List[Patient] = []
        gantt_chart: List[tuple] = []
        events: List[Dict[str, Any]] = []
        timeline_ticks: List[Dict[str, Any]] = []
        current_time = 0
        completed: List[Patient] = []
        visited = set()

        if self.verbose:
            print("\n" + "=" * 65)
            print(
                f"RUNNING: ROUND ROBIN FOR DIAGNOSTICS (TIME QUANTUM = {self.time_quantum})"
            )
            print("=" * 65)

        def add_arrived_patients(t: int):
            for p in patients:
                if (
                    p.arrival_time <= t
                    and p.token_id not in visited
                    and p.remaining_time > 0
                ):
                    queue.append(p)
                    visited.add(p.token_id)
                    p.state = PatientState.READY

        add_arrived_patients(current_time)

        while len(completed) < len(patients):
            if not queue:
                gantt_chart.append(("IDLE", current_time, current_time + 1))
                current_time += 1
                add_arrived_patients(current_time)
                continue

            curr = queue.pop(0)
            if curr.first_response_time is None:
                curr.first_response_time = current_time
                curr.response_time = current_time - curr.arrival_time

            time_slice = min(curr.remaining_time, self.time_quantum)
            start_time = current_time
            curr.state = PatientState.RUNNING

            # Record timeline steps
            for step in range(time_slice):
                timeline_ticks.append(
                    {
                        "time": current_time + step,
                        "running": curr.token_id,
                        "ready": [p.token_id for p in queue],
                    }
                )

            current_time += time_slice
            curr.remaining_time -= time_slice

            gantt_chart.append((curr.token_id, start_time, current_time))

            # New patients arriving during the time slice get added to queue
            add_arrived_patients(current_time)

            if curr.remaining_time > 0:
                curr.state = PatientState.READY
                queue.append(curr)
                events.append(
                    {
                        "type": "QUANTUM_EXPIRED",
                        "time": current_time,
                        "token_id": curr.token_id,
                        "message": f"Token #{curr.token_id} quantum expired, moved back to queue",
                    }
                )
            else:
                curr.completion_time = current_time
                curr.turnaround_time = curr.completion_time - curr.arrival_time
                curr.waiting_time = curr.turnaround_time - curr.burst_time
                curr.state = PatientState.COMPLETED
                completed.append(curr)
                events.append(
                    {
                        "type": "COMPLETED",
                        "time": current_time,
                        "token_id": curr.token_id,
                        "message": f"Token #{curr.token_id} ({curr.name}) diagnostics completed at t={current_time}",
                    }
                )

        return {
            "algorithm": f"Round Robin (TQ={self.time_quantum})",
            "patients": patients,
            "raw_gantt": gantt_chart,
            "gantt": gantt_chart,
            "events": events,
            "timeline": timeline_ticks,
            "total_time": current_time,
        }


class FCFSScheduler:
    """
    First-Come, First-Served (FCFS) Scheduling.
    Standard hospital queue order without triage priority or preemption.
    Used as an academic baseline to compare wait times.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def run(self, patient_list: List[Patient]) -> Dict[str, Any]:
        patients = [p.copy() for p in patient_list]
        patients.sort(key=lambda x: (x.arrival_time, x.token_id))
        current_time = 0
        gantt_chart = []

        for p in patients:
            if current_time < p.arrival_time:
                gantt_chart.append(("IDLE", current_time, p.arrival_time))
                current_time = p.arrival_time

            p.first_response_time = current_time
            p.response_time = current_time - p.arrival_time
            start_time = current_time
            current_time += p.burst_time
            p.remaining_time = 0
            p.completion_time = current_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            p.state = PatientState.COMPLETED
            gantt_chart.append((p.token_id, start_time, current_time))

        return {
            "algorithm": "First-Come First-Served (FCFS)",
            "patients": patients,
            "raw_gantt": gantt_chart,
            "gantt": gantt_chart,
            "events": [],
            "total_time": current_time,
        }
