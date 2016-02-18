#!/usr/bin/env python
"""
NAME: mpRun.py
==============

DESCRIPTION
===========
Take a CMD that requires one INPUT and one OUTPUT files and run
the CMD on a set of files via multiple processes simultaneously.

INSTALLATION
============
1. Download mpRun.py
2. Run

USAGE
=====
python mpRun.py -p 8 "cat {{INPUT}} | wc -l > temp/{{OUTPUT}}" *.txt

{{INPUT}}
Will be replaced with the files supplied one at a time to create the pool of jobs.

{{OUTPUT}}
Will be the *basename* of the {{INPUT}}-file with an added ".out"-ending.

VERSION HISTORY
===============

0.1.2   2016/02.17   Better WARNINGS; stdout and strerr now possibl to capture
0.1.1   2016/02/17   Some improvements.
0.1.0   2016/02/17   Initial version.

LICENCE
=======
See supplied LICENCE file.

2016, copyright Sebastian Schmeier (s.schmeier@gmail.com), http://sschmeier.com
"""
__version__='0.1.2'
__date__='2016/02/17'
__email__='s.schmeier@gmail.com'
__author__='Sebastian Schmeier'
import sys, os, os.path, argparse, time, subprocess, re
from timeit import default_timer as timer
from multiprocessing import Pool

def parse_cmdline():
    ## parse cmd-line -----------------------------------------------------------
    sDescription = 'Take a CMD that contains one INPUT-file placeholder and one optional OUTPUT-placeholder and run the CMD on a set of files via multiple processes simultaneously.'
    sVersion='version %s, date %s' %(__version__,__date__)
    sEpilog = 'Copyright %s (%s)' %(__author__, __email__)

    oParser = argparse.ArgumentParser(description=sDescription,
                                      #version=sVersion,  # does not work in Python 3
                                      epilog=sEpilog)
    oParser.add_argument('sCMD',
                         metavar='CMD',
                         type=str,
                         help='Command to execute on every {{INPUT}} file. Should contain one "{{INPUT}}" and one optional "{{OUTPUT}}" placeholder descriptor in the CMD, which are substituted with the filenames supplied, e.g. "cat {{INPUT}} | wc -l > temp/{{OUTPUT}}"')
    oParser.add_argument('aFiles',
                         nargs='+',
                         metavar='FILE',
                         type=str,
                         help='Files to use as {{INPUT}}.')
    oParser.add_argument('--stderr',
                         type=str,
                         metavar='PATH',
                         dest='sErrorPath',
                         default=None,
                         help='Create a separate error file for each job in the directory at PATH. [default: Do not create any error-files, stderr->dev/null]')
    oParser.add_argument('--stdout',
                         type=str,
                         metavar='PATH',
                         dest='sStdoutPath',
                         default=None,
                         help='Create a separate stdout-file for each job in the directory at PATH. [default: Do not create any stdout-files, stdout->dev/null]')
    oParser.add_argument('--dry',
                         action='store_true',
                         dest='bDry',
                         default=False,
                         help='Only print created commands without runnig them. [default: False]')

    group1 = oParser.add_argument_group('Multithreading', 'optional arguments:')
    group1.add_argument('-p', '--processes',
                         metavar='INT',
                         type=int,
                         dest='iP',
                         default=2,
                         help='Number of sub-processes (workers) to use. It is only logical to not give more processes than cpus/cores are available. [default: 2]')
    group1.add_argument('--no-pb',
                         action='store_true',
                         dest='bNoProgress',
                         default=False,
                         help='Turn the progress-bar off. A progress-bar will force a "chunksize" of 1 in threading. This might slow things down for very large job numbers, but allows for a realistic progress-bar. [default: Show progress-bar -> chunksize = 1]')

    oArgs = oParser.parse_args()
    return oArgs, oParser

