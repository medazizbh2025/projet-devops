import threading
import time
import logging
from .metrics_exporter import fetch_sonarqube_metrics

logger = logging.getLogger(__name__)

class MetricsScheduler:
    def __init__(self, interval=300):  # Default 5 minutes
        self.interval = interval
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        """Start the metrics collection thread"""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Metrics scheduler is already running")
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Started metrics scheduler")

    def stop(self):
        """Stop the metrics collection thread"""
        if self.thread is None or not self.thread.is_alive():
            logger.warning("Metrics scheduler is not running")
            return

        self.stop_event.set()
        self.thread.join()
        self.thread = None
        logger.info("Stopped metrics scheduler")

    def _run(self):
        """Main metrics collection loop"""
        while not self.stop_event.is_set():
            try:
                fetch_sonarqube_metrics()
            except Exception as e:
                logger.error(f"Error in metrics collection: {str(e)}")
            
            # Sleep until next collection or stop event
            self.stop_event.wait(self.interval)