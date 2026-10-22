/**
 * Hospital OPD OS - Process Scheduling & Concurrency Simulator
 * MediQueue OS • Interactive Front-End Engine
 */

// Initial default patient batch (matching coursework specification)
const DEFAULT_PATIENTS = [
  { token_id: 101, name: "Ramesh", age: 28, category: "Normal", arrival_time: 0, burst_time: 6 },
  { token_id: 102, name: "Sita Devi", age: 70, category: "Senior", arrival_time: 1, burst_time: 4 },
  { token_id: 103, name: "Kabir (Trauma)", age: 35, category: "Emergency", arrival_time: 2, burst_time: 3 },
  { token_id: 104, name: "Amit", age: 24, category: "Normal", arrival_time: 3, burst_time: 5 },
];

const PRESETS = {
  default: [
    { token_id: 101, name: "Ramesh", age: 28, category: "Normal", arrival_time: 0, burst_time: 6 },
    { token_id: 102, name: "Sita Devi", age: 70, category: "Senior", arrival_time: 1, burst_time: 4 },
    { token_id: 103, name: "Kabir (Trauma)", age: 35, category: "Emergency", arrival_time: 2, burst_time: 3 },
    { token_id: 104, name: "Amit", age: 24, category: "Normal", arrival_time: 3, burst_time: 5 },
  ],
  emergency_inflow: [
    { token_id: 201, name: "Vikas (Checkup)", age: 30, category: "Normal", arrival_time: 0, burst_time: 7 },
    { token_id: 202, name: "Cardiac Arrest", age: 58, category: "Emergency", arrival_time: 1, burst_time: 4 },
    { token_id: 203, name: "Stroke Patient", age: 62, category: "Emergency", arrival_time: 3, burst_time: 3 },
    { token_id: 204, name: "Senior Ortho", age: 75, category: "Senior", arrival_time: 4, burst_time: 5 },
  ],
  aging_demo: [
    { token_id: 301, name: "Long Waiter A", age: 22, category: "Normal", arrival_time: 0, burst_time: 8 },
    { token_id: 302, name: "Emergency 1", age: 40, category: "Emergency", arrival_time: 1, burst_time: 4 },
    { token_id: 303, name: "Emergency 2", age: 35, category: "Emergency", arrival_time: 4, burst_time: 4 },
    { token_id: 304, name: "Emergency 3", age: 50, category: "Emergency", arrival_time: 7, burst_time: 3 },
  ]
};

// Application State
const state = {
  patients: JSON.parse(JSON.stringify(DEFAULT_PATIENTS)),
  activeTab: "priority", // "priority", "rr", "concurrency", "compare"
  currentSimResult: null,
  stepIndex: 0,
  isPlaying: false,
  playbackTimer: null,
  playbackSpeed: 600, // ms per tick
  nextCustomToken: 105,

  // Concurrency Playground State
  tokenCounter: 100,
  isMutexLocked: false,
  deskHistory: []
};

// Priority mapping: 1 (Emergency) is highest, 3 (Normal) is lowest
function getPriority(category) {
  if (category === "Emergency") return 1;
  if (category === "Senior") return 2;
  return 3;
}

/* ==========================================================================
   SIMULATION ENGINES (PURE CLIENT-SIDE JAVASCRIPT MATCHING PYTHON EXACTLY)
   ========================================================================== */

function compressGantt(rawGantt) {
  if (!rawGantt || rawGantt.length === 0) return [];
  const compressed = [[rawGantt[0][0], rawGantt[0][1], rawGantt[0][2]]];
  for (let i = 1; i < rawGantt.length; i++) {
    const [pid, start, end] = rawGantt[i];
    const last = compressed[compressed.length - 1];
    if (pid === last[0] && start === last[2]) {
      last[2] = end;
    } else {
      compressed.push([pid, start, end]);
    }
  }
  return compressed;
}

