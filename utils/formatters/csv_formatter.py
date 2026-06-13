"""
CSV report formatter for material lists
"""

import os
from utils.formatters.base_formatter import BaseReportFormatter
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult


class CSVReportFormatter(BaseReportFormatter):
    """CSV report formatter for material lists"""

    @property
    def file_extension(self) -> str:
        return '.csv'

    @property
    def file_filter(self) -> str:
        return "CSV Files (*.csv)"

    @property
    def format_name(self) -> str:
        return "CSV Material List"

    def generate(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        config = self._ensure_config(config)
        warnings = self.validate_data(data)

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w') as f:
                self._write_csv_content(f, data)

            self.logger.info(f"CSV report generated: {file_path}")
            return self._create_success_result(file_path, warnings)

        except Exception as e:
            error_msg = f"Error generating CSV report: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(error_msg, warnings)

    def _write_csv_content(self, f, data: ReportData):
        """Write CSV material list"""
        f.write("Item Type,Item Description,Quantity,Zone Assignment\n")

        summary = self._get_material_summary(data.zones_data)

        # Write controllers
        for controller, qty in summary['controllers'].items():
            f.write(f"Controller,{controller},{qty},Various\n")

        # Write materials
        for material, qty in summary['materials'].items():
            f.write(f"Material,{material},{qty},Various\n")

    def validate_data(self, data: ReportData) -> list:
        """Validate data specific to CSV material lists"""
        warnings = super().validate_data(data)

        summary = self._get_material_summary(data.zones_data)

        if not summary['materials'] and not summary['controllers']:
            warnings.append("No materials or controllers found in any zones")

        return warnings