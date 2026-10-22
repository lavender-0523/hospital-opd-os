"""
tests/test_simulation.py
Unit tests for OS Hospital Simulation:
- Thread-safe token generation and Mutex lock integrity
- Preemptive Priority Scheduling with Aging
- Round Robin Scheduling time slice distribution
- Performance Metrics calculations
"""

import unittest
from hospital_os.patient import Patient
from hospital_os.synchronization import TokenDispenser, run_concurrency_test
from hospital_os.schedulers import PreemptivePriorityScheduler, RoundRobinScheduler, FCFSScheduler
from hospital_os.metrics import calculate_metrics


class TestHospitalOS(unittest.TestCase):
    def setUp(self):
        self.sample_patients = [
            Patient(101, "Ramesh", 28, "Normal", arrival_time=0, burst_time=6),
            Patient(102, "Sita Devi", 70, "Senior", arrival_time=1, burst_time=4),
            Patient(103, "Kabir (Trauma)", 35, "Emergency", arrival_time=2, burst_time=3),
            Patient(104, "Amit", 24, "Normal", arrival_time=3, burst_time=5),
        ]

    def test_mutex_concurrency(self):
        """Test that TokenDispenser never produces duplicate tokens under multi-threading."""
        result = run_concurrency_test(desks=["D1", "D2", "D3", "D4"], tokens_per_desk=5)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["has_duplicates"])
        tokens = [t[1] for t in result["tokens"]]
        self.assertEqual(len(tokens), 20)
        self.assertEqual(len(set(tokens)), 20)

    def test_priority_scheduling_preemption_and_aging(self):
        """Test Preemptive Priority scheduling, preemption events, and aging."""
        scheduler = PreemptivePriorityScheduler(aging_threshold=5, verbose=False)
        result = scheduler.run(self.sample_patients)

        patients_dict = {p.token_id: p for p in result["patients"]}
        # Emergency patient T103 must complete first among active ones
        self.assertEqual(patients_dict[103].completion_time, 5)
        self.assertEqual(patients_dict[103].waiting_time, 0)

        # Check total time equals sum of burst times (no idle gaps in sample)
        total_burst = sum(p.burst_time for p in self.sample_patients)
        self.assertEqual(result["total_time"], total_burst)

        # Verify aging events occurred
        aging_events = [e for e in result["events"] if e["type"] == "AGING"]
        self.assertGreater(len(aging_events), 0)

    def test_round_robin_diagnostics(self):
        """Test Round Robin time quantum splitting."""
        tq = 2
        scheduler = RoundRobinScheduler(time_quantum=tq, verbose=False)
        result = scheduler.run(self.sample_patients)

        patients_dict = {p.token_id: p for p in result["patients"]}
        self.assertEqual(patients_dict[101].completion_time, 15)
        self.assertEqual(patients_dict[104].completion_time, 18)

        # All patients should have remaining_time == 0
        for p in result["patients"]:
            self.assertEqual(p.remaining_time, 0)
            self.assertEqual(p.turnaround_time, p.completion_time - p.arrival_time)
            self.assertEqual(p.waiting_time, p.turnaround_time - p.burst_time)

    def test_metrics_calculation(self):
        """Test computation of AWT, ATAT, utilization."""
        scheduler = FCFSScheduler(verbose=False)
        result = scheduler.run(self.sample_patients)
        m = calculate_metrics(result["patients"], result["total_time"])
        self.assertAlmostEqual(m["awt"], 5.75, places=2)
        self.assertAlmostEqual(m["atat"], 10.25, places=2)
        self.assertEqual(m["utilization"], 100.0)


if __name__ == "__main__":
    unittest.main()
