"""
Data models and containers for report generation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class ReportData:
    """Data container for report generation"""
    project_data: Dict[str, Any]
    zones_data: Dict[str, Any]
    speaker_layout: Optional[Dict[str, Any]] = None
    obstruction_layout: Optional[Dict[str, Any]] = None


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    include_thumbnails: bool = True
    include_snapshots: bool = True
    include_measurements: bool = True   # spacing analysis section per zone
    high_resolution: bool = True
    page_margins: int = 20
    dpi: int = 1200


@dataclass
class ReportGenerationResult:
    """Result of report generation operation"""
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class BatchReportResult:
    """Result of batch report generation"""
    total_requested: int
    successful: int
    failed: int
    results: Dict[str, ReportGenerationResult]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_requested == 0:
            return 0.0
        return (self.successful / self.total_requested) * 100.0

    @property
    def is_complete_success(self) -> bool:
        """Check if all reports were generated successfully"""
        return self.successful == self.total_requested

    @property
    def is_partial_success(self) -> bool:
        """Check if some but not all reports were successful"""
        return 0 < self.successful < self.total_requested