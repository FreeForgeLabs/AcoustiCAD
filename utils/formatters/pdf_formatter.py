"""
PDF report formatter
"""

import os
from utils.formatters.base_formatter import BaseReportFormatter
from utils.formatters.html_formatter import HTMLReportFormatter
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult


class PDFReportFormatter(BaseReportFormatter):
    """PDF report formatter"""

    def __init__(self, logger=None, html_formatter: HTMLReportFormatter = None):
        super().__init__(logger)
        self.html_formatter = html_formatter or HTMLReportFormatter(logger)

    @property
    def file_extension(self) -> str:
        return '.pdf'

    @property
    def file_filter(self) -> str:
        return "PDF Files (*.pdf)"

    @property
    def format_name(self) -> str:
        return "PDF Report"

    def generate(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        config = self._ensure_config(config)
        warnings = self.validate_data(data)

        try:
            # Generate temporary HTML
            html_path = file_path + ".temp.html"
            html_result = self.html_formatter.generate(data, html_path, config)

            if not html_result.success:
                return self._create_error_result(
                    f"Failed to generate HTML for PDF conversion: {html_result.error_message}",
                    warnings
                )

            # Convert to PDF
            pdf_success = self._convert_html_to_pdf(html_path, file_path, config)

            # Clean up
            try:
                os.remove(html_path)
            except:
                pass

            if pdf_success:
                self.logger.info(f"PDF report generated: {file_path}")
                return self._create_success_result(file_path, warnings)
            else:
                return self._create_error_result("Failed to convert HTML to PDF", warnings)

        except Exception as e:
            error_msg = f"Error generating PDF report: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(error_msg, warnings)

    def _convert_html_to_pdf(self, html_path: str, pdf_path: str, config: ReportConfig) -> bool:
        """Convert HTML to PDF using Qt WebEngine"""
        try:
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtCore import QUrl, QEventLoop, QTimer
            from PySide6.QtWidgets import QApplication
            import sys

            app = QApplication.instance() or QApplication(sys.argv)

            view = QWebEngineView()
            view.resize(1400, 1000)

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(pdf_path)
            printer.setResolution(config.dpi)
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(
                config.page_margins, config.page_margins,
                config.page_margins, config.page_margins,
                QPrinter.Millimeter
            )
            printer.setColorMode(QPrinter.Color)

            loop = QEventLoop()

            def on_load_finished(success):
                if success:
                    QTimer.singleShot(1000, lambda: view.page().printToPdf(pdf_path))
                    QTimer.singleShot(2000, loop.quit)
                else:
                    self.logger.error("Failed to load HTML for PDF conversion")
                    loop.quit()

            view.loadFinished.connect(on_load_finished)
            view.load(QUrl.fromLocalFile(os.path.abspath(html_path)))
            loop.exec()

            return True

        except Exception as e:
            self.logger.error(f"Error converting HTML to PDF: {e}", exc_info=True)
            return False