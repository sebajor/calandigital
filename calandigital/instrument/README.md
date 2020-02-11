Instrument class that uses the [vxi11 package](https://github.com/python-ivi/python-vxi11) and add the functionality of simulating an instrument. To create an instrument object, simply use:

- real instrument: `instrument = cd.Instrument(<IP>)`, or 
- simulated instrument: `cd.Instrument()`,

and then use it the same as a vxi11 Instrument.
