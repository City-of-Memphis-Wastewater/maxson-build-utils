## Does maxson-build-utils offer healing?

No. Opinionated MBU files can be stood up individually in a project.
If a file at that path already exists, a warning will be printed.
If not, it will be built.
Want verison healing?
Delete the existing version, then stand up the newest version of any scaffolded file, via the mbu CLI.
Check the existing version to make sure you are losing any local custom changes.


