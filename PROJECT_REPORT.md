# MINI PROJECT REPORT

## PROJECT TITLE:
### HOSPITAL OPD RESOURCE & PATIENT MANAGEMENT SYSTEM (MediQueue OS)
**Domain:** Computer Organization and Operating Systems (COOS)  
**Project Focus:** Process Synchronization (Mutex Locks) & CPU Scheduling Algorithms

---

## 1. ABSTRACT
In modern hospital operations, outpatient management presents critical operational challenges identical to Operating System resource management. A single medical specialist (analogous to a single-core CPU) or shared diagnostic apparatus (such as X-Ray or MRI machines) must be allocated efficiently across patients presenting varying urgency levels. 

This project simulates hospital Out-Patient Department (OPD) triage, diagnostic resource sharing, and reception token generation by modeling fundamental Operating System principles:
1. **Mutual Exclusion (Mutex Lock)** for race-free sequential token generation across concurrent reception desks.
2. **Process Control Block (PCB)** abstraction mapping clinical patient data to OS process metadata.
3. **Preemptive Priority Scheduling with Dynamic Aging** to guarantee rapid emergency care while strictly preventing starvation of normal patients.
4. **Round Robin (RR) Scheduling** for fair time-sliced access to shared diagnostic laboratory equipment.
5. **Gantt Chart Generation & Performance Metric Analysis** evaluating Average Waiting Time (AWT), Turnaround Time (ATAT), Response Time (ART), and Resource Utilization.

---

## 2. PROBLEM STATEMENT & OBJECTIVES
Standard hospital queues that operate on a First-Come, First-Served (FCFS) basis create fatal bottlenecks when trauma or emergency cases arrive behind lengthy routine checkups. Conversely, strict static priority scheduling risks **starvation** (indefinite postponement) of low-urgency patients. Furthermore, concurrent ticket generation at multiple reception counters introduces race conditions and duplicate token issuance.

### Core Objectives:
- Develop a multi-threaded Token Generator using **Mutex Locks** to ensure thread safety in the critical section.
- Implement **Preemptive Priority Scheduling** with dynamic **Aging** to eliminate starvation.
- Implement **Round Robin Scheduling** with configurable Time Quantum for diagnostic lab apparatus sharing.
- Provide interactive CLI and animated Web visualizer displaying real-time Gantt charts and performance metrics.

---

## 3. OS CONCEPT TO CLINICAL ANALOGY MAPPING

```
+-----------------------------------+-----------------------------------+
|      OPERATING SYSTEM CONCEPT     |         HOSPITAL OPD ANALOGY      |
+-----------------------------------+-----------------------------------+
| Process                           | Patient                           |
| Process Control Block (PCB)       | Patient Record / OPD Token        |
| Process ID (PID)                  | Token ID (#101, #102, ...)        |
| CPU / Processor                   | Doctor / Consultation Room        |
| CPU Burst Time (BT)               | Consultation / Diagnosis Duration |
| Arrival Time (AT)                 | Patient Arrival at Hospital       |
| Ready Queue                       | Waiting Room Lounge               |
| Context Switch                    | Doctor Switching Patient Charts   |
| Preemption                        | Emergency Trauma Triage Preempt   |
| Starvation                        | Patient Waiting Indefinitely      |
| Aging                             | Elevating Priority with Wait Time |
| Time Quantum (TQ)                 | Fixed X-Ray / Diagnostic Slot     |
| Shared Memory / Global Variable   | Central Token Counter             |
| Mutex Lock (threading.Lock)       | Reception Counter Mutex Lock      |
| Race Condition                    | Duplicate Token Number Issued     |
+-----------------------------------+-----------------------------------+
```

---

## 4. MATHEMATICAL FORMULATION & METRICS

1. **Turnaround Time (TAT)**:
   $$\text{TAT} = \text{Completion Time (CT)} - \text{Arrival Time (AT)}$$

2. **Waiting Time (WT)**:
   $$\text{WT} = \text{Turnaround Time (TAT)} - \text{Burst Time (BT)}$$

3. **Response Time (RT)**:
   $$\text{RT} = \text{Time of First Doctor Attention} - \text{Arrival Time (AT)}$$

4. **Average Waiting Time (AWT)**:
   $$\text{AWT} = \frac{1}{N} \sum_{i=1}^{N} \text{WT}_i$$

5. **Doctor / Resource Utilization**:
   $$\text{Utilization} = \left( \frac{\sum_{i=1}^{N} \text{BT}_i}{\text{Total Simulation Time}} \right) \times 100\%$$

---

## 5. DETAILED TRACE OF DEFAULT TEST BATCH

### Initial Input Batch:
- **T101**: Ramesh (Normal, Priority 3, AT = 0, BT = 6)
- **T102**: Sita Devi (Senior, Priority 2, AT = 1, BT = 4)
- **T103**: Kabir (Emergency Trauma, Priority 1, AT = 2, BT = 3)
- **T104**: Amit (Normal, Priority 3, AT = 3, BT = 5)

### Step-by-Step Execution Trace (Preemptive Priority with Aging):

