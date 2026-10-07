from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


class Metrics:
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.releases = Counter("deploywarden_release_total", "Release attempts", ["action", "outcome"], registry=self.registry)
        self.duration = Histogram("deploywarden_operation_seconds", "Release operation duration", ["action"], registry=self.registry)
        self.current_version = Gauge("deploywarden_current_release_info", "Current release", ["version"], registry=self.registry)
        self.in_progress = Gauge("deploywarden_operation_in_progress", "Operation in progress", registry=self.registry)
        self.checkpoints = Gauge("deploywarden_checkpoints", "Available rollback checkpoints", registry=self.registry)

    def render(self) -> bytes:
        return generate_latest(self.registry)
