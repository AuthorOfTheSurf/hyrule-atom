#! /usr/bin/env python
"""
Used to format the raw data text files produced by a BITalino
Parses the json-text format into a Python object more appropriate for
processing by the the MATL application

Sample BITalino txt file:

    # JSON Text File Format
    # {"SamplingResolution": "10", "SampledChannels": [1], "SamplingFrequency": "1000", "ColumnLabels": ["SeqN", "Digital0", "Digital1", "Digital2", "Digital3", "EMG"], "AcquiringDevice": "98:D3:31:XX:XX:XX", "Version": "111", "StartDateTime": "2015-02-12 19:37:46.727000"}
    # EndOfHeader
    0   1   1   1   1   467 
    1   1   1   1   1   467 
    2   1   1   1   1   472 
    3   1   1   1   1   476 
    4   1   1   1   1   478 
    ...

    Note that the StartDateTime field above is formatted in a non-default way.
    parser.py expects a StartDateTime field to be formatted as ISO with a space between
    the date and the time. This is done by changing line 241 of `code/writefile.py` to
    dict['StartDateTime'] = date.isoformat(" ")

"""

import sys
import json
import numpy

"""
BITalino data object, a plain old Python object
Accepts a BITalino .txt data file
- Header json into dict
- Parses colums into numpy arrays
"""
class BITdo:
    def __init__(self, BITalinoTxtData):
        next(BITalinoTxtData)
        self._header = self.makeHeader(next(BITalinoTxtData))
        next(BITalinoTxtData)
        self._channels = self.makeChannels(BITalinoTxtData)
    """
    BITalino header as a Python dict
        {
            "SamplingResolution": "10",
            "SampledChannels": [1],
            "SamplingFrequency": "1000",
            "ColumnLabels": ["SeqN", "Digital0", "Digital1", "Digital2", "Digital3", "EMG"],
            "AcquiringDevice": "98:D3:31:XX:XX:XX",
            "Version": "111",
            "StartDateTime": "2015-02-12 19:37:46.727000"
        }
    """
    @property
    def header(self):
        return self._header
    """
    List of the channels and their data
        [
            { "label": "Digital0", "data": [1, 1, 1] },
            ...
            { "label": "EMG", "data": [270, 551, 432] }
        ]
    """
    @property
    def channels(self):
        return self._channels
    """
    Parses the header, located on line two of the source file into a python dict
    """
    def makeHeader(self, headerLine):
        header = json.loads(headerLine[2:])
        if len(header["StartDateTime"]) != 26:
            raise AttributeError("BITalino source file does not have microsecond precision in \"StartDateTime\" field")
        elif header["SamplingFrequency"] != "1000":
            raise AttributeError("BITalino source data must be recorded at 1000hz, found %s" %header["SamplingFrequency"])
        return header
    """
    Parses the dataStream into and array of channel objects containing data and a label.
    See the description for BITdo.channels
    """
    def makeChannels(self, dataStream):
        labels = self._header["ColumnLabels"]
        # Each line has a trailing tab, newline, and carrage return. Datastream ends with a blank line
        fmtStream = [line[:-3].split("\t") for line in dataStream if len(line) > 0]
        na = numpy.array(fmtStream).astype(int)

        channels = {}
        for col, label in enumerate(labels):
            if label != "SeqN":
                channels[label] = na[:,col] # grab column col from 2d array na
        return channels
    """
    Return a JSON representation of this BITdo object
    """
    def toJson(self):
        channels = {}
        for key, value in self._channels.iteritems():
            channels[key] = value.tolist()
        return json.dumps({ "header": self._header, "channels": channels })

"""
Return a json representation of the supplied BITalino data .txt file
"""
def main():
    try:
        with open(sys.argv[1], "r") as bitsrc:
            data = BITdo(bitsrc)
            print data.toJson()
    except IndexError as e:
        print "Missing BITalino data file argument"

if __name__ == '__main__':
    main()
