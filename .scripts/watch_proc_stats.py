#!/usr/bin/python3
"""
File: watch_proc_stats.py
Description: Monitors searches for processes with names containing a \
given string and monitors those processes statistics continuously
"""
# import os
import sys
import time
import logging
import threading
import subprocess
import psutil
import datetime
import dataset

# pylint: disable=C0325

LOGGER_NAME = "ProcessesMonitor"
MIN_ARGS_COUNT = 2
MAX_ARGS_COUNT = 3
POLL_TIME_ARG_LOCATION = 3
DEFAULT_POLL_TIME = 5
DATABASE_LOCATION = "sqlite:///processes_statistics.db"

class SingleProcessMonitor(object):

    """Document statistics for a given PID process"""

    def __init__(self, pid_of_process):
        """
        Initialization
        :pid_of_process: The pid of the process

        """
        self.pid = pid_of_process
        self.process_info = psutil.Process(pid_of_process)
        self.username = self.process_info.username()
        self.cmdline = self.process_info.cmdline()

    def snapshot_process(self):
        """
        Taking a snapshot of processs statistics

        :returns: Dictionary with the process data
        """
        data = {}
        data["timestamp"] = datetime.datetime.now()
        data["Username"] = self.username
        data["PID"] = self.pid
        data["cmdline"] = self.cmdline
        data["cpu_percent"] = self.process_info.cpu_percent()
        data["memory_percent"] = self.process_info.memory_percent()

        return data

class ProcessesMonitor(object):

    """Monitor processes statistics by a given string"""

    def __init__(self, process_string, poll_time=DEFAULT_POLL_TIME):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.process_string = process_string
        self.poll_time = poll_time

        self._timer = None
        self.already_running = False
        self.should_loop = False
        self.current_pids = set()
        self.process_monitors = {}
        self.db_connection = None

    def loop(self):
        """Used to block execution while monitoring
        :returns: TODO

        """
        while self.should_loop:
            time.sleep(1)

    def snaptshot_all_processes(self):
        """
        Snapshoting all existing processes
        """
        data = {}
        for pid, monitor in self.process_monitors.items():
            data[pid] = monitor.snapshot_process()

        for pid, data_item in data.items()
            table = self.db_connection[pid]
            table.insert(data_item)

    def _run(self):
        """
        Main loop function for the code execution
        """
        self.logger.debug("Running _run")
        if self.should_loop:
            self.logger.debug("Entered main logic")
            # Get list of existing processes according to the string
            # For each new PID create a new SingleProcessMonitor
            # For each SingleProcessMonitor call snapshot stats
            child = subprocess.Popen(["pgrep", self.process_string], stdout=subprocess.PIPE, shell=False)
            result = child.communicate()[0]
            pid_result = set([int(pid) for pid in result.split()])
            new_pids = pid_result - self.current_pids
            if new_pids:
                self.logger.info("Will start monitoring these new PIDs %s", new_pids)
                self.current_pids.update(new_pids)
                for new_pid in new_pids:
                    self.logger.debug("Creating SingleProcessMonitor for PID: %s", new_pid)
                    self.process_monitors[new_pid] = SingleProcessMonitor(new_pid)

            self.snaptshot_all_processes()

        # Must be at end of _run function to create execution loop
        if self.should_loop:
            self.logger.debug("Calling _run again")
            self._timer = threading.Timer(self.poll_time, self._run)
            self._timer.start()

    def start(self):
        """
        Starts the monitoring of the process
        """
        self.logger.debug("Running start")
        if not self.already_running:
            self.should_loop = True
            self.already_running = True
            self.db_connection = dataset.connect(DATABASE_LOCATION)
            self._timer = threading.Timer(self.poll_time, self._run)
            self._timer.start()

    def stop(self):
        """
        Stopping process monitoring
        """
        self.should_loop = False
        self._timer.cancel()

    def clean(self):
        """
        Place holder for a clean function
        """
        self.already_running = False
        self.db_connection.close()


def set_logging(logger_name):
    """Setting the logger configuration for a given name

    :logger_name: TODO
    :returns: TODO

    """
    # log_file_location = r"." + os.sep + time.strftime('%Y-%m-%d-%H-%M-%S') + ".log"
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
            poll_time = float(sys.argv[2])
        except ValueError:
            print("Value for polling is not a number")
            print_usage()
            return
        except IndexError:
            pass

        logger = set_logging(LOGGER_NAME)
        monitor = ProcessesMonitor(process_string, poll_time)
        monitor.start()

        try:
            monitor.loop()
            logger.info("ProcessesMonitor has stopped working")
            monitor.stop()
            logger.info("Quitting ProcessesMonitor")
        except KeyboardInterrupt:
            monitor.stop()
            logger.info("Quitting ProcessesMonitor")
        finally:
            monitor.clean()
            # Cleaning loggers
            # map(logger.removeHandler, logger.handlers)
            logger_clean_list = [logger.removeHandler(x) for x in logger.handlers]
            if logger_clean_list:
                print(logger_clean_list)
    else:
        print_usage()


if __name__ == "__main__":
    main()
