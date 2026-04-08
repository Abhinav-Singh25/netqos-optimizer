# NetQoS Optimizer

> Dual-stage network optimization for campus Wi-Fi using **0/1 Knapsack DP** and **Min-Heap Load Balancing**.

**Live Demo:** [https://netqos-optimizer.onrender.com](https://netqos-optimizer.onrender.com) *(update after deploy)*

---

## Problem Statement

VIT Vellore's campus Wi-Fi suffers from two critical issues during peak hours:

1. **Macro Level** — All students connect to the nearest router (Wing A), overloading it while surrounding routers sit idle.
2. **Micro Level** — Large streaming/download packets consume all bandwidth, causing critical academic portals (VTOP, Zoom) to timeout.

## Solution

### Algorithm 1: Min-Heap Load Balancer (Macro Level)

Distributes students across 5 library wing routers using a **Min-Heap Priority Queue**.

- **Data Structure:** `heapq` (Python) — Min-Heap sorted by `active_users`
- **Operation:** `heappop()` least-loaded router → assign student → `heappush()` back
- **Time Complexity:** `O(S × log R)` — S students, R routers
- **Space Complexity:** `O(R)`

### Algorithm 2: 0/1 Knapsack DP (Micro Level)

Selects the optimal subset of network packets that maximizes total priority within a bandwidth limit.

- **Formulation:** Items = packets, Weight = byte size, Value = priority score, Capacity = bandwidth
- **DP Table:** `dp[n+1][W+1]` where `dp[i][w]` = max priority using first `i` packets with capacity `w`
- **Time Complexity:** `O(n × W)` — n packets, W bandwidth limit
- **Space Complexity:** `O(n × W)`

## Interactive Demo Features

| Feature | What It Shows |
|---------|---------------|
| **Library Topology** | Step 1: All students flood Wing A (problem) → Step 2: Min-Heap redistributes evenly (solution) |
| **Simulation Panel** | Toggle Normal Router (FIFO) vs Smart QoS (Knapsack) to see which packets get selected/dropped |
| **Dashboard** | Real-time KPIs from last simulation |
| **Analytics** | Packet-level table with priority scores and status |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, Pydantic |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS |
| **Algorithms** | `heapq` (Min-Heap), Custom DP (Knapsack) |
| **Deployment** | Render.com (Free Tier) |

## Run Locally

```bash
# Clone the repo
git clone https://github.com/Abhinav-Singh25/netqos-optimizer.git
cd netqos-optimizer

# Install dependencies
pip install -r requirements.txt

# Start the server
python server.py

# Open in browser
# http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve frontend |
| `GET` | `/health` | Server status |
| `POST` | `/generate-packets` | Generate traffic packets |
| `POST` | `/optimize` | Run 0/1 Knapsack DP |
| `POST` | `/fifo-simulate` | Simulate FIFO router |
| `POST` | `/simulate-unbalanced` | Show overload problem |
| `POST` | `/rebalance-heap` | Apply Min-Heap solution |
| `POST` | `/balance-network` | Full load balancer |
| `GET` | `/network-topology` | Router map |
| `GET` | `/docs` | Swagger API docs |

## Project Structure

```
netqos-optimizer/
├── index.html          # Frontend (single-page app)
├── server.py           # FastAPI backend + algorithms
├── requirements.txt    # Python dependencies
├── render.yaml         # Render.com deploy config
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Team

- **Abhinav Kumar Singh** (25BCE2258)
- Course: Data Structures & Algorithms
- Institution: VIT Vellore

## License

MIT License