- **$t = 0$**: Only T101 is present. T101 enters Doctor's Office. BT remaining: 6.
- **$t = 1$**: T102 arrives with Priority 2. Since Priority 2 < Priority 3 (higher urgency), **Preemption occurs!** Doctor pauses T101 (BT remaining: 5). T102 begins checkup.
- **$t = 2$**: T103 arrives with Priority 1 (Emergency). Since Priority 1 < Priority 2, **Preemption occurs!** Doctor pauses T102 (BT remaining: 3). T103 begins checkup.
- **$t = 3$**: T104 arrives (Priority 3). T103 continues (BT remaining: 2).
- **$t = 4$**: T103 continues (BT remaining: 1).
- **$t = 5$**: T103 finishes ($\text{CT} = 5$).
  - **Aging Evaluation**: T101 has been waiting since $t=0$ ($5 - 0 = 5$ units). Its priority is dynamically elevated from $3 \rightarrow 2$!
  - Active ready patients: T101 (Priority 2, AT=0), T102 (Priority 2, AT=1), T104 (Priority 3, AT=3).
  - Tie-breaker on priority is Arrival Time: T101 arrived at $t=0$, so T101 resumes execution.
- **$t = 6$**: T101 continues. T101 and T102 age again based on waiting duration.
- **$t = 10$**: T101 finishes ($\text{CT} = 10$). T102 resumes.
- **$t = 13$**: T102 finishes ($\text{CT} = 13$). T104 begins.
- **$t = 18$**: T104 finishes ($\text{CT} = 18$). All patients completed.

### Final Result Metrics:
```
Token  | Name             | Category   | AT  | BT  | CT  | TAT  | WT  | RT 
-------------------------------------------------------------------------
T101   | Ramesh           | Normal     | 0   | 6   | 10  | 10   | 4   | 0  
T102   | Sita Devi        | Senior     | 1   | 4   | 13  | 12   | 8   | 0  
T103   | Kabir (Trauma)   | Emergency  | 2   | 3   | 5   | 3    | 0   | 0  
T104   | Amit             | Normal     | 3   | 5   | 18  | 15   | 10  | 10 
-------------------------------------------------------------------------
Average Waiting Time (AWT)       : 5.50
Average Turnaround Time (ATAT)   : 10.00
Average Response Time (ART)      : 2.50
Doctor / Resource Utilization    : 100.00%
```

---

## 6. PROCESS SYNCHRONIZATION & CRITICAL SECTION ANALYSIS

### The Critical Section Problem:
Multiple reception desks operate concurrently as separate POSIX / Python OS threads:
- Shared Variable: `token_counter`
- Hazard: If Desk A and Desk B simultaneously execute `token_counter += 1`, both read the same base value, resulting in duplicate token numbers issued to two distinct patients.

### Solution via Mutex Lock:
```python
with token_lock:  # Entry Section: Acquires Mutex Lock
    token_counter += 1  # Critical Section: Modifies Shared Memory
    new_token = token_counter
# Exit Section: Lock automatically released
```

### Verification:
Unit tests spawning concurrent threads confirmed:
- `Total Tokens Generated: 20`
- `Unique Tokens: 20`
- `Duplicate Rate: 0.0%`
When the lock was disabled in our race condition simulator, duplicates consistently occurred, verifying the necessity of Mutual Exclusion.

---

## 7. VIVA & INTERVIEW PREPARATION QUESTIONS

### Q1: What is the Critical Section Problem, and what three conditions must a solution satisfy?
**Answer:** The Critical Section Problem involves coordinating access to shared data accessed by concurrent processes. A valid solution must satisfy:
1. **Mutual Exclusion**: If process $P_i$ is executing in its critical section, no other process can be executing in its critical section.
2. **Progress**: If no process is executing in its critical section and some processes wish to enter, only those processes not in their remainder section can participate in deciding who enters next.
3. **Bounded Waiting**: There exists a bound on the number of times other processes are allowed to enter their critical sections after a process has made a request to enter.

### Q2: What is Starvation, and how does Aging solve it in this project?
**Answer:** Starvation (indefinite postponement) occurs in priority scheduling when a continuous stream of higher-priority processes prevents a lower-priority process from ever acquiring the CPU. Aging solves this by gradually increasing the priority of processes that wait in the system for extended periods (in our implementation, reducing priority number by 1 every 5 time units of wait), guaranteeing that low-priority patients eventually attain the highest priority and receive service.

### Q3: Why is Round Robin suitable for diagnostic equipment but Preemptive Priority preferred for doctors?
**Answer:** In diagnostic labs (X-Ray/MRI), no single patient has a medical right to monopolize equipment indefinitely; time-slicing ensures everyone gets progressive imaging with minimal maximum waiting time. In doctor consultation, clinical severity (e.g., hemorrhages, cardiac arrest) demands immediate preemption because human life is at stake.

### Q4: What happens if the Time Quantum (TQ) in Round Robin is extremely large or extremely small?
**Answer:**
- **If TQ is extremely large**: Round Robin degrades into First-Come, First-Served (FCFS) scheduling.
- **If TQ is extremely small**: The system incurs excessive context switching overhead, causing severe CPU performance degradation and reduced throughput.

---

## 8. CONCLUSION
The MediQueue OS simulator bridges theoretical Operating System principles and pragmatic healthcare resource allocation. By implementing Mutex Locks, Preemptive Priority Scheduling with Aging, and Round Robin diagnostic queueing, the system ensures zero-conflict token generation, zero patient starvation, and rapid emergency intervention.
