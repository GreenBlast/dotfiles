#!/usr/bin/python3
# Based on https://github.com/neingeist/task-recurring-delete

from subprocess import Popen, PIPE, STDOUT

import collections
import datetime
import os
import pytz
import taskw


def dateparse(datestr):
    """
    Parses date string
    """
    PARSE_STRING = "%Y%m%dT%H%M%SZ"
    return datetime.datetime.strptime(datestr, PARSE_STRING).replace(tzinfo=pytz.utc)


def task_delete(uuidstr):
    """Delete the given task."""

    print("Deleting uuidstr:{}".format(uuidstr))
    # This is somewhat a hack, but as TaskWwarrior 2.4.0 does NOT disable
    # the 'Do you want to delete all pending recurrences ...' confirmation
    # on rc.confirmation=off, so this is necessary.
    devnull = open(os.devnull, 'wb')
    process_instance = Popen(['task', 'rc.confirmation=off', str(uuidstr), 'delete'],
                             stdin=PIPE, stdout=devnull, stderr=STDOUT)
    process_instance.communicate(input=bytes('no', 'UTF-8'))


def main():
    """
    Main function
    """

    taskwarrior = taskw.TaskWarrior()
    tasks = taskwarrior.load_tasks()

    # Only (over-)due and recurring tasks are considered for deletion:
    due_before = datetime.datetime.utcnow()
    due_before = due_before.replace(tzinfo=pytz.utc)

    # datetime.datetime.now()
    recurring_tasks_due = [task for task in tasks['completed'] if 'recur' in task
                           and 'parent' in task
                           and 'due' in task
                           and dateparse(task['due']) < due_before]

    # Delete all but the first of all (over-)due and duplicate tasks:
    parents = collections.Counter([task['parent'] for task in recurring_tasks_due])

    for parent in parents:
        count = parents[parent]
        if count > 1:
            dupe_tasks = [task for task in recurring_tasks_due
                          if task['parent'] == parent]
            dupe_tasks = sorted(dupe_tasks, key=lambda t: t['due'])
            # dupe_tasks_to_keep = dupe_tasks[0:1]
            dupe_tasks_to_trash = dupe_tasks[1:]
            print('Deleting {} duplicate due tasks: "{}"'.format(
                len(dupe_tasks_to_trash), dupe_tasks_to_trash[0]['description']))
            for task in dupe_tasks_to_trash:
                task_delete(task['uuid'])
