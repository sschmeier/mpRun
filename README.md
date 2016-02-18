# mpRun

## DESCRIPTION
Simple script that takes a command-line command (`CMD`) that contains one INPUT-file placeholder and one optional OUTPUT-placeholder and runs the `CMD` on a set of user supplied input-files. Each input-file represents a job and  jobs are run in as many concurrent processes as requested.

## INSTALLATION
1. Download or clone the repo
2. Simply move `mpRun.py` file into the directory where you want to use
   it. Alternatively,  you can make it executable `chmod x+a mpRun.py` and move
   it into a directory on your `PATH`, e.g. `mv mpRun.py ~/bin` or create a
   symbolic link, .e.g. `ln -s ${PWD}/mpRun.py ~/bin/mpRun.py`.

## REQUIREMENTS
Python

## USAGE
The program expects a command that has one input `{{INPUT}}` and at most one output `{{OUTPUT}}`. The `{{INPUT}}` needs to be specified in order for the program to execute. The `{{OUTPUT}}` in the command is optional.

### `{{INPUT}}`
Will be replaced with the files supplied one at a time to create the pool of jobs.

### `{{OUTPUT}}`
Will be the *basename* of the `{{INPUT}}`-file with an added ".out"-ending.

### EXAMPLES

```bash
# Rather stupid examples
$ python mpRun.py "gzip {{INPUT}}" *.fa -p 8

# Here it is your responsibility to make sure that temp/ exists, otherwise
# the program will run but without --stderr no error message is printed, even
# though no output is produced.
$ python mpRun.py -p 16 'cat {{INPUT}} | grep "ACGT" | wc -l > temp/{{OUTPUT}}' *.txt
```

```bash
usage: mpRun.py [-h] [--stderr PATH] [--stdout PATH] [-p INT] [--no-pb]
                CMD FILE [FILE ...]

Take a CMD that contains one INPUT-file placeholder and one optional OUTPUT-
placeholder and run the CMD on a set of files via multiple processes
simultaneously.

positional arguments:
  CMD                   Command to execute on every {{INPUT}} file. Should
                        contain one "{{INPUT}}" and one optional "{{OUTPUT}}"
                        placeholder descriptor in the CMD, which are
                        substituted with the filenames supplied, e.g. "cat
                        {{INPUT}} | wc -l > temp/{{OUTPUT}}"
  FILE                  Files to use as {{INPUT}}.

optional arguments:
  -h, --help            show this help message and exit
  --stderr PATH         Create a separate error file for each job in the
                        directory at PATH. [default: Do not create any error-
                        files, stderr->dev/null]
  --stdout PATH         Create a separate stdout-file for each job in the
                        directory at PATH. [default: Do not create any stdout-
                        files, stdout->dev/null]

Multithreading:
  optional arguments:

  -p INT, --processes INT
                        Number of sub-processes (workers) to use. It is only
                        logical to not give more processes than cpus/cores are
                        available. [default: 2]
  --no-pb               Turn the progress-bar off. A progress-bar will force a
                        "chunksize" of 1 for the threading. This might slow
                        things down for very large job numbers, but allows for
                        a realistic progress-bar. [default: Show progress-bar]

Copyright Sebastian Schmeier (s.schmeier@gmail.com)