// 1. Preemptive Priority Scheduling with Aging
function simulatePriority(patientList, agingThreshold = 5) {
  const patients = patientList.map(p => ({
    ...p,
    priority: getPriority(p.category),
    initial_priority: getPriority(p.category),
    remaining_time: p.burst_time,
    completion_time: 0,
    turnaround_time: 0,
    waiting_time: 0,
    response_time: 0,
    first_response_time: null,
    aged_times: 0
  }));

  let currentTime = 0;
  const completed = [];
  const rawGantt = [];
  const events = [];
  const timelineTicks = [];
  let lastPatient = null;
  const totalPatients = patients.length;

  while (completed.length < totalPatients) {
    // 1. Aging check: boost priority if a waiting patient has waited >= agingThreshold
    for (const p of patients) {
      if (p.arrival_time <= currentTime && p.remaining_time > 0) {
        const waitSoFar = currentTime - p.arrival_time;
        if (waitSoFar >= agingThreshold && p.priority > 1) {
          const oldPrio = p.priority;
          p.priority -= 1;
          p.aged_times += 1;
          events.push({
            type: "AGING",
            time: currentTime,
            token_id: p.token_id,
            name: p.name,
            old_priority: oldPrio,
            new_priority: p.priority,
            message: `[AGING at t=${currentTime}] Token #${p.token_id} (${p.name}) waited ${waitSoFar} units -> Priority elevated to ${p.priority}`
          });
        }
      }
    }

    // 2. Pick highest priority available patient
    const available = patients.filter(p => p.arrival_time <= currentTime && p.remaining_time > 0);
    if (available.length === 0) {
      rawGantt.push(["IDLE", currentTime, currentTime + 1]);
      timelineTicks.push({
        time: currentTime,
        running: "IDLE",
        ready: [],
        patientsSnapshot: JSON.parse(JSON.stringify(patients))
      });
      currentTime += 1;
      continue;
    }

    available.sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority;
      return a.arrival_time - b.arrival_time;
    });

    const currentP = available[0];

    // First Response Time
    if (currentP.first_response_time === null) {
      currentP.first_response_time = currentTime;
      currentP.response_time = currentTime - currentP.arrival_time;
    }

    // 3. Preemption detection
    if (lastPatient && lastPatient.token_id !== currentP.token_id && lastPatient.remaining_time > 0) {
      events.push({
        type: "PREEMPTION",
        time: currentTime,
        token_id: currentP.token_id,
        preempted_id: lastPatient.token_id,
        message: `[PREEMPTION at t=${currentTime}] Emergency Token #${currentP.token_id} preempted Doctor from Token #${lastPatient.token_id}`
      });
    }

    // Record timeline step
    timelineTicks.push({
      time: currentTime,
      running: currentP.token_id,
      ready: available.filter(p => p.token_id !== currentP.token_id).map(p => p.token_id),
      patientsSnapshot: JSON.parse(JSON.stringify(patients))
    });

    // Execute 1 time unit
    rawGantt.push([currentP.token_id, currentTime, currentTime + 1]);
    currentP.remaining_time -= 1;
    lastPatient = currentP;
    currentTime += 1;

    // Check completion
    if (currentP.remaining_time === 0) {
      currentP.completion_time = currentTime;
      currentP.turnaround_time = currentP.completion_time - currentP.arrival_time;
      currentP.waiting_time = currentP.turnaround_time - currentP.burst_time;
      completed.push(currentP);
      events.push({
        type: "COMPLETED",
        time: currentTime,
        token_id: currentP.token_id,
        message: `Token #${currentP.token_id} (${currentP.name}) completed checkup at t=${currentTime}`
      });
    }
  }

  // Final tick snapshot
  timelineTicks.push({
    time: currentTime,
    running: null,
    ready: [],
    patientsSnapshot: JSON.parse(JSON.stringify(patients))
  });

  return {
    algorithm: "Preemptive Priority (with Aging)",
    patients,
    raw_gantt: rawGantt,
    gantt: compressGantt(rawGantt),
    events,
    timeline: timelineTicks,
    total_time: currentTime
  };
}

