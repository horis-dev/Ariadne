from datetime import datetime
import os
import re
from typing import List

from apt_pkg import time_to_str

# Log file path
COUCHDB_LOG_PATH = "./logs/couch.log"
# Can also be configured via an environment variable
log_path_env = os.environ.get("COUCHDB_LOG")
if log_path_env is not None:
    COUCHDB_LOG_PATH = log_path_env

# Saved log read position
_log_position: int = 0


def update_log_position():
    """Explicitly update the log read position by seeking to the end of the file."""
    global _log_position

    try:
        with open(COUCHDB_LOG_PATH, 'r') as f:
            # Move to end of file
            f.seek(0, 2)
            # Update global position
            _log_position = f.tell()
            return _log_position
    except Exception as e:
        print(f"Error updating log position: {e}")
        return _log_position


def _read_new_log_lines() -> List[str]:
    """Read new lines from the log without updating the saved position."""

    # Check if the log file exists
    if not os.path.exists(COUCHDB_LOG_PATH):
        return []

    try:
        with open(COUCHDB_LOG_PATH, 'r') as f:
            # Seek to the current saved position
            f.seek(_log_position)
            # Read new lines
            new_lines = f.readlines()
            # Note: we do not update _log_position here
            return new_lines
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []


def get_db_write() -> List[str]:
    """Parse database write operations and return a list of database names.
    Includes:
    1. Direct database writes (PUT /db_name 201)
    2. Implicit database operations via document writes (PUT /db_name/doc_id 201)
    """
    new_lines = _read_new_log_lines()
    result = []

    # Regex for direct database write
    db_write_pattern = re.compile(r'\] (\d+\.\d+\.\d+\.\d+) .* PUT /(\w+) 201')
    # Regex for implicit database ops during document writes
    doc_write_pattern = re.compile(r'\] (\d+\.\d+\.\d+\.\d+) .* PUT /(\w+)/\w+ 201')

    for line in new_lines:
        # Check direct database write
        match = db_write_pattern.search(line)
        if match:
            db_name = match.group(2)
            if not db_name.startswith('_') and db_name not in result:
                result.append(db_name)
                continue

        # Check implicit database operation via document write
        match = doc_write_pattern.search(line)
        if match:
            db_name = match.group(2)
            if not db_name.startswith('_') and db_name not in result:
                result.append(db_name)

    return result


def get_db_read() -> List[str]:
    """Parse database read operations and return a list of database names.
    Includes:
    1. Direct database reads (GET /db_name 200)
    2. Implicit database operations via document reads (GET /db_name/doc_id 200)
    """
    new_lines = _read_new_log_lines()
    result = []

    # Regex for direct database read
    db_read_pattern = re.compile(r'\] (\d+\.\d+\.\d+\.\d+) .* GET /(\w+) 200')
    # Regex for implicit database ops during document reads
    doc_read_pattern = re.compile(r'\] (\d+\.\d+\.\d+\.\d+) .* GET /(\w+)/\w+ 200')

    for line in new_lines:
        # Check direct database read
        match = db_read_pattern.search(line)
        if match:
            db_name = match.group(2)
            if not db_name.startswith('_') and db_name not in result:
                result.append(db_name)
                continue

        # Check implicit database operation via document read
        match = doc_read_pattern.search(line)
        if match:
            db_name = match.group(2)
            if not db_name.startswith('_') and db_name not in result:
                result.append(db_name)

    return result


def get_doc_write() -> List[str]:
    """Parse document write operations and return a list of document IDs."""
    # Regex for document write operations
    doc_write_pattern = re.compile(r'\] (\d+\.\d+\.\d+\.\d+) .* PUT /(\w+)/(\w+) 201')

    result = []
    new_lines = _read_new_log_lines()

    for line in new_lines:
        match = doc_write_pattern.search(line)
        if match:
            db_name = match.group(2)
            doc_id = match.group(3)
            # Filter out system databases and system documents
            if not db_name.startswith('_') and not doc_id.startswith('_'):
                result.append(doc_id)

    return result


def get_doc_read() -> List[str]:
    """Parse document read operations and return a list of document IDs."""
    # Regex for document read operations
    doc_read_pattern = re.compile(r'\] (\d+\.\d+\.\d+\.\d+) .* GET /(\w+)/(\w+) 200')

    result = []
    new_lines = _read_new_log_lines()

    for line in new_lines:
        match = doc_read_pattern.search(line)
        if match:
            db_name = match.group(2)
            doc_id = match.group(3)
            # Filter out system databases and system documents
            if not db_name.startswith('_') and not doc_id.startswith('_'):
                result.append(doc_id)

    return result


def get_file_read() -> List[str]:
    return []


def get_file_write() -> List[str]:
    return []


def get_file_read_write(flow_ts, log_file, container_name):
    def parse_sysdig_events(start_ts: float, end_ts: float, log_file: str = "./tmp/sysdig_file_events.log"):
        reads = set()
        writes = set()

        def time_str_to_timestamp(time_str):
            # Assume time_str is like '20:19:04.553723788'
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            # Take the first 6 digits of microseconds and drop the nanosecond remainder
            t_main, t_ns = time_str.split('.')
            t_micro = t_ns[:6].ljust(6, '0')  # pad to 6 microseconds
            dt = datetime.strptime(f"{date_str} {t_main}.{t_micro}", "%Y-%m-%d %H:%M:%S.%f")
            return dt.timestamp()

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                # print(line)
                # ts = parse_time(line)
                ts = time_str_to_timestamp(parts[0])
                ts += 8 * 3600
                # print('ts:', ts)
                # print('start:', start_ts)
                file_name = parts[-1]
                # print('ts:', ts)
                # print('file_name', file_name)
                if ts is None or ts < start_ts or ts > end_ts or file_name[0] != '/':
                    continue
                # Check operation type and file path
                if 'open' in line or 'openat' in line or 'read' in line or 'fopen' in line:
                    # e.g., ... fd=3(<f>/var/www/data.txt) ...
                    reads.add(file_name)
                if 'write' in line or 'creat' in line or 'unlink' in line:
                    writes.add(file_name)
        return list(reads), list(writes)

    start_ts = flow_ts - 1
    end_ts = flow_ts + 1
    reads, writes = parse_sysdig_events(start_ts, end_ts, log_file)
    return reads, writes
