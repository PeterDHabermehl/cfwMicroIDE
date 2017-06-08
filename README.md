# startIDE
An app to provide an onboard IDE for *very* simple projects (just switch outputs depending on an input...)

startIDE can be run on both ft TXT and community TX-Pi.

Some functionality is implemented: Robo family interfaces (Robo Interface, Robo I/O Extention, Robo LT controller and RF Data link) can be connected.
Digital Inputs can be evaluated on both TXT and Robo device, also Outputs and Motors can be accessed.

Encoder Motors connected to TXT also can be controlled (speed, direction and running distance (encoder steps))

Although it is pysically possible to connect more than one interface, startIDE will only address the first IF found.

When run on ft TXT controller, it is possible to use TXT and a connected Robo family device in parallel.

See [ddoc/FunctionList.ods](ddoc/FunctionList.ods) for a list of functions implemented/planned.