// 2. Round Robin Scheduling
function simulateRoundRobin(patientList, timeQuantum = 2) {
  const patients = patientList.map(p => ({
    ...p,
    priority: getPriority(p.category),
    initial_priority: getPriority(p.category),
    remaining_time: p.burst_time,
    completion_time: 0,
    turnaround_time: 0,
    waiting_time: 0,
    response_time: 0,
    first_response_time: null,
    aged_times: 0
  }));

  patients.sort((a, b) => a.arrival_time - b.arrival_time);
  const queue = [];
  const ganttChart = [];
  const events = [];
  const timelineTicks = [];
  let currentTime = 0;
  const completed = [];
  const visited = new Set();

  function addArrivedPatients(t) {
    for (const p of patients) {
      if (p.arrival_time <= t && !visited.has(p.token_id) && p.remaining_time > 0) {
        queue.push(p);
        visited.add(p.token_id);
      }
    }
  }

  addArrivedPatients(currentTime);

  while (completed.length < patients.length) {
    if (queue.length === 0) {
      ganttChart.push(["IDLE", currentTime, currentTime + 1]);
      timelineTicks.push({
        time: currentTime,
        running: "IDLE",
        ready: [],
        patientsSnapshot: JSON.parse(JSON.stringify(patients))
      });
      currentTime += 1;
      addArrivedPatients(currentTime);
      continue;
    }

    const curr = queue.shift();
    if (curr.first_response_time === null) {
      curr.first_response_time = currentTime;
      curr.response_time = currentTime - curr.arrival_time;
    }

    const timeSlice = Math.min(curr.remaining_time, timeQuantum);
    const startTime = currentTime;

    for (let s = 0; s < timeSlice; s++) {
      timelineTicks.push({
        time: currentTime + s,
        running: curr.token_id,
        ready: queue.map(p => p.token_id),
        patientsSnapshot: JSON.parse(JSON.stringify(patients))
      });
    }

    currentTime += timeSlice;
    curr.remaining_time -= timeSlice;
    ganttChart.push([curr.token_id, startTime, currentTime]);

    addArrivedPatients(currentTime);

    if (curr.remaining_time > 0) {
      queue.push(curr);
      events.push({
        type: "QUANTUM_EXPIRED",
        time: currentTime,
        token_id: curr.token_id,
        message: `Token #${curr.token_id} quantum expired, returned to ready queue`
      });
    } else {
      curr.completion_time = currentTime;
      curr.turnaround_time = curr.completion_time - curr.arrival_time;
      curr.waiting_time = curr.turnaround_time - curr.burst_time;
      completed.push(curr);
      events.push({
        type: "COMPLETED",
        time: currentTime,
        token_id: curr.token_id,
        message: `Token #${curr.token_id} (${curr.name}) diagnostics completed at t=${currentTime}`
      });
    }
  }

  timelineTicks.push({
    time: currentTime,
    running: null,
    ready: [],
    patientsSnapshot: JSON.parse(JSON.stringify(patients))
  });

  return {
    algorithm: `Round Robin (TQ=${timeQuantum})`,
    patients,
    raw_gantt: ganttChart,
    gantt: ganttChart,
    events,
    timeline: timelineTicks,
    total_time: currentTime
  };
}

// 3. First-Come First-Served (FCFS)
function simulateFCFS(patientList) {
  const patients = patientList.map(p => ({
    ...p,
    priority: getPriority(p.category),
    remaining_time: 0,
    completion_time: 0,
    turnaround_time: 0,
    waiting_time: 0,
    response_time: 0
  }));

  patients.sort((a, b) => a.arrival_time - b.arrival_time);
  let currentTime = 0;
  const gantt = [];

  for (const p of patients) {
    if (currentTime < p.arrival_time) {
      gantt.push(["IDLE", currentTime, p.arrival_time]);
      currentTime = p.arrival_time;
    }
    const startTime = currentTime;
    p.response_time = currentTime - p.arrival_time;
    currentTime += p.burst_time;
    p.completion_time = currentTime;
    p.turnaround_time = p.completion_time - p.arrival_time;
    p.waiting_time = p.turnaround_time - p.burst_time;
    gantt.push([p.token_id, startTime, currentTime]);
  }

  return {
    algorithm: "First-Come First-Served (FCFS)",
    patients,
    gantt,
    total_time: currentTime
  };
}

