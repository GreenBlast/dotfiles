#!/usr/bin/python3
"""
File: watch_proc_stats.py
Description: Monitors searches for processes with names containing a \
given string and monitors those processes statistics continuously
"""
# pylint: disable=C0325,R0902,R0903,E1101,F0401
# import os
import sys
import time
import logging
import threading
import subprocess
import psutil
import datetime
import queue
import dataset
import datafreeze


LOGGER_NAME = "ProcessesMonitor"
HELP_ARGS_NUMBER = 2
EXPORT_ARGS_NUMBER = 2
MIN_ARGS_COUNT = 2
MAX_ARGS_COUNT = 3
POLL_TIME_ARG_LOCATION = 3
DEFAULT_POLL_TIME = 5
DATABASE_LOCATION = "sqlite:///processes_statistics.db?check_same_thread=False"

class DataExporter(object):

    """Exporting all the data from the tables to csv"""

    def __init__(self, db_location_uri):
        """
        :db_location_uri: Location of the database

        """
        self.logger = logging.getLogger(LOGGER_NAME)
        self.db_location_uri = db_location_uri

    def export(self):
        """
        Exporting the data in the database
        """
        database_connection = dataset.connect(self.db_location_uri)
        for table_name in database_connection.tables:
            file_name = table_name + ".csv"
            file_name = file_name.replace("/", "_")
            self.logger.debug("About to export filename %s", file_name)
            result = database_connection[table_name].all()
            datafreeze.freeze(result, format="csv", filename=file_name)


class DatabaseManager(object):

    """Handles instance of database connection and synchronizes writes to database"""
    def __init__(self, db_location_uri):
        """
            Initialization function
            :db_location_uri: Location of the database
        """
        self.logger = logging.getLogger(LOGGER_NAME)
        self.db_location_uri = db_location_uri
        self.database_connection = None
        self.stored_thread_id = None
        self.consumer_thread = None
        self.lock = threading.Lock()
        self.queue = queue.Queue()

    def consumer_loop(self):
        """
        Continuously consumes data from the queue and stores it
        """
        self.logger.debug("Starting consumer")
        self.validate_connection()
        data = self.queue.get()
        while data:
            table_name = data[0]
            data_item = data[1]
            table = self.database_connection[table_name]
            table.insert(data_item)
            data = self.queue.get()

        self.disconnect()
        self.logger.debug("Consumer thread about to stop id:%s", threading.get_ident())
        self.logger.debug("Stopping consumer")

    def insert_to_db(self, table_name, data_item):
        """
        Inserts data to a table

        :table_name: Name of the table to insert data to
        :data_item: The data item to insert
        """
        self.logger.debug("In thread:%s", threading.get_ident())
        with self.lock:
            if not self.consumer_thread:
                self.consumer_thread = threading.Thread(name="consumer_thread", target=self.consumer_loop)
                self.consumer_thread.start()

        self.queue.put([table_name, data_item])

    def validate_connection(self):
        """
        Making sure that there is a valid connection to the database registered on this thread
        """
        if self.database_connection:
            if threading.get_ident() != self.stored_thread_id:
                self.disconnect()
                self.connect()
        else:
            self.connect()

    def connect(self):
        """
        Setting a connection to the database
        """
        self.logger.debug("Connecting database")
        self.stored_thread_id = threading.get_ident()
        self.database_connection = dataset.connect(self.db_location_uri)

    def disconnect(self):
        """
        Closing the connection after finishing using it
        """
        # This is a hack to handle SqlAlchemy pooling connections and then being angry that they are not being accessed from  the same thread
        self.logger.debug("Disconnecting database")
        self.database_connection.engine.dispose()
        self.database_connection = None
        self.stored_thread_id = None

    def clean(self):
        """
        Cleanup: Stopping the consumer thread
        """
        with self.lock:
            if self.consumer_thread:
                self.queue.put(None)

                self.consumer_thread.join()
                self.consumer_thread = None

        self.logger.debug("Finished cleanup")



