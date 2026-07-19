"""
Audit logging module for the FinMark data pipeline.
Logs all pipeline runs to a CSV file for tracking and compliance.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class AuditLogger:
    """Handles writing pipeline execution events to an audit log CSV."""

    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the audit logger.
        
        Args:
            log_path: Path to the audit log CSV. Defaults to data/audit_log.csv
        """
        if log_path is None:
            base_dir = Path(__file__).resolve().parents[1]
            log_path = base_dir / "data" / "audit_log.csv"
        
        self.log_path = Path(log_path)
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """Create the audit log file and headers if it doesn't exist."""
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Pipeline_Stage',
                    'Status',
                    'Duration_Seconds',
                    'Error_Message',
                    'Notes'
                ])

    def log_event(
        self,
        stage: str,
        status: str,
        duration: float = 0.0,
        error_message: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Log a pipeline execution event.
        
        Args:
            stage: Name of the pipeline stage (e.g., 'BRONZE', 'SILVER', 'GOLD')
            status: Status of the stage ('SUCCESS' or 'FAILURE')
            duration: How long the stage took to run in seconds
            error_message: Error message if status is FAILURE
            notes: Additional notes about the run
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                stage,
                status,
                round(duration, 2),
                error_message or '',
                notes or ''
            ])

    def log_pipeline_start(self):
        """Log the start of a full pipeline run."""
        self.log_event(
            stage='PIPELINE_START',
            status='SUCCESS',
            duration=0.0,
            notes='Full pipeline execution initiated'
        )

    def log_pipeline_end(self):
        """Log the successful completion of a full pipeline run."""
        self.log_event(
            stage='PIPELINE_END',
            status='SUCCESS',
            duration=0.0,
            notes='Full pipeline execution completed'
        )

    def log_pipeline_failure(self, error_message: str):
        """Log a pipeline failure."""
        self.log_event(
            stage='PIPELINE_END',
            status='FAILURE',
            duration=0.0,
            error_message=error_message,
            notes='Pipeline execution failed'
        )
