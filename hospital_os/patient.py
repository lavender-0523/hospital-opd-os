"""
hospital_os/patient.py
Represents a Patient record, equivalent to an Operating System Process Control Block (PCB).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PatientState:
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"


class Patient:
    """
    Patient Data Structure - Analogous to an OS Process Control Block (PCB).

    OS Concept Mapping:
      PID                <--> token_id
      Process Name       <--> name
      Process Priority   <--> priority (1: Emergency, 2: Senior, 3: Normal)
      Arrival Time (AT)  <--> arrival_time
      Burst Time (BT)    <--> burst_time (Consultation / Lab test duration)
      Remaining Time(RT) <--> remaining_time
      Completion Time(CT)<--> completion_time
      Turnaround Time(TAT)<--> turnaround_time = CT - AT
      Waiting Time (WT)  <--> waiting_time = TAT - BT
      Response Time (RT) <--> first_response_time - AT
    """

    def __init__(
        self,
        token_id: int,
        name: str,
        age: int,
        category: str,
        arrival_time: int,
        burst_time: int,
    ):
        self.token_id = int(token_id)
        self.name = str(name)
        self.age = int(age)
        self.category = str(category).capitalize()  # "Emergency", "Senior", "Normal"
        self.arrival_time = int(arrival_time)
        self.burst_time = int(burst_time)
        self.remaining_time = int(burst_time)

        # Priority mapping: 1 (Emergency) is highest, 2 (Senior), 3 (Normal) is lowest
        if self.category == "Emergency":
            self.priority = 1
        elif self.category == "Senior":
            self.priority = 2
        else:
            self.priority = 3

        self.initial_priority = self.priority
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.first_response_time: Optional[int] = None
        self.response_time = 0
        self.aged_times = 0
        self.state = PatientState.NEW

    def copy(self) -> "Patient":
        """Creates an independent duplicate of the patient PCB for fresh simulation runs."""
        p = Patient(
            self.token_id,
            self.name,
            self.age,
            self.category,
            self.arrival_time,
            self.burst_time,
        )
        p.priority = self.priority
        p.initial_priority = self.initial_priority
        return p

    def to_dict(self) -> dict:
        """Serializes patient state for JSON metrics / Web UI."""
        return {
            "token_id": self.token_id,
            "name": self.name,
            "age": self.age,
            "category": self.category,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "priority": self.priority,
            "initial_priority": self.initial_priority,
            "completion_time": self.completion_time,
            "turnaround_time": self.turnaround_time,
            "waiting_time": self.waiting_time,
            "response_time": self.response_time,
            "aged_times": self.aged_times,
            "state": self.state,
        }

    def __repr__(self) -> str:
        return (
            f"<Patient T{self.token_id} | {self.name} | {self.category} | "
            f"AT={self.arrival_time} BT={self.burst_time} Prio={self.priority}>"
        )
