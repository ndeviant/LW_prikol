"""Logging configuration"""

import atexit
import io
import logging
import logging.handlers
import sys
from pathlib import Path
import queue
import datetime

Path("logs").mkdir(exist_ok=True)

# 1. Create a Queue for log messages
log_queue = queue.Queue(-1) # -1 means infinite size

# 2. Create the actual handler that will write to file
file_handler = logging.handlers.TimedRotatingFileHandler(
    'logs/app.log', # Base filename - it will add date extensions
    when='midnight',
    interval=1,
    backupCount=30, # Keep logs for the last 30 days
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# 3. Create a QueueHandler that puts messages into the queue
queue_handler = logging.handlers.QueueHandler(log_queue)

# 4. Create a QueueListener that reads from the queue and dispatches to the file_handler
queue_listener = logging.handlers.QueueListener(log_queue, file_handler, respect_handler_level=True)
queue_listener.start() # Start the listener thread

app_logger = logging.getLogger('app')
app_logger.addHandler(queue_handler) # Add the QueueHandler to your logger

# Add console handler as before (this one is still blocking to console)
utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
console_handler = logging.StreamHandler(utf8_stdout)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
))
app_logger.addHandler(console_handler)

atexit.register(queue_listener.stop)

def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    app_logger.setLevel(level)