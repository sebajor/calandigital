"""
Main calandigital script with helper functions.
"""
import time
import corr
import numpy as np
from dummy_roach.dummy_roach import DummyRoach

def initialize_roach(ip, port=7147, boffile=None, upload=False, timeout=10.0):
    """
    Initializes ROACH, that is, start ROACH communication, program boffile
    into the FPGA, and creates the FpgaClient object to communicate with.
    :param ip: ROACH IP address. If None use dummy roach.
    :param port: ROACH TCP/IP port for communication.
    :param boffile: .bof file to program the FPGA. If None porgramming 
        is skipped.
    :param upload: If true upload .bof file from PC into ROACH volatile 
        memory. Supported for ROACH2 only.
    :param timeout: time to wait before thorwing a timeout exception while
        communicating with roach. Use longer times when extracting large
        amounts of data (e.g. from DRAM).
    :return: FpgaClient object to communicate with ROACH's FPGA.
    """
    print("Initializing ROACH communication...")
    if ip is None:
        print("Using dummy ROACH...")
        roach = DummyRoach(ip)

    else:
        roach = corr.katcp_wrapper.FpgaClient(ip, port, timeout=timeout)
    
    time.sleep(0.5)
    if not roach.is_connected():
        print("Unable to connect to ROACH :/")
        print("Possible causes:")
        print("\t1. ROACH wasn't ready to connect yet")
        print("\t2. Incorrect IP")
        print("\t3. ROACH not connected to the network")
        exit()
    print("done")

    if boffile is not None:
        print("Programming boffile " + boffile + " into ROACH...")
        if not upload:
            print("\tProgramming ROACH from internal memory...")
            roach.progdev(boffile)
            time.sleep(1)
        else: # upload
            print("\tProgramming ROACH from PC memory...")
            roach.upload_program_bof(boffile, 60000)
            time.sleep(1)
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

def read_data(roach, bram, awidth, dwidth, dtype):
    """
    Reads data from a bram in roach.
    :param roach: CalanFpga object to communicate with ROACH.
    :param bram: bram name.
    :param awidth: width of bram address in bits.
    :param dwidth: width of bram data in bits.
    :param dtype: data type of data in bram. See read_snapshots().
    :return: array with the read data.
    """
    depth = 2**awidth
    rawdata  = roach.read(bram, depth*dwidth/8, 0)
    bramdata = np.frombuffer(rawdata, dtype=dtype)
    bramdata = bramdata.astype(np.float)

    return bramdata

def read_interleave_data(roach, brams, awidth, dwidth, dtype):
    """
    Reads data from a list of brams and interleave the data in order to return 
    in correctly ordered (as per typical spectrometer models in ROACH).
    :param roach: CalanFpga object to communicate with ROACH.
    :param brams: list of brams to read and interleave.
    :param awidth: width of bram address in bits.
    :param dwidth: width of bram data in bits.
    :param dtype: data type of data in brams. See read_snapshots().
    :return: array with the read data.
    """
    # get data
    bramdata_list = []
    for bram in brams:
        bramdata = read_data(roach, bram, awidth, dwidth, dtype)
        bramdata_list.append(bramdata)

    # interleave data list into a single array (this works, believe me)
    interleaved_data = np.vstack(bramdata_list).reshape((-1,), order='F')

    return interleaved_data

def read_deinterleave_data(roach, bram, dfactor, awidth, dwidth, dtype):
    """
    Reads data from a bram and deinterleave the data into a dfactor number of 
    separate data arrays. Assumes that lendata % dfactor = 0.
    Useful when independent spectral data is saved in the same bram in an 
    interleaved manner.
    :param roach: CalanFpga object to communicate with ROACH.
    :param bram: bram name to read.
    :param dfactor: deinterleave factor. The number of arrays in which to
        deinterleave the data.
    :param awidth: width of bram address in bits.
    :param dwidth: width of bram data in bits.
    :param dtype: data type of data in bram. See read_snapshots().
    :return: list with the deinterleaved data arrays.
    """
    # get data
    bramdata = read_data(roach, bram, awidth, dwidth, dtype)

    lendata  = len(bramdata)
    newshape = (lendata/dfactor, dfactor)
    # deinterleave data into dfactor arrays (this works, believe me)
    bramdata_list = list(np.transpose(np.reshape(bramdata, newshape)))

    return bramdata_list