function calculateMetrics(patients, totalTime) {
  const n = patients.length;
  if (!n || !totalTime) return { awt: 0, atat: 0, art: 0, utilization: 0 };
  const totalWT = patients.reduce((acc, p) => acc + p.waiting_time, 0);
  const totalTAT = patients.reduce((acc, p) => acc + p.turnaround_time, 0);
  const totalRT = patients.reduce((acc, p) => acc + (p.response_time || 0), 0);
  const totalBurst = patients.reduce((acc, p) => acc + p.burst_time, 0);

  return {
    awt: (totalWT / n).toFixed(2),
    atat: (totalTAT / n).toFixed(2),
    art: (totalRT / n).toFixed(2),
    utilization: ((totalBurst / totalTime) * 100).toFixed(1)
  };
}

/* ==========================================================================
   UI RENDERING AND CONTROLS
   ========================================================================== */

function getPatientCategoryColor(category) {
  if (category === "Emergency") return "#ffffff";
  if (category === "Senior") return "#8e8e93";
  return "#242426";
}

function renderKPIs(metrics, simResult) {
  document.getElementById("kpi-awt").textContent = metrics.awt;
  document.getElementById("kpi-atat").textContent = metrics.atat;
  document.getElementById("kpi-art").textContent = metrics.art;
  document.getElementById("kpi-util").textContent = `${metrics.utilization}%`;

  const preemptCount = simResult.events ? simResult.events.filter(e => e.type === "PREEMPTION").length : 0;
  const agingCount = simResult.events ? simResult.events.filter(e => e.type === "AGING").length : 0;
  const eventBadge = document.getElementById("kpi-events-count");
  if (eventBadge) {
    eventBadge.textContent = `${preemptCount} Preempt | ${agingCount} Aged`;
  }
}

function renderGanttChart(gantt, totalTime, patients) {
  const track = document.getElementById("gantt-track");
  const ruler = document.getElementById("gantt-ruler");
  track.innerHTML = "";
  ruler.innerHTML = "";

  if (!gantt || gantt.length === 0) return;

  const patientMap = {};
  patients.forEach(p => { patientMap[p.token_id] = p; });

  // Render Blocks
  gantt.forEach(([pid, start, end]) => {
    const duration = end - start;
    const widthPct = (duration / totalTime) * 100;
    const block = document.createElement("div");
    block.className = `gantt-block ${pid === "IDLE" ? "idle" : ""}`;
    block.style.width = `${widthPct}%`;

    if (pid !== "IDLE") {
      const p = patientMap[pid];
      const cat = p ? p.category : "Normal";
      if (cat === "Emergency") {
        block.style.background = "#ffffff";
        block.style.color = "#000000";
        block.style.border = "1px solid #ffffff";
      } else if (cat === "Senior") {
        block.style.background = "#8e8e93";
        block.style.color = "#000000";
        block.style.border = "1px solid #aeaeb2";
      } else {
        block.style.background = "#242426";
        block.style.color = "#ffffff";
        block.style.border = "1px solid #48484a";
      }
      block.innerHTML = `<span>T${pid}</span>`;

      // Tooltip listener
      block.addEventListener("mouseenter", (e) => {
        showTooltip(e, `
          <strong>Token #${pid} - ${p ? p.name : 'Unknown'}</strong><br/>
          Category: <span class="cat-badge cat-${cat}">${cat}</span><br/>
          Execution: t=${start} to t=${end} (${duration} units)
        `);
      });
      block.addEventListener("mouseleave", hideTooltip);
    } else {
      block.innerHTML = `<span>IDLE</span>`;
      block.addEventListener("mouseenter", (e) => {
        showTooltip(e, `<strong>Doctor Idle</strong><br/>No patients available (t=${start} to t=${end})`);
      });
      block.addEventListener("mouseleave", hideTooltip);
    }

    track.appendChild(block);
  });

  // Render Ruler ticks
  for (let t = 0; t <= totalTime; t++) {
    // Only show ticks for reasonable density
    if (totalTime > 25 && t % 2 !== 0 && t !== totalTime) continue;
    const tick = document.createElement("div");
    tick.className = "ruler-tick";
    tick.style.left = `${(t / totalTime) * 100}%`;
    tick.innerHTML = `<span>${t}</span>`;
    ruler.appendChild(tick);
  }
}

