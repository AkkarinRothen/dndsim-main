from collections import defaultdict


class Log:
    def __init__(self, detailed=False):
        self.record_ = defaultdict(int)
        self.detailed = detailed
        self.enabled = False
        self._queue = None

    def set_queue(self, queue):
        self._queue = queue

    def record(self, type: str, val: int):
        if self.enabled:
            if self._queue:
                self._queue.put((type, val))
            else:
                self.record_[type] += val

    def printReport(self):
        keys = sorted(self.record_.keys())
        for key in keys:
            print(f"{key} - {self.record_[key]}")

    def print_specific_report(self, record_data: defaultdict):
        keys = sorted(record_data.keys())
        for key in keys:
            print(f"{key} - {record_data[key]}")

    def output(self, message):
        if self.enabled and self.detailed:
            print(message())

    def enable(self):
        self.enabled = True


log = Log(detailed=False)