def write_interleaved_data(roach, brams, data):
    """
    Deinterleaves an array of interleaved data, and writes each deinterleaved
    array into a bram of a list of brams.
    :param roach: CalanFpga object to communicate with ROACH.
    :param brams: list of brams to write into.
    :param data: array of data to write. (Every Numpy type is accepted but the
        data converted into bytes before is written).
    """
    ndata  = len(data)
    nbrams = len(brams)

    # deinterleave data into arrays (this works, believe me)
    bramdata_list = np.transpose(np.reshape(data, (ndata/nbrams, nbrams)))
    
    # write data into brams
    for bram, bramdata in zip(brams, bramdata_list):
        roach.write(bram, bramdata.tobytes(), 0)

def read_dram_data(roach, awidth, dwidth, dtype):
    """
    Reads data from a dram in roach.
    :param roach: CalanFpga object to communicate with ROACH.
    :param awidth: width of dram address in bits.
    :param dwidth: width of dram data in bits.
    :param dtype: data type of data in dram. See read_snapshots().
    :return: array with the read data.
    """
    depth = 2**awidth
    rawdata  = roach.read_dram(depth*dwidth/8, 0)
    dramdata = np.frombuffer(rawdata, dtype=dtype)
    dramdata = dramdata.astype(np.float)

    return dramdata

def scale_and_dBFS_specdata(data, acclen, dBFS):
    """
    Scales spectral data by an accumulation length, and converts
    the data to dBFS. Used for plotting spectra.
    :param data: spectral data to convert. Must be Numpy array.
    :param acclen: accumulation length of spectrometer. 
        Used to scale the data.
    :param dBFS: amount to shift the dB data is shifted in order
        to converted it to dBFS. It is usually computed as: 
        dBFS = 6.02 adc_bits + 10*log10(spec_channels)
    :return: scaled data in dBFS.
    """
    # scale data 
    data = data / float(acclen)

    # convert data to dBFS
    data = 10*np.log10(data+1) - dBFS

    return data

def float2fixed(data, nbits, binpt, signed=True, warn=False):
    """
    Convert an array of floating points to fixed points, with width number of
    bits nbits, and binary point binpt. Optional warinings can be printed
    to check for overflow in conversion.
    :param data: data to convert.
    :param nbits: number of bits of the fixed point format.
    :param binpt: binary point of the fixed point format.
    :param signed: if true use signed representation, else use unsigned.
    :param warn: if true print overflow warinings.
    :return: data in fixed point format.
    """
    if warn:
        check_overflow(data, nbits, binpt, signed)

    nbytes = int(np.ceil(nbits/8))
    dtype = '>i'+str(nbytes) if signed else '>u'+str(nbytes)

    fixedpoint_data = (2**binpt * data).astype(dtype)
    return fixedpoint_data

def check_overflow(data, nbits, binpt, signed):
    """
    Check if the values of an array exceed the limit values given by a 
    fixed point representation, and print a warining if that is the case.
    :param data: data to check.
    :param nbits: number of bits of the fixed point format.
    :param binpt: binary point of the fixed point format.
    :param signed: if true use signed representation, else use unsigned.
    """
    # limit values of fixed point
    max_val_unsigned = ( 2.0** nbits   -1) / (2**binpt)
    min_val_unsigned =   0
    max_val_signed   = ( 2.0**(nbits-1)-1) / (2**binpt)
    min_val_signed   = (-2.0**(nbits-1))   / (2**binpt)

    # check overflow
    if signed:
        if np.max(data) > max_val_signed:
            print "WARNING! Maximum value exceeded in overflow check."
            print "Max allowed value: " + str(max_val_signed)
            print "Max value in data: " + str(np.max(data))
        if np.min(data) < min_val_signed:
            print "WARNING! Minimum value exceeded in overflow check."
            print "Min allowed value: " + str(min_val_signed)
            print "Min value in data: " + str(np.min(data))

    else: # unsigned
        if np.max(data) > max_val_unsigned:
            print "WARNING! Maximum value exceeded in overflow check."
            print "Max allowed value: " + str(max_val_unsigned)
            print "Max value in data: " + str(np.max(data))
        if np.min(data) < min_val_unsigned:
            print "WARNING! Minimum value exceeded in overflow check."
            print "Min allowed value: " + str(min_val_unsigned)
            print "Min value in data: " + str(np.min(data))
