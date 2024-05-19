import psutil
from flask import Flask, jsonify
import GPUtil
import threading
import time

app = Flask(__name__)


def get_user_job_breakdown():
    user_resource_usage = {}

    for proc in psutil.process_iter(
        ["username", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            username = proc.info["username"]
            cpu_usage = proc.info["cpu_percent"]
            memory_usage = proc.info["memory_percent"]

            if username not in user_resource_usage:
                user_resource_usage[username] = {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                }

            user_resource_usage[username]["cpu_usage"] += cpu_usage
            user_resource_usage[username]["memory_usage"] += memory_usage

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return user_resource_usage


last_time = 0
cached_usage_data = {}

@app.route("/system_usage", methods=["GET"])
def get_system_usage():
    return jsonify(cached_usage_data)

def compute_system_usage():
    # Get CPU usage
    cpu_usage = [p / 100 for p in psutil.cpu_percent(interval=1, percpu=True)]

    memory = psutil.virtual_memory()
    memory_usage = memory.percent / 100
    memory_used = memory.used
    memory_total = memory.total

    # Get GPU usage
    gpus = GPUtil.getGPUs()
    gpu_usage_list = []
    gpu_memory_used_list = []
    gpu_memory_total_list = []
    gpu_memory_usage_list = []
    gpu_temperature_list = []
    for gpu in gpus:
        gpu_usage_list.append(gpu.load)
        gpu_memory_used_list.append(gpu.memoryUsed)
        gpu_memory_total_list.append(gpu.memoryTotal)
        gpu_temperature_list.append(gpu.temperature)
        gpu_memory_usage_list.append(gpu.memoryUtil)

    # Prepare response data
    response_data = {
        "cpu_usage": cpu_usage,
        "cpu_usage_average": sum(cpu_usage) / len(cpu_usage),
        "cpu_memory_usage": memory_usage,
        "cpu_memory_used": memory_used,
        "cpu_memory_total": memory_total,
        "gpu_usage": gpu_usage_list,
        "gpu_usage_average": sum(gpu_usage_list) / len(gpu_usage_list),
        "gpu_memory_usage": gpu_memory_usage_list,
        "gpu_memory_usage_average": sum(gpu_memory_usage_list)
        / len(gpu_memory_usage_list),
        "gpu_memory_used": gpu_memory_used_list,
        "gpu_memory_total": gpu_memory_total_list,
        "gpu_temperature": gpu_temperature_list,
        "usage_breakdown": get_user_job_breakdown(),
    }

    return response_data


def start_collecting_resources():
    def _loop():
        global cached_usage_data
        while True:
            cached_usage_data = compute_system_usage()
            time.sleep(30)
    background_thread = threading.Thread(target=_loop)
    background_thread.start()


with app.app_context():
    start_collecting_resources()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
