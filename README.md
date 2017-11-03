# startIDE
An app to provide an onboard IDE for *very* simple projects (just switch outputs depending on an input...)

startIDE can be run on both ft TXT and community TX-Pi.

![Main window](ddoc/screenshots/startIDE01.png)

Some functionality is implemented: Robo family interfaces (Robo Interface, Robo I/O Extention, Robo LT controller and RF Data link) can be connected.
Digital Inputs can be evaluated on both TXT and Robo device, also Outputs and Motors can be accessed.

![Add function](ddoc/screenshots/startIDE02.png)

Encoder Motors connected to TXT also can be controlled (speed, direction and running distance (encoder steps))

![Motor control](ddoc/screenshots/startIDE03.png)

Although it is pysically possible to connect more than one interface, startIDE will only address the first IF found.

When run on ft TXT controller, it is possible to use TXT and a connected Robo family device in parallel.

A german user guide (Handbuch) is available: [ddoc/Manual_060_de.pdf](ddoc/Manual_060_de.pdf)

See [ddoc/FunctionList.ods](ddoc/FunctionList.ods) for a list of functions implemented/planned.
