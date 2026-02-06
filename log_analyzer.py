"""
Log Analysis Utilities for Streaming JSON Processing and Anomaly Detection
"""
import re
import json
import ijson
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime
import joblib
from sklearn.ensemble import IsolationForest


class LogTemplateExtractor:
    """Converts specific log messages into generic templates"""
    
    @staticmethod
    def extract_template(message: str) -> str:
        """
        Convert specific log to generic template by replacing variable parts
        
        Examples:
            "User 123 logged in" -> "User {num} logged in"
            "Request took 450ms" -> "Request took {num}ms"
            "Error: UUID a1b2c3d4-..." -> "Error: UUID {uuid}"
        """
        # Replace numbers with {num}
        msg = re.sub(r'\b\d+\b', '{num}', message)
        
        # Replace UUIDs with {uuid}
        msg = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 
            '{uuid}', 
            msg, 
            flags=re.IGNORECASE
        )
        
        # Replace timestamps (ISO format)
        msg = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '{timestamp}', msg)
        
        # Replace IP addresses
        msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '{ip}', msg)
        
        # Replace hex values
        msg = re.sub(r'0x[0-9a-fA-F]+', '{hex}', msg)
        
        return msg


class StreamingLogAnalyzer:
    """Analyzes large JSON log files without loading into memory"""
    
    def __init__(self):
        self.template_extractor = LogTemplateExtractor()
    
    def calculate_baseline_stats(
        self, 
        log_file_path: str,
        duration_field: str = 'duration_ms',
        message_field: str = 'message'
    ) -> Dict[str, Dict[str, float]]:
        """
        Stream through logs and calculate baseline statistics per template
        
        Args:
            log_file_path: Path to JSON log file (.json or .jsonl)
            duration_field: Field name containing duration/latency
            message_field: Field name containing log message
            
        Returns:
            Dict mapping templates to their statistics
        """
        print(f"[STATS] Calculating baseline stats from {log_file_path}...")
        
        # Accumulators (memory efficient - only stores numbers)
        template_durations = defaultdict(list)
        template_counts = defaultdict(int)
        
        # Stream parse the JSON file
        try:
            with open(log_file_path, 'rb') as f:
                # Try parsing as JSON array first
                try:
                    for record in ijson.items(f, 'item'):
                        self._process_record(record, template_durations, template_counts, 
                                           duration_field, message_field)
                except ijson.JSONError:
                    # If not array, try JSONL (one JSON per line)
                    f.seek(0)
                    for line in f:
                        try:
                            record = json.loads(line)
                            self._process_record(record, template_durations, template_counts,
                                               duration_field, message_field)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            print(f"[WARN] Log file not found: {log_file_path}")
            return {}
        
        # Calculate statistics
        stats = {}
        for template, durations in template_durations.items():
            if len(durations) >= 5:  # Minimum sample size
                stats[template] = {
                    'count': len(durations),
                    'mean': float(np.mean(durations)),
                    'std_dev': float(np.std(durations)),
                    'min': float(np.min(durations)),
                    'max': float(np.max(durations)),
                    'p50': float(np.percentile(durations, 50)),
                    'p95': float(np.percentile(durations, 95)),
                    'p99': float(np.percentile(durations, 99))
                }
        
        print(f"[OK] Baseline calculated for {len(stats)} unique templates")
        return stats
    
    def _process_record(self, record, template_durations, template_counts, 
                       duration_field, message_field):
        """Process a single log record"""
        message = record.get(message_field, '')
        duration = record.get(duration_field, 0)
        
        if message and duration:
            template = self.template_extractor.extract_template(message)
            template_durations[template].append(duration)
            template_counts[template] += 1
    
    def detect_anomalies(
        self,
        log_file_path: str,
        baseline_stats: Dict[str, Dict],
        z_score_threshold: float = 3.0,
        duration_field: str = 'duration_ms',
        message_field: str = 'message',
        session_id_field: str = 'correlation_id',  # NEW: Field for session tracking
        use_isolation_forest: bool = True,  # NEW: Enable Isolation Forest
        iso_forest_model=None  # NEW: Pre-trained Isolation Forest model
    ) -> List[Dict[str, Any]]:
        """
        Stream through logs and detect anomalies using Z-score + Isolation Forest
        
        Args:
            log_file_path: Path to JSON log file
            baseline_stats: Baseline statistics from training phase
            z_score_threshold: Z-score threshold for anomaly detection
            session_id_field: Field name for session/correlation ID (e.g., request_id, trace_id)
            use_isolation_forest: Whether to use Isolation Forest for detection
            iso_forest_model: Pre-trained IsolationForestAnalyzer instance
            
        Returns:
            List of detected anomalies with full session context
        """
        from collections import deque, defaultdict
        
        print(f"[SEARCH] Detecting anomalies in {log_file_path}...")
        
        anomalies = []
        total_processed = 0
        
        # Session tracking: Maps session_id -> list of all logs in that session
        session_logs = defaultdict(list)
        
        # Context buffer for logs without session IDs
        context_buffer = deque(maxlen=10)
        
        try:
            with open(log_file_path, 'rb') as f:
                # Try JSON array format
                try:
                    records = list(ijson.items(f, 'item'))
                    
                    # First pass: Group logs by session
                    for record in records:
                        session_id = record.get(session_id_field)
                        if session_id:
                            session_logs[session_id].append(record)
                    
                    # Second pass: Detect anomalies
                    for i, record in enumerate(records):
                        # Z-Score detection
                        anomaly = self._check_record_for_anomaly(
                            record, baseline_stats, z_score_threshold,
                            duration_field, message_field
                        )
                        
                        # Isolation Forest detection (if enabled)
                        if use_isolation_forest and iso_forest_model and iso_forest_model.is_trained:
                            iso_anomaly = self._check_isolation_forest_anomaly(
                                record, baseline_stats, iso_forest_model,
                                duration_field, message_field
                            )
                            if iso_anomaly and not anomaly:
                                anomaly = iso_anomaly
                        
                        if anomaly:
                            session_id = record.get(session_id_field)
                            
                            if session_id and session_id in session_logs:
                                # Use FULL SESSION CONTEXT
                                session_context = session_logs[session_id]
                                anomaly_index = session_context.index(record)
                                
                                anomaly['context'] = {
                                    'session_id': session_id,
                                    'session_logs': session_context,  # ENTIRE session
                                    'anomaly_position': anomaly_index,
                                    'session_start': session_context[0].get('timestamp'),
                                    'session_end': session_context[-1].get('timestamp'),
                                    'total_logs_in_session': len(session_context),
                                    'context_type': 'FULL_SESSION'
                                }
                            else:
                                # Fallback to window-based context
                                previous_context = list(context_buffer)
                                future_context = records[i+1:i+11] if i+1 < len(records) else []
                                
                                anomaly['context'] = {
                                    'previous_logs': previous_context,
                                    'current_log': record,
                                    'next_logs': future_context,
                                    'position': i,
                                    'context_type': 'WINDOW_BASED'
                                }
                            
                            anomalies.append(anomaly)
                        
                        # Update buffer
                        context_buffer.append(record)
                        total_processed += 1
                        
                except ijson.JSONError:
                    # Try JSONL format
                    f.seek(0)
                    lines = f.readlines()
                    records = []
                    
                    # Parse all records first
                    for line in lines:
                        try:
                            record = json.loads(line)
                            records.append(record)
                            session_id = record.get(session_id_field)
                            if session_id:
                                session_logs[session_id].append(record)
                        except json.JSONDecodeError:
                            continue
                    
                    # Detect anomalies
                    for i, record in enumerate(records):
                        anomaly = self._check_record_for_anomaly(
                            record, baseline_stats, z_score_threshold,
                            duration_field, message_field
                        )
                        
                        # Isolation Forest check
                        if use_isolation_forest and iso_forest_model and iso_forest_model.is_trained:
                            iso_anomaly = self._check_isolation_forest_anomaly(
                                record, baseline_stats, iso_forest_model,
                                duration_field, message_field
                            )
                            if iso_anomaly and not anomaly:
                                anomaly = iso_anomaly
                        
                        if anomaly:
                            session_id = record.get(session_id_field)
                            
                            if session_id and session_id in session_logs:
                                session_context = session_logs[session_id]
                                anomaly_index = session_context.index(record)
                                
                                anomaly['context'] = {
                                    'session_id': session_id,
                                    'session_logs': session_context,
                                    'anomaly_position': anomaly_index,
                                    'session_start': session_context[0].get('timestamp'),
                                    'session_end': session_context[-1].get('timestamp'),
                                    'total_logs_in_session': len(session_context),
                                    'context_type': 'FULL_SESSION'
                                }
                            else:
                                previous_context = list(context_buffer)
                                future_context = records[i+1:i+11] if i+1 < len(records) else []
                                
                                anomaly['context'] = {
                                    'previous_logs': previous_context,
                                    'current_log': record,
                                    'next_logs': future_context,
                                    'position': i,
                                    'context_type': 'WINDOW_BASED'
                                }
                            
                            anomalies.append(anomaly)
                        
                        context_buffer.append(record)
                        total_processed += 1
                        
        except FileNotFoundError:
            print(f"[WARN] Log file not found: {log_file_path}")
            return []
        
        print(f"[OK] Processed {total_processed} logs, found {len(anomalies)} anomalies")
        if session_logs:
            print(f"[OK] Tracked {len(session_logs)} unique sessions")
        return anomalies
    
    def _check_isolation_forest_anomaly(self, record, baseline_stats, iso_forest_model,
                                       duration_field, message_field):
        """Check if record is anomalous using Isolation Forest"""
        message = record.get(message_field, '')
        duration = record.get(duration_field, 0)
        
        if not message:
            return None
        
        template = self.template_extractor.extract_template(message)
        
        # Get stats for this template
        if template in baseline_stats:
            stats = baseline_stats[template]
            
            # Create feature vector
            features = np.array([[
                stats['mean'],
                stats['std_dev'],
                stats['p95'],
                stats['count']
            ]])
            
            # Predict (-1 = anomaly, 1 = normal)
            prediction = iso_forest_model.model.predict(features)[0]
            
            if prediction == -1:
                # Get anomaly score
                score = iso_forest_model.model.score_samples(features)[0]
                
                return {
                    'timestamp': record.get('timestamp', datetime.now().isoformat()),
                    'level': record.get('level', 'INFO'),
                    'message': message,
                    'template': template,
                    'duration': duration,
                    'anomaly_type': 'ISOLATION_FOREST_ANOMALY',
                    'severity': 'HIGH' if score < -0.5 else 'MEDIUM',
                    'isolation_score': float(score),
                    'expected_mean': stats['mean']
                }
        
        return None
    
    def _check_record_for_anomaly(self, record, baseline_stats, z_score_threshold,
                                  duration_field, message_field):
        """Check if a single record is anomalous using Z-score"""
        message = record.get(message_field, '')
        duration = record.get(duration_field, 0)
        timestamp = record.get('timestamp', datetime.now().isoformat())
        level = record.get('level', 'INFO')
        
        if not message:
            return None
        
        template = self.template_extractor.extract_template(message)
        
        # Check if we have baseline for this template
        if template in baseline_stats:
            stats = baseline_stats[template]
            
            # Avoid division by zero
            if stats['std_dev'] == 0:
                return None
            
            # Calculate Z-score
            z_score = (duration - stats['mean']) / stats['std_dev']
            
            if abs(z_score) > z_score_threshold:
                return {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message,
                    'template': template,
                    'duration': duration,
                    'expected_mean': stats['mean'],
                    'expected_std': stats['std_dev'],
                    'z_score': float(z_score),
                    'anomaly_type': 'DURATION_SPIKE' if z_score > 0 else 'DURATION_DROP',
                    'severity': 'HIGH' if abs(z_score) > 5 else 'MEDIUM'
                }
        else:
            # New template = potential anomaly
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'template': template,
                'duration': duration,
                'anomaly_type': 'NEW_PATTERN',
                'severity': 'MEDIUM',
                'z_score': None
            }
        
        return None


