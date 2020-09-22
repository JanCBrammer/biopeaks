from biopeaks.heart import ecg_peaks
from benchmark_utils import BenchmarkDetectorGUDB

condition = "hand_bike"    # can be one of {"sitting", "maths", "walking", "hand_bike", "jogging"}
tolerance = 1    # in samples

pipeline = BenchmarkDetectorGUDB(ecg_peaks, tolerance)
pipeline.benchmark_records(condition, channel="cs_V2_V1", annotation="annotation_cs")
