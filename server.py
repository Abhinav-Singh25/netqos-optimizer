"""
+==============================================================================+
|                     NetQoS Optimizer -- Python Backend                        |
|                                                                              |
|   Dual-Stage Network Optimization Architecture:                              |
|                                                                              |
|   PROBLEM 1 (Macro Level):                                                   |
|       Load Balancing via Priority Queue (Min-Heap)                           |
|       -> Distributes students across campus routers using heapq              |
|       -> Always assigns to the least-congested router: O(log N)              |
|                                                                              |
|   PROBLEM 2 (Micro Level):                                                   |
|       Packet Prioritization via 0/1 Knapsack Dynamic Programming             |
|       -> Maximizes total priority score under bandwidth constraints          |
|       -> Guarantees critical academic traffic (VTOP) is never dropped        |
|       -> Time Complexity: O(n * W), Space: O(n * W)                          |
|                                                                              |
|   Team:  Abhinav Kumar Singh (25BCE2258)                                     |
|   Course: Data Structures & Algorithms -- VIT Vellore                        |
+==============================================================================+
"""

import os
import random
import heapq
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict


# ═══════════════════════════════════════════════════════════════════════════════
#  FastAPI Application Setup
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="NetQoS Optimizer API",
    description="Dual-stage network optimization using Min-Heap Load Balancing and 0/1 Knapsack DP",
    version="2.0.0"
)

# CORS — Allow the frontend HTML page to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROBLEM 2: 0/1 Knapsack — Packet Prioritization
# ═══════════════════════════════════════════════════════════════════════════════

# ── Packet Data Structure ─────────────────────────────────────────────────────
class Packet:
    """Represents a single network packet with type, size (weight), and priority (value)."""

    def __init__(self, id: int, packet_type: str, size: int, priority: int):
        self.id = id
        self.packet_type = packet_type
        self.size = size            # Weight in Knapsack terms
        self.priority = priority    # Value in Knapsack terms

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "packet_type": self.packet_type,
            "size": self.size,
            "priority": self.priority,
        }


# ── Dynamic Packet Generator ─────────────────────────────────────────────────
TRAFFIC_PROFILES = {
    "VTOP":     {"size_range": (8, 22),   "priority_range": (85, 99)},
    "Zoom":     {"size_range": (30, 55),  "priority_range": (70, 88)},
    "YouTube":  {"size_range": (45, 100), "priority_range": (15, 38)},
    "Netflix":  {"size_range": (50, 110), "priority_range": (12, 35)},
    "Download": {"size_range": (120, 170),"priority_range": (3, 15)},
}

DEFAULT_WEIGHTS = {
    "VTOP": 15,
    "Zoom": 10,
    "YouTube": 30,
    "Netflix": 20,
    "Download": 25,
}


def packet_generator(num_packets: int, weights: Optional[Dict[str, int]] = None) -> List[Packet]:
    """Generate network packets with a realistic traffic distribution."""
    packets: List[Packet] = []
    w = weights if weights else DEFAULT_WEIGHTS
    types = list(w.keys())
    type_weights = [w[t] for t in types]
    total_weight = sum(type_weights)
    probabilities = [tw / total_weight for tw in type_weights]

    for packet_id in range(1, num_packets + 1):
        chosen_type = random.choices(types, weights=probabilities, k=1)[0]
        profile = TRAFFIC_PROFILES.get(chosen_type, TRAFFIC_PROFILES["YouTube"])
        size = random.randint(*profile["size_range"])
        priority = random.randint(*profile["priority_range"])
        packets.append(Packet(packet_id, chosen_type, size, priority))

    return packets


# ── 0/1 Knapsack Dynamic Programming Algorithm ───────────────────────────────
def optimize_packets(packets: List[Packet], bandwidth_limit: int) -> dict:
    """
    Classic 0/1 Knapsack using bottom-up Dynamic Programming.

    Time Complexity:  O(n * W)
    Space Complexity: O(n * W)
    """
    n = len(packets)
    W = bandwidth_limit
    weights = [p.size for p in packets]
    values = [p.priority for p in packets]

    # Build the DP table
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(W + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    dp[i - 1][w],
                    values[i - 1] + dp[i - 1][w - weights[i - 1]]
                )
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtrack to find the selected packets
    max_priority = dp[n][W]
    selected: List[Packet] = []
    i, w = n, W

    while i > 0 and w > 0:
        if dp[i][w] != dp[i - 1][w]:
            selected.append(packets[i - 1])
            w -= weights[i - 1]
        i -= 1

    selected.reverse()

    selected_ids = set(p.id for p in selected)
    dropped = [p for p in packets if p.id not in selected_ids]
    bw_used = sum(p.size for p in selected)
    pct = round(bw_used / bandwidth_limit * 100, 1) if bandwidth_limit > 0 else 0

    return {
        "selected_packets":     [p.to_dict() for p in selected],
        "dropped_packets":      [p.to_dict() for p in dropped],
        "selected_count":       len(selected),
        "dropped_count":        len(dropped),
        "max_priority":         max_priority,
        "total_bandwidth_used": bw_used,
        "bandwidth_limit":      bandwidth_limit,
        "bandwidth_utilization": pct,
    }


