from biopeaks.heart import ecg_peaks
from benchmark_utils import BenchmarkDetectorGUDB

condition = "sitting"    # can be one of {"sitting", "maths", "walking", "hand_bike", "jogging"}
tolerance = 1    # in samples

pipeline = BenchmarkDetectorGUDB(ecg_peaks, tolerance)
pipeline.benchmark_records(condition, channel="einthoven_II", annotation="annotation_cables")