function renderTable(patients) {
  const tbody = document.getElementById("metrics-table-body");
  tbody.innerHTML = "";

  patients.forEach(p => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="mono-cell">T${p.token_id}</td>
      <td style="font-weight:600;">${p.name}</td>
      <td><span class="cat-badge cat-${p.category}">${p.category}</span></td>
      <td class="mono-cell">${p.arrival_time}</td>
      <td class="mono-cell">${p.burst_time}</td>
      <td class="mono-cell" style="font-weight:700;">${p.completion_time}</td>
      <td class="mono-cell">${p.turnaround_time}</td>
      <td class="mono-cell" style="font-weight:700;">${p.waiting_time}</td>
      <td class="mono-cell">${p.response_time !== undefined ? p.response_time : '-'}</td>
    `;
    tbody.appendChild(row);
  });
}

function renderEventFeed(events) {
  const feed = document.getElementById("event-feed");
  feed.innerHTML = "";
  if (!events || events.length === 0) {
    feed.innerHTML = `<div style="color:var(--text-dim);">No events triggered yet.</div>`;
    return;
  }

  events.forEach(evt => {
    const line = document.createElement("div");
    line.className = "event-line";

    let colorClass = "event-completed";
    let icon = "✓";
    if (evt.type === "PREEMPTION") {
      colorClass = "event-preempt";
      icon = "⚡";
    } else if (evt.type === "AGING") {
      colorClass = "event-aging";
      icon = "⏳";
    }

    line.innerHTML = `
      <span class="event-time">[t=${evt.time}]</span>
      <span class="${colorClass}">${icon} ${evt.message}</span>
    `;
    feed.appendChild(line);
  });
}

function renderTimelineStep(stepIdx) {
  const sim = state.currentSimResult;
  if (!sim || !sim.timeline || sim.timeline.length === 0) return;

  const currentTick = sim.timeline[Math.min(stepIdx, sim.timeline.length - 1)];
  document.getElementById("current-tick-display").textContent = `t = ${currentTick.time}`;

  const doctorStage = document.getElementById("doctor-stage");
  const doctorAvatar = document.getElementById("doctor-avatar");
  const activeBadge = document.getElementById("active-patient-badge");
  const waitingList = document.getElementById("queue-list");

  waitingList.innerHTML = "";

  if (currentTick.running && currentTick.running !== "IDLE") {
    doctorStage.classList.add("active");
    const activePatient = sim.patients.find(p => p.token_id === currentTick.running);
    doctorAvatar.innerHTML = `🩺`;
    activeBadge.style.display = "inline-block";
    activeBadge.className = `active-patient-badge cat-${activePatient.category}`;
    activeBadge.textContent = `T${activePatient.token_id}: ${activePatient.name} (Running)`;
  } else if (currentTick.running === "IDLE") {
    doctorStage.classList.remove("active");
    doctorAvatar.innerHTML = `💤`;
    activeBadge.style.display = "inline-block";
    activeBadge.className = `active-patient-badge`;
    activeBadge.style.background = `var(--idle-color)`;
    activeBadge.style.color = `#fff`;
    activeBadge.textContent = "Doctor is Idle (No Patients)";
  } else {
    doctorStage.classList.remove("active");
    doctorAvatar.innerHTML = `🏥`;
    activeBadge.style.display = "inline-block";
    activeBadge.className = `active-patient-badge`;
    activeBadge.style.background = `rgba(16, 185, 129, 0.2)`;
    activeBadge.style.color = `#34d399`;
    activeBadge.textContent = "All Consultations Completed!";
  }

  // Populate Ready Queue
  if (currentTick.ready.length === 0) {
    waitingList.innerHTML = `<div style="color:var(--text-dim); padding:10px; text-align:center;">Queue is empty</div>`;
  } else {
    currentTick.ready.forEach(tid => {
      const p = sim.patients.find(pt => pt.token_id === tid);
      if (!p) return;
      const item = document.createElement("div");
      item.className = "queue-item";
      item.innerHTML = `
        <div class="queue-item-left">
          <span class="queue-token">T${p.token_id}</span>
          <div>
            <div class="queue-name">${p.name}</div>
            <div class="queue-meta">Arrival: ${p.arrival_time} | Burst Left: ${p.remaining_time}</div>
          </div>
        </div>
        <span class="cat-badge cat-${p.category}">${p.category}</span>
      `;
      waitingList.appendChild(item);
    });
  }
}

