import time

class Timer:
    def __init__(self, message=""):
        self.message = message

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.interval = self.end - self.start
        print(f"{self.message} 耗时 {self.interval*1000:.3f} ms")