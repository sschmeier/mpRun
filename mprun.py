#!/usr/bin/env python
"""
NAME: mprun.py
==============

DESCRIPTION
===========
Take a CMD that requires one INPUT and one OUTPUT files and run
the CMD on a set of files via multiple processes simultaneously.

INSTALLATION
============
1. Download mprun.py
2. Run

USAGE
=====
python mprun.py -p 8 "cat {{INPUT}} | wc -l > temp/{{OUTPUT}}" *.txt

{{INPUT}}
Will be replaced with the files supplied one at a time to create the pool of jobs.

{{OUTPUT}}
Will be the *basename* of the {{INPUT}}-file with an added ".out"-ending.

VERSION HISTORY
===============

0.1.4   2016/05/01   pylint and pep8 cleaned
0.1.3   2016/02/18   Did not call aResults.get(), which led to premature end o program
0.1.2   2016/02/17   Better WARNINGS; stdout and strerr now possibl to capture
0.1.1   2016/02/17   Some improvements.
0.1.0   2016/02/17   Initial version.

LICENCE
=======
See supplied LICENCE file.

2016, copyright Sebastian Schmeier (s.schmeier@gmail.com), http://sschmeier.com
"""
from timeit import default_timer as timer
from multiprocessing import Pool
import sys
import os
import os.path
import argparse
import time
import subprocess
import re
__version__ = '0.1.4'
__date__ = '2016/05/01'
__email__ = 's.schmeier@gmail.com'
__author__ = 'Sebastian Schmeier'

def parse_cmdline():
    """ Parse command-line args. """
    ## parse cmd-line -----------------------------------------------------------
    description = 'Read delimited file.'
    version = 'version %s, date %s' % (__version__, __date__)
    epilog = 'Copyright %s (%s)' % (__author__, __email__)

    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('--version',
                        action='version',
                        version='%s' % (version))
    parser.add_argument(
        'command',
        metavar='CMD',
        type=str,
        help=
        'Command to execute on every {{INPUT}} file. Should contain one '+\
        '"{{INPUT}}" and one optional "{{OUTPUT}}" placeholder descriptor in '+\
        'the CMD, which are substituted with the filenames supplied, e.g. '+\
        '"cat {{INPUT}} | wc -l > temp/{{OUTPUT}}"')
    parser.add_argument('files_list',
                        nargs='+',
                        metavar='FILE',
                        type=str,
                        help='Files to use as {{INPUT}}.')
    parser.add_argument(
        '--stderr',
        type=str,
        metavar='PATH',
        dest='error_path',
        default=None,
        help=
        'Create a separate error file for each job in the directory at PATH.'+\
        ' [default: Do not create any error-files, stderr->dev/null]')
    parser.add_argument(
        '--stdout',
        type=str,
        metavar='PATH',
        dest='stdout_path',
        default=None,
        help=
        'Create a separate stdout-file for each job in the directory at PATH.'+\
        ' [default: Do not create any stdout-files, stdout->dev/null]')
    parser.add_argument(
        '--dry',
        action='store_true',
        dest='do_dryrun',
        default=False,
        help=
        'Only print created commands without runnig them. [default: False]')

    group1 = parser.add_argument_group('Multithreading', 'optional arguments:')
    group1.add_argument(
        '-p',
        '--processes',
        metavar='INT',
        type=int,
        dest='process_num',
        default=2,
        help=
        'Number of sub-processes (workers) to use. It is only logical to not'+\
        ' give more processes than cpus/cores are available. [default: 2]')
    group1.add_argument(
        '--no-pb',
        action='store_true',
        dest='hide_progress',
        default=False,
        help=
        'Turn the progress-bar off. A progress-bar will force a "chunksize"'+\
        ' of 1 in threading. This might slow things down for very large job'+\
        ' numbers, but allows for a realistic progress-bar. [default: Show'+\
        ' progress-bar -> chunksize = 1]')

    args = parser.parse_args()
    return args, parser


def run_command(args):
    """
    THIS IS THE ACCTUAL WORKHORSE FUNCTION THAT HAS TO BE EXECUTED MULTPLE TIMES.
    This function will be distributed to the processes as requested.
    # do stuff
    res = ...
    return (args, res)
    """
    command = args[1]  # command to execute
    err = args[2]  # stderr file
    out = args[3]  # stdout file

    if err:
        stderr_filehandle = open(err, 'w')
    else:
        # standard err to /dev/null
        stderr_filehandle = open(os.devnull, 'w')

    if out:
        stdout_filehandle = open(out, 'w')
    else:
        # standard out to /dev/null
        stdout_filehandle = open(os.devnull, 'w')

    returncode = subprocess.call(command,
                                 shell=True,
                                 stdout=stdout_filehandle,
                                 stderr=stderr_filehandle)
    stdout_filehandle.close()
    stderr_filehandle.close()
    # TEST:
    # check returncode for non-zero status
    if returncode != 0:
        sys.stderr.write(
            '[mprun WARNING]: *** Non-zero exit codes of child process'+\
            ' encountered. Better check with --stderr. ***\n')
    return (args, returncode)


