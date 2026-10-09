"""Read-only Linux scheduling evidence; never changes a runtime or system setting."""
import os
import time
from pathlib import Path


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def keyed_fields(raw):
    return {key.strip(): value.strip() for key, value in
            (line.split(":", 1) for line in raw.splitlines() if ":" in line)}


def tasks(pid):
    result = {}
    for path in Path(f"/proc/{pid}/task").glob("*"):
        try:
            raw = (path / "stat").read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            status = keyed_fields((path / "status").read_text())
            sched = keyed_fields((path / "sched").read_text())
            stats = [int(value) for value in (read(path / "schedstat") or "").split()]
            tid = int(path.name)
            result[tid] = {
                "name": status["Name"].strip(), "state": fields[0], "core": int(fields[36]),
                "cpu_ticks": int(fields[11]) + int(fields[12]),
                "runtime_ns": stats[0] if len(stats) == 3 else None,
                "runqueue_ns": stats[1] if len(stats) == 3 else None,
                "timeslices": stats[2] if len(stats) == 3 else None,
                "migrations": int(sched["se.nr_migrations"].strip()) if "se.nr_migrations" in sched else None,
                "voluntary": int(status.get("voluntary_ctxt_switches", "0")),
                "involuntary": int(status.get("nonvoluntary_ctxt_switches", "0")),
                "affinity": sorted(os.sched_getaffinity(tid)),
                "policy": os.sched_getscheduler(tid), "rt_priority": os.sched_getparam(tid).sched_priority,
                "nice": os.getpriority(os.PRIO_PROCESS, tid), "wchan": read(path / "wchan"),
            }
        except (OSError, ValueError, KeyError, IndexError):
            continue
    return result


def environment():
    base = Path("/sys/devices/system/cpu")
    freq = {path.parent.parent.name: read(path) for path in base.glob("cpu*/cpufreq/scaling_cur_freq")}
    thermal = {}
    for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
        thermal[zone.name] = {"type": read(zone / "type"), "temp": read(zone / "temp")}
    cooling = {path.name: read(path / "cur_state") for path in Path("/sys/class/thermal").glob("cooling_device*")}
    hwmon = {str(path): read(path) for path in Path("/sys/class/hwmon").glob("hwmon*/temp*_input")}
    return {"frequency_khz": freq, "thermal_zones": thermal, "cooling": cooling,
            "hwmon_temp": hwmon, "loadavg": read("/proc/loadavg")}


def topology():
    base = Path("/sys/devices/system/cpu")
    policies = {}
    names = ("affected_cpus", "related_cpus", "scaling_driver", "scaling_governor",
             "scaling_available_governors", "scaling_available_frequencies", "scaling_min_freq",
             "scaling_max_freq", "cpuinfo_min_freq", "cpuinfo_max_freq", "cpuinfo_cur_freq")
    for path in (base / "cpufreq").glob("policy*"):
        policies[path.name] = {name: read(path / name) for name in names}
    cores = {}
    for path in base.glob("cpu[0-9]*"):
        cores[path.name] = {"capacity": read(path / "cpu_capacity"),
                           "topology": {p.name: read(p) for p in (path / "topology").glob("*") if p.is_file()},
                           "caches": [{p.name: read(p) for p in cache.glob("*") if p.is_file()}
                                      for cache in (path / "cache").glob("index*")]}
    return {"cpuinfo": read("/proc/cpuinfo"), "online": read(base / "online"),
            "allowed": sorted(os.sched_getaffinity(0)), "policies": policies, "cores": cores,
            "environment": environment(), "clock_ticks": os.sysconf("SC_CLK_TCK")}


def delta(before, after):
    result = {}
    for tid, row in after.items():
        old = before.get(tid)
        if old is None:
            continue
        result[tid] = {key: None if row[key] is None or old[key] is None else row[key] - old[key]
                       for key in ("cpu_ticks", "runtime_ns", "runqueue_ns", "timeslices",
                                   "migrations", "voluntary", "involuntary")}
    return result


def system_load(seconds=2):
    def sample():
        processes = {}
        for path in Path("/proc").glob("[0-9]*"):
            raw = read(path / "stat")
            if not raw:
                continue
            try:
                fields = raw[raw.rfind(")") + 2:].split()
                processes[path.name] = {"name": raw[raw.find("(") + 1:raw.rfind(")")],
                                       "ticks": int(fields[11]) + int(fields[12]), "last_core": int(fields[36])}
            except (ValueError, IndexError):
                continue
        cpus = {line.split()[0]: list(map(int, line.split()[1:]))
                for line in (read("/proc/stat") or "").splitlines() if line.startswith("cpu")}
        return processes, cpus
    before, cpu_before = sample()
    watched = {pid: row["name"] for pid, row in before.items()
               if row["name"] in ("hyperion-webos", "hyperhdr", "pqcontroller", "WebAppMgr")}
    thread_samples = []
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        thread_samples.append({"monotonic": time.monotonic(),
                               "processes": {pid: tasks(pid) for pid in watched}})
        time.sleep(.2)
    after, cpu_after = sample()
    hot = [{"pid": pid, **row, "delta_ticks": row["ticks"] - before[pid]["ticks"]}
           for pid, row in after.items() if pid in before]
    hot.sort(key=lambda row: row["delta_ticks"], reverse=True)
    utilization = {}
    for core, values in cpu_after.items():
        values = [a - b for a, b in zip(values[:8], cpu_before[core][:8])]
        total = sum(values)
        utilization[core] = 100 * (total - values[3] - values[4]) / total if total else 0
    return {"seconds": seconds, "core_busy_percent": utilization, "top_processes": hot[:15],
            "watched_processes": watched, "thread_samples": thread_samples}