function runCurrentSimulation() {
  const algo = state.activeTab;
  let result;

  if (algo === "priority") {
    const threshold = parseInt(document.getElementById("aging-input").value) || 5;
    result = simulatePriority(state.patients, threshold);
  } else if (algo === "rr") {
    const tq = parseInt(document.getElementById("tq-input").value) || 2;
    result = simulateRoundRobin(state.patients, tq);
  } else {
    result = simulatePriority(state.patients, 5);
  }

  state.currentSimResult = result;
  state.stepIndex = 0;

  const metrics = calculateMetrics(result.patients, result.total_time);
  renderKPIs(metrics, result);
  renderGanttChart(result.gantt, result.total_time, result.patients);
  renderTable(result.patients);
  renderEventFeed(result.events);
  renderTimelineStep(0);
}

function renderComparisonTab() {
  const priorityRes = simulatePriority(state.patients, 5);
  const rr2Res = simulateRoundRobin(state.patients, 2);
  const rr3Res = simulateRoundRobin(state.patients, 3);
  const fcfsRes = simulateFCFS(state.patients);

  const list = [priorityRes, rr2Res, rr3Res, fcfsRes];
  const grid = document.getElementById("comparison-grid");
  grid.innerHTML = "";

  list.forEach(res => {
    const m = calculateMetrics(res.patients, res.total_time);
    const card = document.createElement("div");
    card.className = "algo-card";
    if (res.algorithm.includes("Priority")) {
      card.classList.add("best");
    }

    card.innerHTML = `
      <div class="algo-header">
        <div class="algo-title">${res.algorithm}</div>
        ${res.algorithm.includes("Priority") ? '<span class="cat-badge cat-Emergency">Triage Preferred</span>' : ''}
      </div>
      <div class="stat-row">
        <span class="stat-name">Average Waiting Time (AWT)</span>
        <span class="stat-val">${m.awt}</span>
      </div>
      <div class="stat-row">
        <span class="stat-name">Average Turnaround (ATAT)</span>
        <span class="stat-val">${m.atat}</span>
      </div>
      <div class="stat-row">
        <span class="stat-name">Average Response Time (ART)</span>
        <span class="stat-val">${m.art}</span>
      </div>
      <div class="stat-row">
        <span class="stat-name">Resource Utilization</span>
        <span class="stat-val">${m.utilization}%</span>
      </div>
      <div class="stat-row">
        <span class="stat-name">Total Execution Time</span>
        <span class="stat-val">${res.total_time} units</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

/* ==========================================================================
   CONCURRENCY & MUTEX CRITICAL SECTION DEMO
   ========================================================================== */

function initConcurrencyPlayground() {
  const deskCards = ["Desk-A", "Desk-B", "Desk-C"].map(id => document.getElementById(`desk-${id.toLowerCase()}`));
  updateLockStatus(false);
}

function updateLockStatus(isLocked, deskOwner = "") {
  state.isMutexLocked = isLocked;
  const badge = document.getElementById("mutex-lock-badge");
  if (!badge) return;

  if (isLocked) {
    badge.className = "lock-state-badge lock-locked";
    badge.innerHTML = `🔒 MUTEX LOCKED [Owner: ${deskOwner}]`;
  } else {
    badge.className = "lock-state-badge lock-unlocked";
    badge.innerHTML = `🔓 MUTEX UNLOCKED [Resource Available]`;
  }
}

async function simulateDeskTokenRequest(deskName, delay = 600) {
  const deskEl = document.getElementById(`desk-${deskName.toLowerCase()}`);
  const logFeed = document.getElementById("concurrency-log");
  const useMutex = document.getElementById("toggle-mutex").checked;

  if (useMutex) {
    // Wait if lock is held (Entry Section)
    while (state.isMutexLocked) {
      await new Promise(r => setTimeout(r, 50));
    }

    // Acquire Lock
    updateLockStatus(true, deskName);
    if (deskEl) deskEl.classList.add("in-cs");

    // Critical Section
    await new Promise(r => setTimeout(r, delay));
    state.tokenCounter += 1;
    const issuedToken = state.tokenCounter;

    // Log event
    const logLine = document.createElement("div");
    logLine.className = "event-line";
    logLine.innerHTML = `<span class="event-time">[Safe Mutex]</span> <strong>${deskName}</strong> generated Token <span class="mono-cell" style="font-weight:700;">#${issuedToken}</span>`;
    logFeed.prepend(logLine);

    document.getElementById("shared-token-display").textContent = `#${issuedToken}`;
    if (deskEl) {
      deskEl.querySelector(".desk-last-token").textContent = `Token #${issuedToken}`;
      deskEl.classList.remove("in-cs");
    }

    // Exit Section
    updateLockStatus(false);
  } else {
    // Race Condition: No Lock!
    if (deskEl) deskEl.classList.add("in-cs");
    const current = state.tokenCounter;
    await new Promise(r => setTimeout(r, delay));
    state.tokenCounter = current + 1;
    const issuedToken = state.tokenCounter;

    const logLine = document.createElement("div");
    logLine.className = "event-line";
    logLine.innerHTML = `<span class="event-time" style="text-decoration:underline;">[UNSAFE RACE]</span> <strong>${deskName}</strong> wrote Token #${issuedToken} (Risk of Duplicate!)`;
    logFeed.prepend(logLine);

    document.getElementById("shared-token-display").textContent = `#${issuedToken}`;
    if (deskEl) {
      deskEl.querySelector(".desk-last-token").textContent = `Token #${issuedToken}`;
      deskEl.classList.remove("in-cs");
    }
  }
}

function simulateConcurrentBursts() {
  simulateDeskTokenRequest("Desk-A", 400);
  setTimeout(() => simulateDeskTokenRequest("Desk-B", 400), 100);
  setTimeout(() => simulateDeskTokenRequest("Desk-C", 400), 200);
}

/* ==========================================================================
   TOOLTIPS & MODAL
   ========================================================================== */

const tooltip = document.getElementById("global-tooltip");

function showTooltip(e, html) {
  tooltip.innerHTML = html;
  tooltip.style.display = "block";
  tooltip.style.left = `${e.pageX + 12}px`;
  tooltip.style.top = `${e.pageY + 12}px`;
}

function hideTooltip() {
  tooltip.style.display = "none";
}

/* ==========================================================================
   EVENT LISTENERS & INITIALIZATION
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeTab = btn.dataset.tab;

      // Toggle views
      const theaterView = document.getElementById("theater-view");
      const concurrencyView = document.getElementById("concurrency-view");
      const compareView = document.getElementById("compare-view");

      if (state.activeTab === "concurrency") {
        theaterView.style.display = "none";
        concurrencyView.style.display = "block";
        compareView.style.display = "none";
      } else if (state.activeTab === "compare") {
        theaterView.style.display = "none";
        concurrencyView.style.display = "none";
        compareView.style.display = "block";
        renderComparisonTab();
      } else {
        theaterView.style.display = "block";
        concurrencyView.style.display = "none";
        compareView.style.display = "none";

        // Show/hide algorithm specific controls
        const agingGroup = document.getElementById("aging-group");
        const tqGroup = document.getElementById("tq-group");
        if (state.activeTab === "priority") {
          agingGroup.style.display = "flex";
          tqGroup.style.display = "none";
        } else {
          agingGroup.style.display = "none";
          tqGroup.style.display = "flex";
        }

        runCurrentSimulation();
      }
    });
  });

  // Controls
  document.getElementById("btn-run-sim").addEventListener("click", runCurrentSimulation);

  document.getElementById("btn-play").addEventListener("click", () => {
    if (state.isPlaying) {
      clearInterval(state.playbackTimer);
      state.isPlaying = false;
      document.getElementById("btn-play").innerHTML = "▶ Play";
    } else {
      state.isPlaying = true;
      document.getElementById("btn-play").innerHTML = "⏸ Pause";
      state.playbackTimer = setInterval(() => {
        if (!state.currentSimResult || state.stepIndex >= state.currentSimResult.timeline.length - 1) {
          clearInterval(state.playbackTimer);
          state.isPlaying = false;
          document.getElementById("btn-play").innerHTML = "▶ Play";
          return;
        }
        state.stepIndex++;
        renderTimelineStep(state.stepIndex);
      }, state.playbackSpeed);
    }
  });

  document.getElementById("btn-step").addEventListener("click", () => {
    if (!state.currentSimResult) return;
    if (state.stepIndex < state.currentSimResult.timeline.length - 1) {
      state.stepIndex++;
      renderTimelineStep(state.stepIndex);
    }
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    if (state.playbackTimer) clearInterval(state.playbackTimer);
    state.isPlaying = false;
    document.getElementById("btn-play").innerHTML = "▶ Play";
    state.stepIndex = 0;
    renderTimelineStep(0);
  });

  document.getElementById("speed-select").addEventListener("change", (e) => {
    state.playbackSpeed = parseInt(e.target.value);
    if (state.isPlaying) {
      clearInterval(state.playbackTimer);
      state.playbackTimer = setInterval(() => {
        if (!state.currentSimResult || state.stepIndex >= state.currentSimResult.timeline.length - 1) {
          clearInterval(state.playbackTimer);
          state.isPlaying = false;
          document.getElementById("btn-play").innerHTML = "▶ Play";
          return;
        }
        state.stepIndex++;
        renderTimelineStep(state.stepIndex);
      }, state.playbackSpeed);
    }
  });

  // Presets
  document.getElementById("preset-select").addEventListener("change", (e) => {
    const key = e.target.value;
    if (PRESETS[key]) {
      state.patients = JSON.parse(JSON.stringify(PRESETS[key]));
      runCurrentSimulation();
    }
  });

  // Add Patient Modal
  const modal = document.getElementById("patient-modal");
  document.getElementById("btn-add-patient-modal").addEventListener("click", () => {
    document.getElementById("input-token").value = state.nextCustomToken;
    document.getElementById("input-name").value = "";
    document.getElementById("input-age").value = 30;
    document.getElementById("input-at").value = 0;
    document.getElementById("input-bt").value = 4;
    modal.classList.add("active");
  });

  document.getElementById("modal-cancel").addEventListener("click", () => {
    modal.classList.remove("active");
  });

  document.getElementById("modal-save").addEventListener("click", () => {
    const tid = parseInt(document.getElementById("input-token").value) || state.nextCustomToken;
    const name = document.getElementById("input-name").value.trim() || `Patient #${tid}`;
    const age = parseInt(document.getElementById("input-age").value) || 30;
    const cat = document.getElementById("input-cat").value;
    const at = parseInt(document.getElementById("input-at").value) || 0;
    const bt = parseInt(document.getElementById("input-bt").value) || 1;

    state.patients.push({
      token_id: tid,
      name,
      age,
      category: cat,
      arrival_time: at,
      burst_time: bt
    });
    state.nextCustomToken = Math.max(state.nextCustomToken, tid + 1);
    modal.classList.remove("active");
    runCurrentSimulation();
  });

  // Concurrency Playground Buttons
  document.getElementById("btn-req-a").addEventListener("click", () => simulateDeskTokenRequest("Desk-A"));
  document.getElementById("btn-req-b").addEventListener("click", () => simulateDeskTokenRequest("Desk-B"));
  document.getElementById("btn-req-c").addEventListener("click", () => simulateDeskTokenRequest("Desk-C"));
  document.getElementById("btn-req-all").addEventListener("click", simulateConcurrentBursts);
  document.getElementById("btn-reset-tokens").addEventListener("click", () => {
    state.tokenCounter = 100;
    document.getElementById("shared-token-display").textContent = "#100";
    document.getElementById("concurrency-log").innerHTML = "";
    document.querySelectorAll(".desk-last-token").forEach(el => el.textContent = "Token #---");
  });

  // Initial Run
  runCurrentSimulation();
});
