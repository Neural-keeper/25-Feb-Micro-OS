import streamlit as st
import time
from collections import deque

# --- OS Logic ---
class Process:
    def __init__(self, pid, name, burst_time):
        self.pid, self.name, self.burst_time = pid, name, burst_time
        self.state = "READY"

class Kernel:
    def __init__(self):
        self.ready_queue = deque()
        self.slots = [None] * 32
        self.pid_counter = 1
        self.logs = ["💻 System Booted..."]
        self.fs = {"root": {
                        "bin" : {"echo": "SYSTEM_BINARY"},
                        "home" : {
                            "user" : {"notes.txt": "Study OS today", "todo.txt": "Explore Simulator\nFind Dorothy"}
                        },
                        "tmp": {}
                    }}

    def spawn(self, name, burst_time):
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = self.pid_counter
                self.ready_queue.append(Process(self.pid_counter, name, burst_time))
                self.logs.append(f"🟢 Loaded {name} (PID {self.pid_counter})")
                self.pid_counter += 1
                return True
        return False

    def kill_process(self, pid):
        # Remove from queue
        self.ready_queue = deque([p for p in self.ready_queue if p.pid != pid])
        # Free RAM
        self.slots = [None if x == pid else x for x in self.slots]
        self.logs.append(f"🛑 Terminated PID {pid}")

    def tick(self):
        if not self.ready_queue: return
        curr = self.ready_queue.popleft()
        curr.state = "RUNNING"
        time.sleep(0.1) # Micro-delay for realism
        curr.burst_time -= 1
        if curr.burst_time > 0:
            curr.state = "READY"
            self.ready_queue.append(curr)
        else:
            self.slots = [None if x == curr.pid else x for x in self.slots]
            self.logs.append(f"🏁 {curr.name} (PID {curr.pid}) Finished.")

# --- UI Setup ---
st.set_page_config(page_title="pyOS Dashboard", layout="wide")

if "kernel" not in st.session_state:
    st.session_state.kernel = Kernel()
k = st.session_state.kernel

st.title("🖥️ pyOS Interactive Environment")

# Sidebar
with st.sidebar:
    st.header("🛠️ Process Manager")
    with st.form("spawn_form", clear_on_submit=True):
        name = st.text_input("Name", "Task")
        burst = st.slider("Burst (s)", 1, 20, 5)
        if st.form_submit_button("🚀 Spawn"): k.spawn(name, burst)
    
    auto_run = st.toggle("🔌 Enable CPU Scheduler", value=False)
    if st.button("🗑️ Clear Logs"): k.logs = ["Logs cleared."]

tab1, tab2 = st.tabs(["📊 CPU & RAM", "📂 File System"])

with tab1:
    col_proc, col_log = st.columns([2, 1])
    
    with col_proc:
        st.subheader("Active Processes")
        if not k.ready_queue:
            st.info("No processes running.")
        else:
            # Table Header
            h1, h2, h3, h4 = st.columns([1, 2, 2, 1])
            h1.write("**PID**")
            h2.write("**Name**")
            h3.write("**Remaining**")
            h4.write("**Action**")
            
            # Interactive Rows
            for p in list(k.ready_queue):
                r1, r2, r3, r4 = st.columns([1, 2, 2, 1])
                r1.write(f"`{p.pid}`")
                r2.write(p.name)
                r3.progress(max(0, min(p.burst_time/20, 1.0)), text=f"{p.burst_time}s")
                if r4.button("Kill", key=f"kill_{p.pid}"):
                    k.kill_process(p.pid)
                    st.rerun()

        st.subheader("Memory Map (RAM)")
        cols = st.columns(8)
        for i, slot in enumerate(k.slots):
            with cols[i % 8]:
                val = f"P{slot}" if slot else ".."
                st.code(f"{i:02d}: {val}", language="text")

    with col_log:
        st.subheader("Console")
        st.text_area("Logs", value="\n".join(reversed(k.logs)), height=400, disabled=True)

with tab2:
    st.subheader("Virtual File System")
    for filename, content in k.fs.items():
        if st.button(f"📄 {filename}"):
            st.session_state.file_content = content
    
    if "file_content" in st.session_state:
        st.info(f"**Content:** {st.session_state.file_content}")

# Scheduler Tick
if auto_run and k.ready_queue:
    time.sleep(0.7)
    k.tick()
    st.rerun()