def main():
    """ MAIN """
    args, parser = parse_cmdline()

    # TEST:
    # Supplied file list not empty
    if len(args.files_list) < 1:
        parser.error('You need to supply at least one file. EXIT.')
    files_list = []
    for filename in args.files_list:
        filename_path = os.path.abspath(os.path.expanduser(filename))
        # TEST:
        # Test that file exisits
        if os.path.isfile(filename_path):
            files_list.append(filename_path)
        else:
            parser.error('Input-file "%s" not found. EXIT.' % (filename))

    # Check that the CMD contains only one occurrence of {{INPUT}} and {{OUTPUT}}
    command = args.command
    res1 = re.findall('{{INPUT}}', command)
    res2 = re.findall('{{OUTPUT}}', command)

    # TEST:
    # Test that {{INPUT}} is given as it is required
    if len(res1) != 1:
        parser.error(
            'CMD should contain exactly one occurrence of an {{INPUT}} placeholder. EXIT.')
    # this is optional, give warning
    if len(res2) == 0:
        sys.stderr.write(
            '[mprun WARNING]: *** CMD does not contain a {{OUTPUT}} placeholder. ***\n')
    # TEST:
    # can not be more than one
    elif len(res2) > 1:
        parser.error(
            'CMD should contain at most one occurrence of an {{OUTPUT}} placeholder. EXIT.')

    # Stderr-file path
    error_path = None
    if args.error_path:
        # TEST:
        # Test if stderr-path exists
        if not os.path.isdir(args.error_path):
            sys.stderr.write(
                '[mprun WARNING]: *** The stderr-path "%s" does not exist.'+\
                ' Will be ignored and stderr -> dev/null ***\n'
                % args.error_path)
        else:
            error_path = os.path.abspath(os.path.expanduser(args.error_path))
            
    # Stdout-file path
    stdout_path = None
    if args.stdout_path:
        # TEST:
        # Test if stdout-path exists
        if not os.path.isdir(args.stdout_path):
            sys.stderr.write(
                '[mprun WARNING]: *** The stdout-path "%s" does not exist.'+\
                ' Will be ignored and stdout -> dev/null. ***\n'
                % args.stdout_path)
        else:
            stdout_path = os.path.abspath(os.path.expanduser(args.stdout_path))

    # ------------------------------------------------------
    #  THREADING
    # ------------------------------------------------------
    # get number of subprocesses to use
    process_num = args.process_num
    # TEST:
    # Number of processes cannot be smaller than 1.
    if process_num < 1:
        parser.error('-p has to be > 0: EXIT.')

    # FILL ARRAY WITH PARAMETER SETS TO PROCESS
    # this array contains all jobs that have to be run
    job_list = []
    job_num = 1
    # e.g. create jobs based on supplied command+files, here one file = one jobs
    for filename in files_list:
        # Create the command to execute
        command2 = command.replace('{{INPUT}}', filename)
        command2 = command2.replace('{{OUTPUT}}',
                                    os.path.basename(filename) + '.out')

        # create error-filename
        err = None
        if error_path:
            # create error-file path
            err = os.path.join(error_path,
                               '%s.stderr' % (os.path.basename(filename)))
        out = None
        if stdout_path:
            out = os.path.join(stdout_path,
                               '%s.stdout' % (os.path.basename(filename)))
        job_list.append((job_num, command2, err, out))
        job_num += 1

    # Number of total jobs
    jobs_total = len(job_list)
    out = '[mprun OK]: #JOBS TO RUN: %i | #CONCURRENT PROCESSES TO USE: %i\n'
    sys.stdout.write(out % (jobs_total, process_num))

    # Dry run?
    if args.do_dryrun:
        sys.stdout.write('[mprun WARNING]: *** DRY RUN: NOT PROCESSING ***\n')
        for row in job_list:
            sys.stdout.write('%s\n' % row[1])
        return

        # Timing
    start_time = timer()  # very crude

    # create pool of workers ---------------------
    pool = Pool(processes=process_num)

    # No prgress-bar requested.
    if args.hide_progress:
        results = pool.map_async(run_command, job_list)
    else:

        # "chunksize" usually only makes a noticeable performance
        # difference for very large iterables
        # Here, I set it to one to get the progress bar working nicly
        # Otherwise it will not give the correct number of processes left
        # but the chunksize number instead.
        chunksize = 1

        results = pool.map_async(run_command, job_list, chunksize=chunksize)

    # No more work to add to pool
    pool.close()

    # Progress-bar
    if not args.hide_progress:
        # Progress bar
        #==============================
        # This can be changed to make progress-bar bigger or smaller
        progress_bar_length = 50
        #==============================
        while not results.ready():
            jobs_not_done = results._number_left
            jobs_done = jobs_total - jobs_not_done
            bar_done = jobs_done * progress_bar_length / jobs_total
            bar_str = ('=' * bar_done).ljust(progress_bar_length)
            percent = int(jobs_done * 100 / jobs_total)
            sys.stdout.write("[mprun OK]: [%s] %s%%\r" \
                             %(bar_str, str(percent).rjust(3)))
            sys.stdout.flush()
            time.sleep(0.1)  # wait a bit: here we test all .1 secs
        # Finish the progress bar
        bar_str = '=' * progress_bar_length
        sys.stdout.write("[mprun OK]: [%s] 100%%\r\n" % (bar_str))

    # does actually not produce a result but returns exit/return-codes
    # however, need to call it otherwise program will not finish
    # all processes
    results = results.get()

    # --------------------------------------------
    end_time = timer()
    # Print the timing
    sys.stdout.write('[mprun OK]: RUNTIME(s): %.4f | AVG/JOB: %.4f\n' \
                     %(end_time - start_time, (end_time - start_time)/jobs_total))

    # collect all error return-codes
    returncode_list = [returntuple[1] for returntuple in results]
    if max(returncode_list) != 0:
        sys.stdout.write(
            '[mprun WARNING]: END OF PROGRAM. Non-zero error returncodes encountered\n')
    else:
        sys.stdout.write('[mprun OK]: END OF PROGRAM.\n')

    return


if __name__ == '__main__':
    sys.exit(main())
