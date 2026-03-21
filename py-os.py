import time
from collections import deque
import threading

print_cpu = False

class Process:
    """Essentially contains the details of the process"""
    def __init__(self, pid, name, burst_time):
        self.pid = pid
        self.name = name
        self.burst_time = burst_time #total time needed for the process
        self.state = "READY"

    def __repr__(self):
        return f"[PIS {self.pid}: {self.name} ({self.burst_time}s left)]"
    
class VirtualMemory:
    def __init__(self, size = 32):
        #32 slots in RAT, None = Free, PID = Occupied
        self.slots = [None] * size

    def allocate(self, pid):
        #finds the first free slot and assigns it to a PID
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = pid
                return i
        return -1 #out of memory
    
    def deallocate(self, pid):
        #deallocates processes when they're done, frees up RAM
        for i in range(len(self.slots)):
            if self.slots[i] == pid:
                self.slots[i] = None
        
class VFS:
    def __init__(self):
        #simulated hard drive
        self.storage = {
            "root": {
                "bin" : {"echo": "SYSTEM_BINARY"},
                "home" : {
                    "user" : {"notes.txt": "Study OS today", "todo.txt": "Explore Simulator\nFind Dorothy"}
                },
                "tmp": {}
            }
        }
        self.current_path = ["root"]

    def ls(self):
        # lists files and folders in the current directory
        node = self.storage
        for folder in self.current_path:
            node = node[folder]
        return list(node.keys())
    
    def cat(self, filename):
        #"reads" a "file" - it's a simpler one that looks in root/home/user
        try:
            return self.storage["root"]["home"]["user"][filename]
        except KeyError:
            return "Error: File not found."

class Kernel:
    def __init__(self, quantum = 2):
        self.ready_queue = deque()
        self.mem = VirtualMemory()
        self.fs = VFS()        
        self.quantum = quantum 
        self.pid_counter = 1

    def spawn(self, name, burst_time):
        # Try to get RAM first!
        addr = self.mem.allocate(self.pid_counter)
        if addr != -1:
            new_proc = Process(self.pid_counter, name, burst_time)
            self.ready_queue.append(new_proc)
            print(f"Kernel: Loaded {name} into RAM at address {addr}")
            self.pid_counter += 1
        else:
            print("Kernel Error: Out of Memory (OOM)!")

    def scheduler_tick(self):
        global print_cpu
        """We're using one 'tick' of the CPU to decide which process runs next"""
        if not self.ready_queue:
            return False
        
        #Pop the first process in the queue
        current = self.ready_queue.popleft()
        current.state = "RUNNING"
        if print_cpu:
            print(f"\nCPU: Now running {current.name}...")

        #Run for the quantum (or until the process finishes if that time is less than the quantum)
        run_time = min(self.quantum, current.burst_time)
        time.sleep(0.5) #this is just to see the simulation in action
        current.burst_time -= run_time

        if current.burst_time > 0:
            current.state = "READY"
            self.ready_queue.append(current) #return to end of queue since it still needs to finish
            if print_cpu:
                print(F"Context Switch: {current.name} paused. {current.burst_time}s remaining.")
        else:
            self.mem.deallocate(current.pid)
            if print_cpu:
                print(f"Kernel: {current.name} finished. RAM Slot freed.")

        return True
    
    def process_list(self):
        if not self.ready_queue:
            return "No active processes."
        
        header = f"{'PID':<5} | {'NAME':<15} | {'REMAINING':<10} | {'STATE'}"
        rows = [header, "-" * 45]

        for p in self.ready_queue:
            rows.append(f"{p.pid:<5} | {p.name:<15} | {p.burst_time:<10} | {p.state}")

        return "\n".join(rows)

    def run_shell(self):
        global print_cpu
        print("\n--- Welcome to The OS Sim - in Python v0.1 ---")
        print("Commands: ls, cat <file>, run <name> <time>, ps, mem, kill <pid>, pco, exit")

        while True:
            try:
                user_input = input("pyOS> ").strip().split()
                if not user_input: continue

                match user_input:
                    case ["exit"]:
                        print("Shutting down...")
                        break
                    case ["ls"]:
                        print(f"Files: {self.fs.ls()}")
                    case ["cat", filename]:
                        print(self.fs.cat(filename))
                    case ["ps"]:
                        print(self.process_list())
                    case ["mem"]:
                        print(f"RAM: [{' | '.join(str(s) if s else '-' for s in self.mem.slots)}]")
                    case ["run", name, burst]:
                        self.spawn(name, int(burst)) #add a process
                    case ["kill", pid]:
                        initial_len = len(self.ready_queue)
                        self.ready_queue = deque([p for p in self.ready_queue if p.pid != int(pid)])
                        if len(self.ready_queue) < initial_len:
                            self.mem.deallocate(int(pid))
                            print(f"Kernel: PID {pid} terminated and memory freed.")
                        else:
                            print(f"Error: PID {pid} not found.")
                    case ["pco"]:
                        print("<<< Kernel Output Enabled for 5 seconds >>>")
                        print_cpu = True
                        time.sleep(5) # Let the user see 5 seconds of logs
                        print_cpu = False
                        print("\n<<< Kernel Output Silenced >>>")
                    case ["help"]:
                        print("Available: ls, cat <f>, ps, mem, run <n> <t>, kill <p>, pco, exit")
                    case _:
                        print(f"Unknown command or wrong arguments: {' '.join(user_input)}")
            except KeyboardInterrupt:
                print_cpu = False # Safety: Silence if user hits Ctrl+C
                print("\nOutput silenced.")

def background_cpu(kernel):
    while True:
        if kernel.scheduler_tick():
            time.sleep(1) # Wait between cycles
        else:
            time.sleep(2) # Idle if no processes
    
if __name__ == "__main__":
    my_os = Kernel()
    cpu_thread = threading.Thread(target=background_cpu, args=(my_os,), daemon=True)
    cpu_thread.start()
    my_os.run_shell()
