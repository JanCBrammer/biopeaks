from biopeaks.heart import ecg_peaks
from benchmark_utils import BenchmarkDetectorGUDB


urls = [f"https://berndporr.github.io/ECG-GUDB/experiment_data/subject_{str(i).zfill(2)}/jogging/" for i in range(25)]

pipeline = BenchmarkDetectorGUDB(ecg_peaks, 1)
pipeline.benchmark_records(urls)
