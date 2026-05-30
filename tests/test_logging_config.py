"""
Comprehensive unit tests for logging_config.py

This test suite covers all functionality in logging_config.py
to ensure 100% code coverage from a senior developer perspective.
"""

import pytest
import logging
import tempfile
import os
from src.logging_config import setup_logging, get_logger


class TestSetupLogging:
    """Test cases for setup_logging function."""
    
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        logger = setup_logging()
        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1  # Console handler only
    
    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level."""
        logger = setup_logging(level=logging.DEBUG)
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_with_file(self):
        """Test setup_logging with file handler."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            logger = setup_logging(log_file=log_file)
            assert logger is not None
            assert len(logger.handlers) == 2  # Console + file handler
            # Close file handlers before cleanup
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)
        finally:
            # Try to delete the file, ignore if still locked
            try:
                os.unlink(log_file)
            except PermissionError:
                pass
    
    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format string."""
        custom_format = '%(levelname)s: %(message)s'
        logger = setup_logging(format_string=custom_format)
        assert logger is not None
        # Check that handlers use the custom format
        for handler in logger.handlers:
            assert handler.formatter._fmt == custom_format
    
    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        # First setup
        logger1 = setup_logging()
        initial_handler_count = len(logger1.handlers)
        
        # Second setup should clear and add new handlers
        logger2 = setup_logging()
        assert len(logger2.handlers) == initial_handler_count
    
    def test_setup_logging_all_parameters(self):
        """Test setup_logging with all parameters."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            custom_format = '%(name)s - %(message)s'
            logger = setup_logging(
                level=logging.WARNING,
                log_file=log_file,
                format_string=custom_format
            )
            assert logger.level == logging.WARNING
            assert len(logger.handlers) == 2
            for handler in logger.handlers:
                assert handler.formatter._fmt == custom_format
            # Close file handlers before cleanup
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)
        finally:
            # Try to delete the file, ignore if still locked
            try:
                os.unlink(log_file)
            except PermissionError:
                pass


class TestGetLogger:
    """Test cases for get_logger function."""
    
    def test_get_logger_default(self):
        """Test get_logger with default name."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
    
    def test_get_logger_module_name(self):
        """Test get_logger with module name."""
        logger = get_logger(__name__)
        assert logger is not None
        assert logger.name == __name__
    
    def test_get_logger_same_name_returns_same_instance(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("test_same")
        logger2 = get_logger("test_same")
        assert logger1 is logger2