class IsolationForestAnalyzer:
    """Optional: Multi-dimensional anomaly detection using Isolation Forest"""
    
    def __init__(self, contamination: float = 0.01):
        """
        Args:
            contamination: Expected proportion of anomalies (0.01 = 1%)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
    
    def train_on_baseline(self, baseline_stats: Dict[str, Dict]) -> None:
        """Train Isolation Forest on baseline statistics"""
        print("[AI] Training Isolation Forest model...")
        
        # Build feature matrix from baseline stats
        features = []
        template_names = []
        
        for template, stats in baseline_stats.items():
            features.append([
                stats['mean'],
                stats['std_dev'],
                stats['p95'],
                stats['count']
            ])
            template_names.append(template)
        
        if len(features) < 10:
            print("[WARN] Not enough data for Isolation Forest (need at least 10 templates)")
            return
        
        features_array = np.array(features)
        self.model.fit(features_array)
        self.is_trained = True
        self.template_names = template_names
        
        print(f"[OK] Model trained on {len(features)} templates")
    
    def save_model(self, filepath: str = 'iso_forest_model.joblib'):
        """Save trained model to disk"""
        if self.is_trained:
            joblib.dump(self.model, filepath)
            print(f"[OK] Model saved to {filepath}")
    
    def load_model(self, filepath: str = 'iso_forest_model.joblib'):
        """Load trained model from disk"""
        try:
            self.model = joblib.load(filepath)
            self.is_trained = True
            print(f"[OK] Model loaded from {filepath}")
        except FileNotFoundError:
            print(f"[WARN] Model file not found: {filepath}")


def save_baseline_stats(stats: Dict, filepath: str = 'baseline_stats.json'):
    """Save baseline statistics to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"[OK] Baseline stats saved to {filepath}")


def load_baseline_stats(filepath: str = 'baseline_stats.json') -> Dict:
    """Load baseline statistics from JSON file"""
    try:
        with open(filepath, 'r') as f:
            stats = json.load(f)
        print(f"[OK] Baseline stats loaded from {filepath}")
        return stats
    except FileNotFoundError:
        print(f"[WARN] Baseline stats file not found: {filepath}")
        return {}