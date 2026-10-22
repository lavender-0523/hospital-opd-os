# Hospital OPD Resource & Patient Management System (MediQueue OS)
### Computer Organization and Operating Systems (COOS) Mini-Project

A comprehensive, interactive Operating System Simulator modeling real-world Hospital Out-Patient Department (OPD), Triage, and Diagnostic Laboratory operations using fundamental OS concepts:
- **Process Synchronization**: Mutex Locks, Critical Section Protection, Concurrency Testing, and Race Condition Demonstration.
- **Process Scheduling**:
  - **Preemptive Priority Scheduling with Aging** (Emergency Trauma Triage & Anti-Starvation Mechanism).
  - **Round Robin (RR)** with configurable Time Quantum (Diagnostics Lab, X-Ray & MRI sharing).
  - **First-Come, First-Served (FCFS)** baseline comparison.
- **Process Control Block (PCB)** representation of patient medical records.
- **Gantt Chart Visualization & Performance Metrics**: Average Waiting Time (AWT), Average Turnaround Time (ATAT), Average Response Time (ART), Resource / Doctor Utilization, and Throughput.
- **Modern Interactive Web Visualizer & Dashboard**: Built with pure HTML5/CSS3/JavaScript (Zero external dependencies).

---

## 🚀 Quick Start

### 1. Run the Terminal Interactive CLI
The interactive command-line interface provides the core coursework simulation and demo menu:

```bash
python main.py
```

Menu options include:
1. **Preemptive Priority** (Emergency first + Aging)
2. **Round Robin** (Diagnostics Lab TQ=2 or custom)
3. **Concurrency & Mutex Lock Test** (Multi-threaded reception desks)
4. **Race Condition Demo** (Without Mutex - demonstrating data corruption risk)
5. **Comparative Benchmark** (Side-by-side comparison table)
6. **View / Add Patients** (Custom patient entry)
7. **Launch Visual Web Simulator** (Opens dashboard in your browser)
8. **Exit**

---

### 2. Run the Visual Web Dashboard
To launch the rich, animated browser dashboard:

```bash
python server.py
```
Then visit **[http://localhost:8000](http://localhost:8000)** in any modern web browser.

> **Note**: You can also open `web/index.html` directly in your browser without any server, as it features a self-contained client-side simulation engine!

---

### 3. Run Automated Unit Tests
To verify all scheduling algorithms, aging logic, metrics, and thread synchronization:

```bash
python -m unittest discover tests
```

---

## 🏥 OS Concept to Hospital Mapping

| Operating System Concept | Hospital OPD Analogy | Purpose / Implementation |
| :--- | :--- | :--- |
| **Process / PCB** | Patient Record / Token | Stores PID, Category, Arrival Time (AT), Burst Time (BT), Remaining Time, State |
| **CPU / Core** | Doctor Consultation Room / Diagnostic Machine | Single shared resource executing consultations or tests |
| **Critical Section** | Central Token Generator Counter | Shared variable `token_counter` accessed concurrently by reception desks |
| **Mutex Lock (`threading.Lock`)** | Desk Token Dispenser Lock | Ensures only one receptionist modifies the token counter at a time |
| **Priority Scheduling** | Emergency Triage | Priority 1: Emergency, Priority 2: Senior Citizen, Priority 3: Normal OPD |
| **Preemption** | Emergency Trauma Arrival | Doctor stops normal consultation to treat an emergency patient immediately |
| **Aging Mechanism** | Long Wait Priority Escalation | Patients waiting $\ge 5$ time units have their priority elevated to prevent starvation |
| **Round Robin (Time Quantum)** | X-Ray / Lab Machine Sharing | Fixed time slot per patient before cycling to ensure interactive fairness |
| **Ready Queue** | OPD Waiting Room Lounge | Holds arrived patients waiting for the doctor or scanner |

---

## 📁 Repository Structure

```
coos_mini/
├── main.py                     # Interactive CLI Runner (Coursework entry point)
├── server.py                   # Local HTTP & JSON API Server (zero dependencies)
├── hospital_os/                # Core Python OS Simulator Package
│   ├── __init__.py
│   ├── patient.py              # Patient PCB Data Structure & States
│   ├── synchronization.py      # Mutex Lock Token Dispenser & Race Condition Simulator
│   ├── schedulers.py           # Preemptive Priority + Aging, Round Robin, FCFS
│   └── metrics.py              # Gantt Chart generation & Metric computation
├── tests/
│   ├── __init__.py
│   └── test_simulation.py     # Automated Unit Tests
├── web/                        # Modern Web Dashboard
│   ├── index.html              # Interactive Visual UI
│   ├── style.css               # Dark-mode Glassmorphic CSS styling
│   └── app.js                  # Frontend Simulation Engine & Gantt Renderer
├── README.md                   # Project Overview & Setup Guide
└── PROJECT_REPORT.md           # Academic Report, Theory & Viva Q&A
```

---

## 📊 Default Simulation Batch Metrics

Based on the default coursework patient batch:
- **T101 (Ramesh)**: Normal, AT = 0, BT = 6
- **T102 (Sita Devi)**: Senior, AT = 1, BT = 4
- **T103 (Kabir - Trauma)**: Emergency, AT = 2, BT = 3
- **T104 (Amit)**: Normal, AT = 3, BT = 5

### Algorithm Benchmark Comparison:
| Algorithm | Average Waiting Time (AWT) | Average Turnaround (ATAT) | Average Response Time (ART) | Utilization |
| :--- | :---: | :---: | :---: | :---: |
| **Preemptive Priority (with Aging)** | **5.50** | **10.00** | 2.50 | 100% |
| **Round Robin (TQ=2)** | 8.50 | 13.00 | **2.00** | 100% |
| **Round Robin (TQ=3)** | 8.50 | 13.00 | 3.00 | 100% |
| **First-Come First-Served (FCFS)** | 5.75 | 10.25 | 5.75 | 100% |

### Key Observations:
1. **Emergency Response**: Preemptive Priority immediately allocates the doctor to Token #103 (Emergency) at $t=2$, yielding a waiting time of $0$ for critical cases.
2. **Anti-Starvation via Aging**: At $t=5$, Token #101 has waited 5 units, so its priority is boosted, preventing it from being starved behind newer arrivals.
3. **Response Time vs Turnaround**: Round Robin yields superior initial response times for all patients ($ART = 2.00$) at the cost of higher average turnaround time due to frequent context switching.
