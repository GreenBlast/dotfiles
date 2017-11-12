#!/usr/bin/python3
"""
File: watch_proc_stats.py
Description: Monitors searches for processes with names containing a \
given string and monitors those processes statistics continuously
"""
import os
import sys
import time
import logging

# pylint: disable=C0325

LOGGER_NAME = "ProcessMonitor"
MIN_ARGS_COUNT = 2
MAX_ARGS_COUNT = 3
POLL_TIME_ARG_LOCATION = 3
DEFAULT_POLL_TIME = 5

class ProcessesMonitor(object):

    """Monitor processes statistics by a given string"""

    def __init__(self, process_string, poll_time=DEFAULT_POLL_TIME):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.process_string = process_string
        self.poll_time = poll_time

        self.should_loop = False

    def loop(self):
        """Used to block execution while monitoring
        :returns: TODO

        """
        while self.should_loop:
            time.sleep(1)

    def start(self):
        """Starts the monitoring of the process
        """
        self.should_loop = True

    def stop(self):
        """
        Stopping process monitoring
        """
        self.should_loop = False

    def clean(self):
        """
        Place holder for a clean function
        """
        pass


def set_logging(logger_name):
    """Setting the logger configuration for a given name

    :logger_name: TODO
    :returns: TODO

    """
    log_file_location = r"." + os.sep + time.strftime('%Y-%m-%d-%H-%M-%S') + ".log"
    # log_level = logging.INFO
    log_level = logging.DEBUG

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Multiplexing log lines
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    # file_handler = logging.FileHandler(log_file_location, mode='w')
    # file_handler.setFormatter(formatter)
    # file_handler.setLevel(logging.INFO)
    # logger.addHandler(file_handler)
    logger.info("Logger was set")
    return logger

def print_usage():
    """Prints usage """
    print("""{} monitors searches for processes with names containing a\n \
            given string and monitors those processes statistics continuously\n""".format(sys.argv[0]))
    print ("\tUsage: {} process_string [poll_time_in_seconds(default=5)]".format(sys.argv[0]))

def main():
    """
    Main function:
        Checks arguments and calls main logic
    """
    numargs = len(sys.argv)

    if numargs >= MIN_ARGS_COUNT and numargs <= MAX_ARGS_COUNT:
        process_string = sys.argv[1]
        poll_time = DEFAULT_POLL_TIME

        try:
            poll_time = sys.argv[2]
        except IndexError as e:
            pass

        logger = set_logging(LOGGER_NAME)
        monitor = ProcessesMonitor(process_string, poll_time)
        monitor.start()

        try:
            monitor.loop()
            logger.info("ProcessMonitor has stopped working")
            monitor.stop()
            logger.info("Quitting ProcessMonitor")
        except KeyboardInterrupt:
            monitor.stop()
            logger.info("Quitting ProcessMonitor")
        finally:
            monitor.clean()
            # Cleaning loggers
            # map(logger.removeHandler, logger.handlers)
            logger_clean_list = [ logger.removeHandler(x) for x in logger.handlers ]
            print(logger_clean_list)
    else:
        print_usage()


if __name__ == "__main__":
    main()