# ── FIFO (Normal Router) Simulation ──────────────────────────────────────────
def fifo_simulate(packets: List[Packet], bandwidth_limit: int) -> dict:
    """Simulates a traditional router with no QoS intelligence."""
    sorted_packets = sorted(packets, key=lambda p: p.size, reverse=True)
    selected: List[Packet] = []
    dropped: List[Packet] = []
    used_bw = 0

    for p in sorted_packets:
        if used_bw + p.size <= bandwidth_limit:
            selected.append(p)
            used_bw += p.size
        else:
            dropped.append(p)

    max_priority = sum(p.priority for p in selected)
    pct = round(used_bw / bandwidth_limit * 100, 1) if bandwidth_limit > 0 else 0

    return {
        "selected_packets":     [p.to_dict() for p in selected],
        "dropped_packets":      [p.to_dict() for p in dropped],
        "selected_count":       len(selected),
        "dropped_count":        len(dropped),
        "max_priority":         max_priority,
        "total_bandwidth_used": used_bw,
        "bandwidth_limit":      bandwidth_limit,
        "bandwidth_utilization": pct,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  PROBLEM 1: SmartMesh Load Balancer — Min-Heap (Priority Queue)
# ═══════════════════════════════════════════════════════════════════════════════

class Router:
    """
    Represents a physical Wi-Fi access point inside the library.
    The Min-Heap uses active_users for comparison so the least-loaded
    router is always at the top of the heap.
    """

    def __init__(self, name: str, capacity: int, location: str):
        self.name = name
        self.capacity = capacity
        self.location = location
        self.active_users = 0
        self.assignment_log: List[int] = []

    def load_percentage(self) -> float:
        return round(self.active_users / self.capacity * 100, 1) if self.capacity > 0 else 0

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "capacity":         self.capacity,
            "location":         self.location,
            "active_users":     self.active_users,
            "load_percentage":  self.load_percentage(),
            "remaining":        self.capacity - self.active_users,
            "assignment_log":   self.assignment_log,
        }

    # Heap comparison: least-loaded router at top
    def __lt__(self, other):
        return self.active_users < other.active_users

    def __eq__(self, other):
        return self.active_users == other.active_users


LIBRARY_ROUTERS = [
    {"name": "Wing A", "capacity": 200, "location": "Center - Main Reading Hall"},
    {"name": "Wing B", "capacity": 180, "location": "North - Periodicals & Journals"},
    {"name": "Wing C", "capacity": 180, "location": "East - Computer Lab Section"},
    {"name": "Wing D", "capacity": 150, "location": "South - Group Discussion Zone"},
    {"name": "Wing E", "capacity": 120, "location": "West - Digital Archives"},
]


