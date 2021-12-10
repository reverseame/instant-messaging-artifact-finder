# Instant Messaging Artifact Finder

*Instant Messaging Artifact Finder* (abbreviated as *IM Artifact Finder*) is a tool to find memory artifacts present in
instant messaging (IM) applications. It has been designed as a framework, so that it can be extended to support other IM
applications.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Installation

At the moment, the tool can be used as a command line tool. To do that, you can either clone the contents of this
repository or download the code. Additionally, in order for the tool to
work, [Python 3](https://www.python.org/downloads/) has to be installed on the machine where the tool is going to be
used.

## Usage

In order to use the tool from the command line to extract the artifacts from a memory dump of the *Telegram Desktop*
process (generated with [*Windows Memory Extractor*](https://github.com/reverseame/windows-memory-extractor)), execute
the following command, where *memory_data_path* is the directory where the raw memory data files (*.dmp* files) are
stored:

```bash
python3 finder.py memory_data_path TELEGRAM_DESKTOP
```

By default, the tool generates a full report in JSON format and a text file with a summary of the artifacts found. The
report format can be specified as an optional command line argument, as shown in the command below. However, right now,
only the JSON format is supported.

```bash
python3 finder.py memory_data_path TELEGRAM_DESKTOP --format JSON
```

Additionally, a temporary directory can be indicated. When supplied, the contents of the original memory data directory
are copied into that directory. After that, the tool works only with the contents present in the temporary directory.
Finally, the temporary directory is removed. This can be useful for performance reasons if, for example, the temporary
directory is in a RAM disk. Here is an example of how to supply a temporary directory:

```bash
python3 finder.py memory_data_path TELEGRAM_DESKTOP --tmp temporary_directory_path
```

**Note:** In the command above, the temporary directory must not exist.

Lastly, for additional help, run the following command:

```bash
python3 finder.py --help
```

## Support a New IM Application

The memory artifacts found by the tool are modeled as objects. In order to support the common elements that IM
applications have, like conversations or messages, the designed object model is generic, defining a set of abstract
classes to represent the common elements present in IM applications. To introduce support for a particular IM
application, a set of concrete classes that extend the abstract classes has to be created. These concrete classes lack
behavior, since it is not needed in this case, they instead have a set of attributes to store the information found in
the memory dump. Each concrete class, in addition to storing data, has the responsibility of representing itself in each
supported report format, since all of them have to implement the representation methods defined in the *Artifact*
interface.

Two design patterns have been used in this framework: the *Strategy* pattern and the *Abstract Factory* pattern. The
*Strategy* design pattern is used to define a family of algorithms, encapsulate each one, and make them interchangeable.
This pattern has been used in the report creation feature, where there is a different strategy to create a report for
each supported format, which facilitates adding new report formats.

In order to obtain objects that represent memory artifacts, four interfaces have been defined: (i) *ArtifactExtractor*,
the first step is to extract the raw data corresponding to the artifacts from a memory dump, using pattern matching;
(ii) *ArtifactAnalyzer*, once the raw data is extracted, it has to be interpreted and analyzed; (iii)
*ArtifactOrganizer*, before creating the objects, it might be necessary to organize the data acquired after the analysis
phase; and (iv) *InstantMessagingPlatformFactory*, once the information about the artifacts has been extracted,
analyzed, and organized, objects representing those artifacts can be created. In this way, each interface deals with a
different phase, and, as a consequence, there is a separation of concerns.

An important aspect to take into account is that implementations of the four interfaces previously mentioned work
together, therefore, they have to correspond to the same IM platform. To avoid, for instance, using the extraction
technique corresponding to an IM platform and the analysis technique that corresponds to another, the *Abstract Factory*
design pattern has been used. The *Abstract Factory* pattern is used to provide an interface for creating families of
related or dependent objects without specifying their concrete classes. In the particular case of this framework, that
interface is *InstantMessagingPlatformFactory*. The classes that implement that interface are known as factories, and
their responsibility is to create objects. For each supported IM platform, its own factory has to exist. Depending on
the IM platform to which the memory dump under analysis corresponds, one factory or another will be created. After that,
in order to create objects related to the IM platform, the creation methods of its factory will have to be called.

With the aforementioned design, the framework does not have to know the details of each IM application, since it depends
on interfaces, and the details of each IM application will have to be handled in the implementations of those
interfaces. To introduce support for a new IM application, the *ArtifactExtractor*, *ArtifactAnalyzer*,
*ArtifactOrganizer*, and *InstantMessagingPlatformFactory* interfaces will have to be implemented, and the abstract
classes representing general artifacts will have to be extended.

## License

GNU General Public License v3.0