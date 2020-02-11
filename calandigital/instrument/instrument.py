import vxi11

class Instrument():
    """
    Wrapper around vxi11 Instrument to support simulated instruments.
    """
    def __init__(self, *args):
        if not args or args[0] is None:
            self.simulated = True
            self.vxi11Instrument = None
        else:
            self.simulated = False
            self.vxi11Instrument = vxi11.Instrument(*args)

    def __getattr__(self, name):
        """
        Excecute instrument method if it is real, else do nothing.
        """
        def method(*args):
            if self.simulated:
                return
            else:
                getattr(self.vxi11Instrument, name)(*args)

        return method
            
    def __repr__(self):
        """
        Avoid printing error.
        """
        return self.vxi11Instrument.__repr__()
