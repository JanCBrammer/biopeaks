from biopeaks.heart import ecg_peaks
from benchmark_utils import BenchmarkDetectorGUDB


pipeline = BenchmarkDetectorGUDB(ecg_peaks, 1)
pipeline.benchmark_records("jogging", channel="cs_V2_V1", annotation="annotation_cs")
