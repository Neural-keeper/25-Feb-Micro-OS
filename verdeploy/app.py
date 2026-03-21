import streamlit as st
import time
from collections import deque

# --- OS Logic with Nested FS ---
class Kernel:
    def __init__(self):
        self.ready_queue = deque()
        self.slots = [None] * 32
        self.pid_counter = 1
        self.logs = ["💻 System Booted..."]
        # Nested Folder Structure
        self.fs = {
            "bin": {"echo": "SYSTEM_BINARY"},
            "home": {
                "user": {
                    "notes.txt": "Study OS today",
                    "projects": {"sim.py": "print('hello')"}
                }
            },
            "tmp": {}
        }

    # Helper to traverse the nested dict based on a path list
    def get_dir(self, path):
        node = self.fs
        for folder in path:
            node = node[folder]
        return node

    def spawn(self, name, burst_time):
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = self.pid_counter
                self.ready_queue.append({'pid': self.pid_counter, 'name': name, 'burst': burst_time})
                self.logs.append(f"🟢 Loaded {name} (PID {self.pid_counter})")
                self.pid_counter += 1
                return True
        return False

# --- Streamlit UI ---
st.set_page_config(page_title="pyOS Dashboard", layout="wide")

if "kernel" not in st.session_state:
    st.session_state.kernel = Kernel()
    st.session_state.current_path = [] # Root is empty list []

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
    st.subheader("Virtual File Explorer")
    
    # 1. Breadcrumb Navigation
    path_display = "root / " + " / ".join(st.session_state.current_path)
    st.write(f"📂 **Current Path:** `{path_display}`")
    
    if st.button("⬅️ Up One Level") and st.session_state.current_path:
        st.session_state.current_path.pop()
        st.rerun()

    # 2. Folder Actions
    c1, c2, c3 = st.columns(3)
    new_item = c1.text_input("New Item Name", placeholder="e.g. docs")
    if c2.button("📁 New Folder"):
        k.get_dir(st.session_state.current_path)[new_item] = {}
        st.rerun()
    if c3.button("📄 New File"):
        k.get_dir(st.session_state.current_path)[new_item] = "New empty file."
        st.rerun()

    st.divider()

    # 3. List Current Directory
    current_node = k.get_dir(st.session_state.current_path)
    
    for name, content in current_node.items():
        is_folder = isinstance(content, dict)
        icon = "📁" if is_folder else "📄"
        
        col_name, col_act = st.columns([3, 1])
        col_name.write(f"{icon} **{name}**")
        
        if is_folder:
            if col_act.button("Open", key=f"open_{name}"):
                st.session_state.current_path.append(name)
                st.rerun()
        else:
            if col_act.button("Read", key=f"read_{name}"):
                st.session_state.file_preview = (name, content)
        
        # Delete Button
        if col_act.button("🗑️", key=f"del_{name}"):
            del current_node[name]
            st.rerun()

    # 4. File Preview
    if "file_preview" in st.session_state:
        st.divider()
        fname, fcont = st.session_state.file_preview
        st.info(f"**Viewing:** {fname}")
        st.text_area("Content", value=fcont, height=100)

# (Add your CPU Tick logic here as before)


# Scheduler Tick
if auto_run and k.ready_queue:
    time.sleep(0.7)
    k.tick()
    st.rerun()