def run_command(args):
    """
    THIS IS THE ACCTUAL WORKHORSE FUNCTION THAT HAS TO BE EXECUTED MULTPLE TIMES.
    This function will be distributed to the processes as requested.
    # do stuff
    res = ...
    return (args, res)
    """
    sJob = str(args[0])  # job number, not used
    sCMD = args[1]  # command to execute
    sERR = args[2]  # stderr file
    sOUT = args[3]  # stdout file

    if sERR:
        oFstderr = open(sERR, 'w')
    else:
        # standard err to /dev/null
        oFstderr = open(os.devnull, 'w')

    if sOUT:
        oFstdout = open(sOUT, 'w')
    else:
        # standard out to /dev/null
        oFstdout = open(os.devnull, 'w')

    iReturncode = subprocess.call(sCMD, shell=True, stdout=oFstdout, stderr=oFstderr)
    oFstdout.close()
    oFstderr.close()
    # TEST:
    # check returncode for non-zero status
    if iReturncode != 0:
        sys.stderr.write('[mpRun WARNING]: *** Non-zero exit codes of child process encountered. Better check with --stderr. ***\n')
    return (args, iReturncode)

def main():
    oArgs, oParser = parse_cmdline()

    # TEST:
    # Supplied file list not empty
    if len(oArgs.aFiles)<1:
        oParser.error('You need to supply at least one file. EXIT.')
    aFiles = []
    for sFile in oArgs.aFiles:
        sF = os.path.abspath(os.path.expanduser(sFile))
        # TEST:
        # Test that file exisits
        if os.path.isfile(sF):
            aFiles.append(sF)
        else:
            oParser.error('Input-file "%s" not found. EXIT.' %(sFile))

    # Check that the CMD contains only one occurrence of {{INPUT}} and {{OUTPUT}}
    sCMD = oArgs.sCMD
    aRes1 = re.findall('{{INPUT}}', sCMD)
    aRes2 = re.findall('{{OUTPUT}}', sCMD)

    # TEST:
    # Test that {{INPUT}} is given as it is required
    if len(aRes1) != 1:
        oParser.error('CMD should contain exactly one occurrence of an {{INPUT}} placeholder. EXIT.')
    # this is optional, give warning
    if len(aRes2) == 0:
        sys.stderr.write('[mpRun WARNING]: *** CMD does not contain a {{OUTPUT}} placeholder. ***\n')
    # TEST:
    # can not be more than one
    elif len(aRes2) > 1:
        oParser.error('CMD should contain at most one occurrence of an {{OUTPUT}} placeholder. EXIT.')

    # Stderr-file path
    sErrPath = None
    if oArgs.sErrorPath:
        # TEST:
        # Test if stderr-path exists
        if not os.path.isdir(oArgs.sErrorPath):
            sys.stderr.write('[mpRun WARNING]: *** The stderr-path "%s" does not exist. Will be ignored and stderr -> dev/null ***\n'%oArgs.sErrorPath)
        else:
            sErrPath = os.path.abspath(os.path.expanduser(oArgs.sErrorPath))
    # Stdout-file path
    sStdoutPath = None
    if oArgs.sStdoutPath:
        # TEST:
        # Test if stdout-path exists
        if not os.path.isdir(oArgs.sStdoutPath):
            sys.stderr.write('[mpRun WARNING]: *** The stdout-path "%s" does not exist. Will be ignored and stdout -> dev/null. ***\n'%oArgs.sStdoutPath)
        else:
            sStdoutPath = os.path.abspath(os.path.expanduser(oArgs.sStdoutPath))

    # ------------------------------------------------------
    #  THREADING
    # ------------------------------------------------------
    # get number of subprocesses to use
    iNofProcesses = oArgs.iP
    # TEST:
    # Number of processes cannot be smaller than 1.
    if iNofProcesses<1:
        oParser.error('-p has to be > 0: EXIT.')

    # FILL ARRAY WITH PARAMETER SETS TO PROCESS
    # this array contains all jobs that have to be run
    aJobs = []
    iJob = 1
    # e.g. create jobs based on supplied command+files, here one file = one jobs
    for sFile in aFiles:
        # Create the command to execute
        sCMD2 = sCMD.replace('{{INPUT}}', sFile)
        sCMD2 = sCMD2.replace('{{OUTPUT}}', os.path.basename(sFile)+'.out')

        # create error-filename
        sERR = None
        if sErrPath:
            # create error-file path
            sERR = os.path.join(sErrPath ,'%s.stderr'%(os.path.basename(sFile)))
        sOUT = None
        if sStdoutPath:
            sOUT = os.path.join(sStdoutPath ,'%s.stdout'%(os.path.basename(sFile)))
        aJobs.append((iJob, sCMD2, sERR, sOUT))
        iJob+=1

    
    # Number of total jobs
    iNumJobs = len(aJobs)
    sOUT = '[mpRun OK]: #JOBS TO RUN: %i | #CONCURRENT PROCESSES TO USE: %i\n'
    sys.stdout.write(sOUT%(iNumJobs, iNofProcesses))

    # Dry run?
    if oArgs.bDry:
        sys.stdout.write('[mpRun WARNING]: *** DRY RUN: NOT PROCESSING ***\n')
        for a in aJobs:
            sys.stdout.write('%s\n'%a[1])
        return
            
    # Timing
    fStart_time = timer()  # very crude

    # create pool of workers ---------------------
    pool = Pool(processes=iNofProcesses)

    # No prgress-bar requested.
    if oArgs.bNoProgress:
        aResults = pool.map_async(run_command, aJobs)
    else:
        #====================================================================
        # "chunksize" usually only makes a noticeable performance
        # difference for very large iterables
        # Here, I set it to one to get the progress bar working nicly
        # Otherwise it will not give the correct number of processes left
        # but the chunksize number instead.
        chunksize = 1
        #====================================================================
        aResults = pool.map_async(run_command, aJobs, chunksize=chunksize)

    # No more work to add to pool
    pool.close()

    # Progress-bar
    if not oArgs.bNoProgress:
        # Progress bar
        #==============================
        # This can be changed to make progress-bar bigger or smaller
        iProgressBarLength = 50
        #==============================
        while not aResults.ready():
            iNumNotDone = aResults._number_left
            iNumDone = iNumJobs-iNumNotDone
            iBarDone = iNumDone*iProgressBarLength/iNumJobs
            sBar = ('=' * iBarDone).ljust(iProgressBarLength)
            iPercent = int(iNumDone*100/iNumJobs)
            sys.stdout.write("[mpRun OK]: [%s] %s%%\r" \
                             %(sBar, str(iPercent).rjust(3)))
            sys.stdout.flush()
            time.sleep(0.1)  # wait a bit: here we test all .1 secs
        # Finish the progress bar
        sBar = '=' * iProgressBarLength
        sys.stdout.write("[mpRun OK]: [%s] 100%%\r\n"%(sBar))

    # does actually not produce a result but returns exit/return-codes
    # however, need to call it otherwise program will not finish
    # all processes
    aResults = aResults.get()
    
    # --------------------------------------------
    fEnd_time = timer()
    # Print the timing
    sys.stdout.write('[mpRun OK]: RUNTIME(s): %.4f | AVG/JOB: %.4f\n' \
                     %(fEnd_time - fStart_time, (fEnd_time - fStart_time)/iNumJobs))

    # collect all error return-codes
    aReturncodes = [t[1] for t in aResults]
    if max(aReturncodes) != 0:
          sys.stderr.write('[mpRun WARNING]: *** Non-zero exit codes of some child process encountered. Better check with --stderr. ***\n')

    sys.stdout.write('[mpRun OK]: END\n')
                     
    return

if __name__ == '__main__':
    sys.exit(main())
