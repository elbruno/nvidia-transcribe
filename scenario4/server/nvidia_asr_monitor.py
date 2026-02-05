"""
NVIDIA ASR Transcription Monitoring Module
Custom monitoring for transcription service operations.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NvidiaTranscriptionMonitor:
    """
    Monitors NVIDIA ASR transcription operations and tracks metrics.
    Integrates with Azure cloud monitoring when credentials are available.
    """
    
    def __init__(self):
        self.cloud_monitoring_active = False
        self.azure_connection = os.getenv("NVIDIA_TRANSCRIBE_INSIGHTS_CONNECTION")
        
        if not self.azure_connection:
            # Try alternate environment variable names
            self.azure_connection = os.getenv("APPINSIGHTS_CONN_STR") or os.getenv("AZURE_MONITOR_CONNECTION")
        
        if self.azure_connection:
            self._setup_azure_monitoring()
        else:
            logger.info("🔧 NVIDIA Transcription Monitor: Running in local mode (no cloud connection)")
    
    def _setup_azure_monitoring(self):
        """Configure Azure monitoring integration."""
        try:
            from opencensus.ext.azure.log_exporter import AzureLogHandler
            from opencensus.ext.azure.metrics_exporter import MetricsExporter
            from opencensus.stats import stats, view, measure, aggregation
            
            # Create Azure log handler for transcription logs
            azure_log_handler = AzureLogHandler(connection_string=self.azure_connection)
            logger.addHandler(azure_log_handler)
            logger.setLevel(logging.INFO)
            
            # Setup metrics collection
            self.azure_metrics = MetricsExporter(connection_string=self.azure_connection)
            self.stats_handler = stats.stats
            self.view_handler = self.stats_handler.view_manager
            self.metrics_recorder = self.stats_handler.stats_recorder
            
            # Define transcription-specific measurements
            self.measure_transcription_time = measure.MeasureFloat(
                "nvidia_asr/transcription_elapsed_ms",
                "Milliseconds elapsed during ASR transcription",
                "ms"
            )
            
            self.measure_audio_bytes = measure.MeasureInt(
                "nvidia_asr/input_audio_bytes",
                "Audio file size in bytes",
                "bytes"
            )
            
            self.measure_output_chars = measure.MeasureInt(
                "nvidia_asr/output_text_characters",
                "Character count in transcription output",
                "chars"
            )
            
            # Create metric views
            time_view = view.View(
                "transcription_time_distribution",
                "Time distribution for ASR operations",
                [],
                self.measure_transcription_time,
                aggregation.LastValueAggregation()
            )
            
            audio_view = view.View(
                "audio_size_distribution",
                "Audio file size distribution",
                [],
                self.measure_audio_bytes,
                aggregation.LastValueAggregation()
            )
            
            output_view = view.View(
                "output_length_distribution",
                "Transcription output length distribution",
                [],
                self.measure_output_chars,
                aggregation.LastValueAggregation()
            )
            
            # Register views and exporter
            self.view_handler.register_view(time_view)
            self.view_handler.register_view(audio_view)
            self.view_handler.register_view(output_view)
            self.view_handler.register_exporter(self.azure_metrics)
            
            self.cloud_monitoring_active = True
            logger.info("✅ NVIDIA Transcription Monitor: Azure integration enabled")
            
        except ImportError:
            logger.warning("⚠️ Azure monitoring packages unavailable. Install: pip install opencensus-ext-azure")
        except Exception as error:
            logger.warning(f"⚠️ Azure monitoring setup failed: {error}")
    
    def record_job_initiated(self, job_identifier: str, audio_filename: str, file_bytes: int):
        """Record when a transcription job starts."""
        log_data = {
            "event": "transcription_initiated",
            "job_id": job_identifier,
            "filename": audio_filename,
            "size_bytes": file_bytes,
            "timestamp_utc": datetime.utcnow().isoformat()
        }
        self._write_event_log("JOB_STARTED", log_data)
    
    def record_job_finished(self, job_identifier: str, elapsed_milliseconds: float, 
                           input_bytes: int, output_characters: int, segment_count: int):
        """Record successful completion of transcription job."""
        log_data = {
            "event": "transcription_completed",
            "job_id": job_identifier,
            "duration_ms": elapsed_milliseconds,
            "input_size_bytes": input_bytes,
            "output_length_chars": output_characters,
            "segments": segment_count,
            "timestamp_utc": datetime.utcnow().isoformat()
        }
        self._write_event_log("JOB_COMPLETED", log_data)
        
        # Record metrics if cloud monitoring is active
        if self.cloud_monitoring_active:
            self._record_cloud_metrics(elapsed_milliseconds, input_bytes, output_characters)
    
    def record_job_error(self, job_identifier: str, error_description: str, exception_obj: Optional[Exception] = None):
        """Record transcription job failure."""
        log_data = {
            "event": "transcription_failed",
            "job_id": job_identifier,
            "error": error_description,
            "timestamp_utc": datetime.utcnow().isoformat()
        }
        
        if exception_obj:
            log_data["exception_type"] = type(exception_obj).__name__
            logger.error(f"❌ Transcription Error: {error_description}", exc_info=exception_obj)
        else:
            logger.error(f"❌ Transcription Error: {error_description}")
    
    def record_model_load(self, model_identifier: str, load_seconds: float, device_name: str, gpu_detected: bool):
        """Record ASR model loading event."""
        log_data = {
            "event": "model_loaded",
            "model": model_identifier,
            "load_time_seconds": load_seconds,
            "device": device_name,
            "gpu_available": gpu_detected,
            "timestamp_utc": datetime.utcnow().isoformat()
        }
        self._write_event_log("MODEL_READY", log_data)
    
    def _write_event_log(self, event_category: str, properties: Dict[str, Any]):
        """Write structured event to logs."""
        prop_strings = [f"{key}={value}" for key, value in properties.items()]
        logger.info(f"[{event_category}] {' | '.join(prop_strings)}")
    
    def _record_cloud_metrics(self, time_ms: float, audio_bytes: int, text_chars: int):
        """Send metrics to Azure cloud."""
        try:
            from opencensus.tags import tag_map
            
            tag_mapping = tag_map.TagMap()
            measurement_map = self.metrics_recorder.new_measurement_map()
            
            measurement_map.measure_float_put(self.measure_transcription_time, time_ms)
            measurement_map.measure_int_put(self.measure_audio_bytes, audio_bytes)
            measurement_map.measure_int_put(self.measure_output_chars, text_chars)
            
            measurement_map.record(tag_mapping)
        except Exception as error:
            logger.debug(f"Cloud metric recording skipped: {error}")


# Singleton instance for the application
asr_monitor = NvidiaTranscriptionMonitor()
