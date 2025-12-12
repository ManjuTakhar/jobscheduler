"""Main entry point for the job scheduler service."""
import argparse
import signal
import sys
import logging
from pathlib import Path

from .scheduler import JobScheduler
from .file_watcher import JobFileWatcher


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the scheduler."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Job Scheduler - A lightweight, in-memory job scheduling service'
    )
    parser.add_argument(
        '--jobs-dir',
        type=str,
        default='/etc/chronoflow/jobs.d',
        help='Directory containing job definition files (default: /etc/chronoflow/jobs.d)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='logs',
        help='Directory for job-specific log files (default: logs)'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create scheduler and file watcher
    scheduler = JobScheduler(log_directory=args.log_dir)
    file_watcher = JobFileWatcher(args.jobs_dir, scheduler)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received, stopping scheduler...")
        file_watcher.stop()
        scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the services
    try:
        scheduler.start()
        file_watcher.start()
        
        logger.info("Job Scheduler is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            import time
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        file_watcher.stop()
        scheduler.stop()
        logger.info("Job Scheduler stopped")


if __name__ == '__main__':
    main()

