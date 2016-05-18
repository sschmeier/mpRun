# mprun

## DESCRIPTION
Simple script that takes a command-line command (`CMD`) that contains one INPUT-file placeholder and one optional OUTPUT-placeholder and runs the `CMD` on a set of user supplied input-files. Each input-file represents a job and  jobs are run in as many concurrent processes as requested.

## INSTALLATION
1. Download or clone the repo
2. Simply move `mprun.py` file into the directory where you want to use
   it. Alternatively,  you can run `/bin/bash bootstrap.sh` to make file 
   executable and rsync it to ~/bin

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
$ python mprun.py "gzip {{INPUT}}" *.fa -p 8

# Here it is your responsibility to make sure that temp/ exists, otherwise
# the program will run but without --stderr no error message is printed, even
# though no output is produced.
$ python mprun.py -p 16 'cat {{INPUT}} | grep "ACGT" | wc -l > temp/{{OUTPUT}}' *.txt
```
