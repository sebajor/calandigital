"""
Main calandigital script with helper functions.
"""
import sys, time, imp
import corr
import numpy as np

def initialize_roach(ip, port=7147, boffile=None, roach_version=2):
    """
    Initializes ROACH, that is, start ROACH communication, program boffile
    into the FPGA, and creates the FpgaClient object to communicate with.
    :param ip: ROACH IP address.
    :param port: ROCH TCP/IP port for communication.
    :param boffile: .bof file to program the FPGA. If None porgramming 
        is skipped.
    :param roach_version: version of the ROACH, 1 and 2 supported.
    :return: FpgaClient object to communicate with ROACH's FPGA.
    """
    print("Initializing ROACH communication...")
    roach = corr.katcp_wrapper.FpgaClient(ip, port)
    time.sleep(0.1)
    if not roach.is_connected():
        print("Unable to connect to ROACH :/")
        print("Possible causes:")
        print("\t1. ROACH wasn't ready to connect yet")
        print("\t2. Incorrect IP")
        print("\t3. ROACH not connected to the network")
        exit()
    print("done")

    if boffile is not None:
        print("Programming boffile into ROACH...")
        if roach_version is 1:
            print("\tUsing ROACH1, programming from ROACH internal memory...")
            roach.progdev(boffile)
            time.sleep(1)
        elif roach_version is 2:
            print("\tUsing ROACH2, programming from PC memory...")
            roach.upload_program_bof(boffile, 60000)
            time.sleep(1)
        else:
            print("ROACH version not supported.")
            exit()
        print("done")
    else:
        print("Skipping programming boffile.")

    print("Estimating FPGA clock frequency...")
    try:
        fpga_clock = roach.est_brd_clk()
    except RuntimeError:
        print("Unable to estimate frequency :/")
        print("Possible causes:")
        print("\t1. no .bof file programmed in FPGA")
        print("\t2. .bof not found in ROACH internal memory (ROACH1)")
        print("\t3. .bof not in not in the same directory as the script (ROACH2)")
        exit()
    print("done. Estimated clock: " + str(fpga_clock))

    return roach

def read_snapshots(roach, snapshots, dtype='>i1'):
    """
    Reads snapshot data from a list of snapshots names.
    :param roach: CalanFpga object to communicate with ROACH.
    :param snapshots: list of snapshot names to read.
    :param dtype: data type of data in snapshot. Must be Numpy compatible.
        My prefered format:
            (<, >):    little endian, big endian
            (i, u):    signed, unsigned
            (1,2,...): number of bytes
            e.g.: >i1: one byte, signed, big-endian
    :return: list of data arrays in the same order as the snapshot list. 
        Note: the data type is fixed to 8 bits as all of our ADC work at 
        that size. 
    """
    snapdata_list = []
    for snapshot in snapshots:
        rawdata  = roach.snapshot_get(snapshot, man_trig=True, man_valid=True)['data']
        snapdata = np.fromstring(rawdata, dtype=dtype)
        snapdata_list.append(snapdata)
    
    return snapdata_list

def read_interleave_data(roach, brams, awidth, dwidth, dtype):
    """
    Reads data from a list of brams and interleave the data in order to return 
    in correctly ordered (as per typical spectrometer models in ROACH).
    :param brams: list of bram list to read and interleave.
    :param awidth: width of bram address in bits.
    :param dwidth: width of bram data in bits.
    :param data_type: data type of data in brams. See read_snapshots().
    :return: array with the read data.
    """
    depth = 2**awidth
    bramdata_list = []

    # get data
    for bram in brams:
        rawdata  = roach.read(bram, depth*dwidth/8, 0)
        bramdata = np.frombuffer(rawdata, dtype=dtype)
        bramdata = bramdata.astype(np.float)
        bramdata_list.append(bramdata)

    # interleave data list into a single array (this works, believe me)
    interleaved_data = np.vstack(bramdata_list).reshape((-1,), order='F')

    return interleaved_data

def scale_and_dBFS_specdata(data, acclen, nbits, nchannels):
        """
        Scales spectral data by an accumulation length, and converts
        the data to dBFS. Used for plotting spectra.
        :param data: spectral data to convert. Must be Numpy array.
        :param acclen: accumulation length of spectrometer. 
            Used to scale the data.
        :param nbits: number of bits used to sample the data (ADC bits).
        :param nchannels: number of channels of the spectrometer.
        :return: scaled data in dBFS.
        """
        # scale data 
        data = data / acclen

        # convert data to dBFS
        dBFS = 6.02*nbits + 1.76 + 10*np.log10(nchannels)
        data = 10*np.log10(data+1) - dBFS

        return data
