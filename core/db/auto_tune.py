import os
import platform
import psutil
import time
import yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # 进度条库

PROJECT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / 'configs' / 'config.yaml'

class AutoTuner:
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=False)  # 物理核心数
        self.total_memory = psutil.virtual_memory().total
        self.system = platform.system()
        self.config = {}

    def run_load_test(self):
        """
        运行负载测试，测量系统在高负载下的性能
        """
        load_test_results = {
            'cpu_usage': [],
            'memory_usage': [],
            'response_times': [],
            'io_usage': [],
            'network_usage': []
        }

        def simulate_load():
            start_time = time.time()
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            io_counters = psutil.disk_io_counters()
            network_counters = psutil.net_io_counters()
            duration = time.time() - start_time
            return cpu_usage, memory_usage, io_counters, network_counters, duration

        with ThreadPoolExecutor(max_workers=self.cpu_count) as executor:
            futures = [executor.submit(simulate_load) for _ in range(min(50, self.cpu_count * 10))]  # 动态调整并发任务数量
            for future in tqdm(futures, desc="Running load test", ncols=100):  # 添加进度条显示
                cpu_usage, memory_usage, io_counters, network_counters, duration = future.result()
                load_test_results['cpu_usage'].append(cpu_usage)
                load_test_results['memory_usage'].append(memory_usage)
                load_test_results['io_usage'].append(io_counters.read_bytes + io_counters.write_bytes)
                load_test_results['network_usage'].append(network_counters.bytes_sent + network_counters.bytes_recv)
                load_test_results['response_times'].append(duration)

        # 计算平均值
        load_test_results['avg_cpu_usage'] = sum(load_test_results['cpu_usage']) / len(load_test_results['cpu_usage'])
        load_test_results['avg_memory_usage'] = sum(load_test_results['memory_usage']) / len(load_test_results['memory_usage'])
        load_test_results['avg_io_usage'] = sum(load_test_results['io_usage']) / len(load_test_results['io_usage'])
        load_test_results['avg_network_usage'] = sum(load_test_results['network_usage']) / len(load_test_results['network_usage'])
        load_test_results['avg_response_time'] = sum(load_test_results['response_times']) / len(load_test_results['response_times'])
        return load_test_results

    def determine_optimal_parameters(self, load_test_results):
        """
        根据负载测试结果和系统资源，自动调整参数，兼顾高配和低配系统
        """
        # 动态调整基准值，分别针对高配和低配系统
        if self.total_memory <= 8 * 1024 ** 3:  # 小于等于8GB内存
            memory_ratio = self.total_memory / (8 * 1024 ** 3)  # 基准为8GB
            cpu_ratio = self.cpu_count / 4  # 基准为4核
            base_context_tokens = 1024
            base_query_terms = 10
        else:
            memory_ratio = self.total_memory / (16 * 1024 ** 3)  # 基准为16GB
            cpu_ratio = self.cpu_count / 8  # 基准为8核
            base_context_tokens = 2048
            base_query_terms = 18

        # 采用非线性映射调整参数
        def adjust_based_on_ratio(base_value, ratio, load_threshold, response_time_threshold):
            if load_test_results['avg_memory_usage'] < load_threshold and load_test_results['avg_response_time'] < response_time_threshold:
                return int(base_value * ratio * 1.5)
            elif load_test_results['avg_memory_usage'] < 80 and load_test_results['avg_response_time'] < 2:
                return int(base_value * ratio)
            else:
                return int(base_value * ratio * 0.75)

        # 动态调整 max_context_tokens 基于内存、响应时间和 I/O 性能
        self.config['max_context_tokens'] = adjust_based_on_ratio(base_context_tokens, memory_ratio, 60, 1)

        # 动态调整 Elasticsearch 查询参数基于 CPU 使用率和响应时间
        self.config['elasticsearch_query_terms'] = adjust_based_on_ratio(base_query_terms, cpu_ratio, 50, 1)

        # 为低配系统设置最低值限制
        if self.total_memory <= 4 * 1024 ** 3:  # 4GB以下内存
            self.config['max_context_tokens'] = max(self.config['max_context_tokens'], 512)
            self.config['elasticsearch_query_terms'] = max(self.config['elasticsearch_query_terms'], 4)

    def update_config_file(self):
        """
        将调整后的参数保存到 config.yaml 文件
        """
        try:
            if PROJECT_CONFIG_PATH.exists():
                with open(PROJECT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    project_config_lines = f.readlines()
            else:
                project_config_lines = []

            # 移除旧的配置
            new_config_lines = []
            inside_custom_block = False
            for line in project_config_lines:
                if line.strip() == '# ---------- Auto-tuned Configuration ----------':
                    inside_custom_block = True
                    continue
                if line.strip() == '# ---------- End Auto-tuned Configuration ------':
                    inside_custom_block = False
                    continue
                if not inside_custom_block:
                    new_config_lines.append(line)

            # 将新的配置添加到文件末尾
            new_config_lines.append('\n')
            new_config_lines.append('# ---------- Auto-tuned Configuration ----------\n')
            for key, value in self.config.items():
                new_config_lines.append(f'{key}: {value}\n')
            new_config_lines.append('# ---------- End Auto-tuned Configuration ------\n')

            # 保存更新后的内容到 config.yaml 文件
            with open(PROJECT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.writelines(new_config_lines)

            print(f"> 自动调整的配置已保存至：{PROJECT_CONFIG_PATH}")
            print(f"> -------------------------------------------------")
            print(f"> 请不要擅自修改已添加的配置内容及注释，否则可能导致配置系统无法正常工作。")
            print(f"> PLEASE DO NOT MODIFY THE ADDED CONFIGURATION CONTENTS AND COMMENTS,")
            print(f"> OR ELSE THE CONFIGURATION SYSTEM MAY NOT WORK PROPERLY.")
            print(f"> -------------------------------------------------")

        except Exception as e:
            print(f"! 保存自动调整的配置时出错：{e}")
            raise

    def tune(self):
        """
        执行自动调优过程
        """
        load_test_results = self.run_load_test()
        self.determine_optimal_parameters(load_test_results)
        self.update_config_file()


if __name__ == "__main__":
    tuner = AutoTuner()
    tuner.tune()
