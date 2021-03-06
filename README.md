# mc-sdf-1
MineCraft Structure Definition Format (rev 1).

Status: Pre-alpha

# Overview #

Right now most people share their MineCraft creations by zipping up their world file and making it available somewhere. These files are many megabytes in size, containing much more information than just the structure the author wanted to share.

The purpose of this project is to provide an alternative to this by defining an open interchange format that represents these structures in a compact and portable way.

While it is mostly meant for use with MineCraft, it should be usable with similar "block" games too.

# Structure #

This project is arranged into three separate areas:

1. code - miscellaneous tools and reference implementations of parsers
2. examples - demonstrations of the file format using real samples
3. spec - the specification itself