def load_balance(
    num_students: int = 500,
    routers_config: Optional[List[dict]] = None,
    initial_spike_router: int = 0
) -> dict:
    """
    Distributes incoming students across library wing routers using a Min-Heap.
    Total Time Complexity: O(S * log R)
    """
    config = routers_config if routers_config else LIBRARY_ROUTERS

    routers: List[Router] = []
    for r in config:
        routers.append(Router(r["name"], r["capacity"], r.get("location", "")))

    # Simulate initial traffic spike
    spike_amount = 0
    if 0 <= initial_spike_router < len(routers):
        spike_amount = int(routers[initial_spike_router].capacity * 0.7)
        routers[initial_spike_router].active_users = spike_amount

    # Build the Min-Heap
    heap: List[Router] = []
    for r in routers:
        heapq.heappush(heap, r)

    # Distribute students
    assignments_made = 0
    students_rejected = 0
    heap_operations = 0

    for student_id in range(1, num_students + 1):
        least_loaded = heapq.heappop(heap)
        heap_operations += 1

        if least_loaded.active_users < least_loaded.capacity:
            least_loaded.active_users += 1
            least_loaded.assignment_log.append(student_id)
            assignments_made += 1
        else:
            students_rejected += 1

        heapq.heappush(heap, least_loaded)
        heap_operations += 1

    total_capacity = sum(r.capacity for r in routers)
    total_users = sum(r.active_users for r in routers)

    return {
        "routers":              [r.to_dict() for r in routers],
        "total_students":       num_students,
        "assignments_made":     assignments_made,
        "students_rejected":    students_rejected,
        "total_capacity":       total_capacity,
        "total_active_users":   total_users,
        "overall_load_pct":     round(total_users / total_capacity * 100, 1) if total_capacity > 0 else 0,
        "spike_router":         config[initial_spike_router]["name"] if 0 <= initial_spike_router < len(config) else None,
        "spike_amount":         spike_amount,
        "heap_operations":      heap_operations,
        "algorithm":            "Min-Heap Priority Queue (heapq)",
        "time_complexity":      "O(S * log R) -- S students, R routers",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  API Request/Response Models (Pydantic)
# ═══════════════════════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    num_packets: int = 15
    weights: Optional[Dict[str, int]] = None

class PacketData(BaseModel):
    id: int
    packet_type: str
    size: int
    priority: int

class OptimizeRequest(BaseModel):
    packets: List[PacketData]
    bandwidth_limit: int = 300

class FifoRequest(BaseModel):
    packets: List[PacketData]
    bandwidth_limit: int = 300

class BalanceRequest(BaseModel):
    num_students: int = 500
    initial_spike_router: int = 0
    routers: Optional[List[dict]] = None

class UnbalancedRequest(BaseModel):
    num_students: int = 300

class RebalanceRequest(BaseModel):
    num_students: int = 300


# ═══════════════════════════════════════════════════════════════════════════════
#  API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

# ── Serve the frontend ────────────────────────────────────────────────────────
@app.get("/")
def root():
    """Serve the main NetQoS Optimizer HTML frontend."""
    return FileResponse("index.html")


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "server": "NetQoS Optimizer API v2.0",
        "algorithms": ["0/1 Knapsack DP", "Min-Heap Load Balancer"],
    }


# ── PROBLEM 2: Knapsack Packet Endpoints ─────────────────────────────────────

@app.post("/generate-packets")
def generate_packets(req: GenerateRequest):
    packets = packet_generator(req.num_packets, req.weights)
    return {"packets": [p.to_dict() for p in packets]}


@app.post("/optimize")
def optimize(req: OptimizeRequest):
    packets = [
        Packet(p.id, p.packet_type, p.size, p.priority)
        for p in req.packets
    ]
    return optimize_packets(packets, req.bandwidth_limit)


@app.post("/fifo-simulate")
def fifo_endpoint(req: FifoRequest):
    packets = [
        Packet(p.id, p.packet_type, p.size, p.priority)
        for p in req.packets
    ]
    return fifo_simulate(packets, req.bandwidth_limit)


# ── PROBLEM 1: Load Balancer Endpoints ────────────────────────────────────────

@app.post("/balance-network")
def balance_network(req: BalanceRequest):
    return load_balance(
        num_students=req.num_students,
        routers_config=req.routers,
        initial_spike_router=req.initial_spike_router,
    )


@app.post("/simulate-unbalanced")
def simulate_unbalanced(req: UnbalancedRequest):
    """All students rush to Wing A — demonstrates the PROBLEM."""
    config = LIBRARY_ROUTERS
    routers = [Router(r["name"], r["capacity"], r.get("location", "")) for r in config]

    wing_a = routers[0]
    assigned = min(req.num_students, wing_a.capacity)
    rejected = req.num_students - assigned
    wing_a.active_users = assigned

    total_capacity = sum(r.capacity for r in routers)
    total_users = sum(r.active_users for r in routers)

    return {
        "routers":           [r.to_dict() for r in routers],
        "total_students":    req.num_students,
        "assignments_made":  assigned,
        "students_rejected": rejected,
        "total_capacity":    total_capacity,
        "total_active_users": total_users,
        "overall_load_pct":  round(total_users / total_capacity * 100, 1) if total_capacity > 0 else 0,
        "status":            "OVERLOADED" if wing_a.active_users >= wing_a.capacity else "CONGESTED",
        "bottleneck":        wing_a.to_dict(),
    }


@app.post("/rebalance-heap")
def rebalance_heap(req: RebalanceRequest):
    """Apply Min-Heap to redistribute — demonstrates the SOLUTION."""
    return load_balance(
        num_students=req.num_students,
        routers_config=None,
        initial_spike_router=-1,
    )


@app.get("/network-topology")
def get_topology():
    return {"routers": LIBRARY_ROUTERS}


# ═══════════════════════════════════════════════════════════════════════════════
#  Run the Server
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))

    print()
    print("+------------------------------------------------------+")
    print("|        NetQoS Optimizer -- Backend Server v2.0        |")
    print("+------------------------------------------------------+")
    print(f"|  Running on: http://localhost:{port}                    |")
    print("|  API Docs:   http://localhost:{}/docs                 |".format(port))
    print("+------------------------------------------------------+")
    print()

    uvicorn.run(app, host="0.0.0.0", port=port)