class SingleProcessMonitor(object):

    """Document statistics for a given PID process"""

    def __init__(self, pid_of_process):
        """
        Initialization
        :pid_of_process: The pid of the process

        """
        self.logger = logging.getLogger(LOGGER_NAME)
        self.pid = pid_of_process
        self.creation_timestamp = datetime.datetime.now()
        self.process_info = None
        self.username = None
        self.cmdline = None
        try:
            self.process_info = psutil.Process(pid_of_process)
            self.username = self.process_info.username()
            self.cmdline = self.process_info.cmdline()
        except psutil.NoSuchProcess:
            self.logger.info("Failed getting initial data for process:%s", pid_of_process)

    def snapshot_process(self):
        """
        Taking a snapshot of processs statistics

        :returns: Dictionary with the process data
        """
        data = {}
        now = datetime.datetime.now()
        if self.process_info:
            try:
                data["timestamp"] = now
                data["time_since_tracking_start"] = (now - self.creation_timestamp).total_seconds()
                data["Username"] = self.username
                data["PID"] = self.pid
                data["exec_name"] = self.cmdline[0]
                data["cmdline"] = " ".join(self.cmdline)
                data["cpu_percent"] = self.process_info.cpu_percent()
                data["total_reserved_memory"] = self.process_info.memory_info()[0]
                data["memory_percent"] = self.process_info.memory_percent()
            except psutil.NoSuchProcess:
                self.logger.info("Couldn't snapshot process with id:%s. cmline:\"%s\"", self.pid, self.cmdline)

        return data
class ProcessesMonitor(object):

    """Monitor processes statistics by a given string"""

    def __init__(self, process_string, database_manager, poll_time=DEFAULT_POLL_TIME):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.process_string = process_string
        self.database_manager = database_manager
        self.poll_time = poll_time

        self._timer = None
        self.already_running = False
        self.should_loop = False
        self.current_pids = set()
        self.process_monitors = {}

    def loop(self):
        """Used to block execution while monitoring
        """
        while self.should_loop:
            time.sleep(1)

    def snaptshot_all_processes(self):
        """
        Snapshotting all existing processes
        """
        self.logger.debug("Snapshotting data of: %s", self.current_pids)
        data = {}
        for pid in self.current_pids:
            data[pid] = self.process_monitors[pid].snapshot_process()

        for pid, data_item in data.items():
            if data_item:
                self.database_manager.insert_to_db(str(pid) + "_" + data_item["exec_name"], data_item)

    def _run(self):
        """
        Main loop function for the code execution
        """
        self.logger.debug("Running _run")
        if self.should_loop:
            self.logger.debug("Entered main logic")
            # Get list of existing processes according to the string
            child = subprocess.Popen(["pgrep", self.process_string], stdout=subprocess.PIPE, shell=False)
            result = child.communicate()[0]
            pid_result = set([int(pid) for pid in result.split()])
            new_pids = pid_result - self.current_pids
            self.current_pids = pid_result
            if new_pids:
                self.logger.info("Will start monitoring these new PIDs %s", new_pids)
                # For each new PID create a new SingleProcessMonitor
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
        if self.already_running:
            self.already_running = False
            self.should_loop = False
            self._timer.join()

        self.logger.debug("Finished cleanup")


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

def clean_logger_handlers(logger):
    """
    Clean the handlers saved into a logger
    """
    logger_clean_list = [logger.removeHandler(x) for x in logger.handlers]
    if logger_clean_list:
        print(logger_clean_list)

def print_usage():
    """Prints usage """
    print("""Monitors searches for processes with names containing a\n \
    given string and monitors those processes statistics continuously\n""".format(sys.argv[0]))
    print ("Usage:")
    print("\t{} -h - Displays this help message".format(sys.argv[0]))
    print("\t{} process_string [poll_time_in_seconds(default=5)] - Start monitoring data".format(sys.argv[0]))
    print("\t{} -e - Exports data from database to csv files".format(sys.argv[0]))

def main():
    """
    Main function:
        Checks arguments and calls main logic
    """
    numargs = len(sys.argv)

    if HELP_ARGS_NUMBER == numargs and "-h" == sys.argv[1]:
        print_usage()
    elif EXPORT_ARGS_NUMBER == numargs and "-e" == sys.argv[1]:
        logger = set_logging(LOGGER_NAME)
        try:
            data_exporter = DataExporter(DATABASE_LOCATION)
            data_exporter.export()
        except Exception as exception_object:
            raise exception_object
        finally:
            clean_logger_handlers(logger)
    elif numargs >= MIN_ARGS_COUNT and numargs <= MAX_ARGS_COUNT:
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
        database_manager = DatabaseManager(DATABASE_LOCATION)
        monitor = ProcessesMonitor(process_string, database_manager, poll_time)
        monitor.start()

        try:
            monitor.loop()
            logger.info("ProcessesMonitor has stopped working")
            monitor.stop()
            logger.info("Quitting ProcessesMonitor")
        except KeyboardInterrupt:
            logger.info("Quitting ProcessesMonitor")
            monitor.stop()
        finally:
            monitor.stop()
            monitor.clean()
            database_manager.clean()
            logger.debug("Main about to exit thread id:%s", threading.get_ident())
            clean_logger_handlers(logger)
    else:
        print_usage()


if __name__ == "__main__":
    main()
