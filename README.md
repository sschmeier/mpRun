# mpRun

## DESCRIPTION
Simple script that takes a command-line command (`CMD`) that contains one INPUT-file placeholder and one optional OUTPUT-placeholder and runs the `CMD` on a set of user supplied input-files. Each input-file represents a job and  jobs are run in as many concurrent processes as requested.

## INSTALLATION
1. Download or clone the repo
2. Either put the `mpRun.py` file into the directory where you want to use it or make it executable `chmod x+a mpRun.py` and put it in a directory on your PATH.

## REQUIREMENTS
None

## USAGE
The program expects a command that has one input (`{{INPUT}}`) and at most one output (`{{OUTPUT}}`). The {{INPUT}} needs to be specified in order for the program to execute. The `{{OUTPUT}}` in the command is optional.

`{{INPUT}}`
Will be replaced with the files supplied one at a time to create the pool of jobs.

`{{OUTPUT}}`
Will be the *basename* of the `{{INPUT}}`-file with an added ".out"-ending.


```bash
$ python mpRun.py -p 16 'cat {{INPUT}} | grep "ACGT" | wc -l > temp/{{OUTPUT}}' *.txt
```
