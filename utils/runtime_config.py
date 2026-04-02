import os
import platform
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class RuntimeTuning:
    cpu_logical: int
    mem_available_gb: Optional[float]
    tf_intra_threads: int
    tf_inter_threads: int
    parallel_predict: bool
    max_workers: int


def _get_cpu_logical() -> int:
    return max(1, int(os.cpu_count() or 1))


def _mem_available_gb_fallback() -> Optional[float]:
    try:
        import psutil  # type: ignore

        return float(psutil.virtual_memory().available) / (1024 ** 3)
    except Exception:
        pass

    try:
        if os.name == "posix" and os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        parts = line.split()
                        kb = int(parts[1])
                        return kb / (1024 ** 2)
    except Exception:
        pass

    try:
        if os.name == "nt":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return float(stat.ullAvailPhys) / (1024 ** 3)
    except Exception:
        pass

    return None


def get_runtime_tuning() -> RuntimeTuning:
    cpu = _get_cpu_logical()
    mem_gb = _mem_available_gb_fallback()

    reserve = 1 if cpu >= 4 else 0
    base_intra = max(1, cpu - reserve)
    base_inter = 1 if cpu < 16 else 2

    parallel_predict = cpu >= 8 and (mem_gb is None or mem_gb >= 2.0)
    if parallel_predict:
        tf_intra = max(1, base_intra // 2)
        tf_inter = 1
        max_workers = min(8, max(2, cpu // 2))
    else:
        tf_intra = base_intra
        tf_inter = base_inter
        max_workers = min(8, max(1, cpu - reserve))

    if mem_gb is not None and mem_gb < 1.5:
        tf_intra = 1
        tf_inter = 1
        parallel_predict = False
        max_workers = 1

    return RuntimeTuning(
        cpu_logical=cpu,
        mem_available_gb=mem_gb,
        tf_intra_threads=int(tf_intra),
        tf_inter_threads=int(tf_inter),
        parallel_predict=bool(parallel_predict),
        max_workers=int(max_workers),
    )


def apply_runtime_env() -> RuntimeTuning:
    tuning = get_runtime_tuning()

    defaults = {
        "TF_NUM_INTRAOP_THREADS": str(tuning.tf_intra_threads),
        "TF_NUM_INTEROP_THREADS": str(tuning.tf_inter_threads),
        "OMP_NUM_THREADS": str(tuning.tf_intra_threads),
        "MKL_NUM_THREADS": str(tuning.tf_intra_threads),
        "OPENBLAS_NUM_THREADS": str(tuning.tf_intra_threads),
        "NUMEXPR_NUM_THREADS": str(tuning.tf_intra_threads),
    }

    for k, v in defaults.items():
        os.environ.setdefault(k, v)

    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "1")
    return tuning

