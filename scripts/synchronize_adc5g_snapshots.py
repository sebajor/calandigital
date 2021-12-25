#!/usr/bin/env python2
import calandigital as calan
import numpy as np
import matplotlib.pyplot as plt
import argparse, time, pyvisa


parser = argparse.ArgumentParser(
    description="Synchronize 2 ADC5G ADCs in ROACH2 using snapshot blocks.")

parser.add_argument("-i", "--ip", dest="ip", default=None,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="Boffile to load into the FPGA.")
parser.add_argument("-u", "--upload", dest="upload", action="store_true",
    help="If used, upload .bof from PC memory (ROACH2 only).")
parser.add_argument("-g", "--genname", dest="generator_name", default=None,
    help="Generator name as a VISA string. Simulated if not given.\
    See https://pyvisa.readthedocs.io/en/latest/introduction/names.html")
parser.add_argument("-gp", "--genpow", dest="genpow", type=float,
    help="Power (dBm) to set at the generator to perform the calibration.")
parser.add_argument("-gf", "--genfreq", dest="genfreq", type=float,
        help="Frequency (MHz) to set at the generator")
parser.add_argument("-bw", "--bandwidth", dest="bandwidth", type=float, default=1080,
    help="Bandwidth of the spectra to plot in MHz.")


parser.add_argument("-aw", "--addrwidth", dest="awidth", type=int, default=9,
    help="Width of snapshot address in bits.")
parser.add_argument("-dw", "--datawidth", dest="dwidth", type=int, default=64,
    help="Width of snapshot data in bits.")

parser.add_argument("-dr", "--delayregs", dest="delay_regs", nargs="*", 
    default=["adc0_delay", "adc1_delay"],
    help="Delay registers. Define the amount of delay for each ADC.")
parser.add_argument("-sr", "--snapregs", dest="snap_regs", nargs="*", 
    default=["adcsnap0", "adcsnap1"],
    help="adc0 and adc1 snapshots blocks")
parser.add_argument("-st", "--snaptrig", dest="snap_trig", default="snap_trig",
    help="trigger for the snapshot capture")

parser.add_argument("-it", "--iter", dest="iters", default=1,
        help="number of iterations to try to adjust the phase of the adcs")


def get_snap_sync(roach, snap_names=['adcsnap0', 'adcsnap1'], trig_reg='snap_trig',
        addr_width=10,word_size=8, dtype='>i1'):
    """ Prepares the snapshot blocks to receive a trigger and then save data
        so the data saved is coherent and mantains the phase
        roach: corr class
        snap_names: names of the snapshots
        trig_reg: trigger register name
        addr_width : how many words to read
        word_size: size of the words in bits
    """
    word_bytes = word_size/8
    roach.write_int(trig_reg, 0)
    time.sleep(0.1)
    for snap in snap_names:
        ##prepare snapshot capture
        roach.write_int(snap+'_ctrl', 0)
        roach.write_int(snap+'_ctrl', 1)
    time.sleep(0.1)
    roach.write_int(trig_reg, 1)
    time.sleep(0.1)
    roach.write_int(trig_reg, 0)
    adc_data = np.zeros([len(snap_names), 2**addr_width])
    for i in range(len(snap_names)):
        adc_data[i, :] = calan.read_data(roach, snap_names[i]+'_bram', addr_width,
                word_size, dtype)
    return adc_data


def get_phase(adc0, adc1, freq, fs=1200):
    """ get phase in degrees between two adc time values usign a dft
        adc0: adc0 snapshot data
        adc1: adc1 snapshot data
        freq: frequency of the injected tone in MHz
        fs: sampling frequency in MHz
    """
    dft_len = len(adc0)
    k = round(1.*freq/fs*dft_len)
    #print(k)
    twid_factors = np.exp(-1j*2*np.pi*np.arange(dft_len)*k/dft_len)
    dft0 = np.mean(adc0*twid_factors)
    dft1 = np.mean(adc1*twid_factors)
    correlation = dft0*np.conj(dft1)
    phase = np.rad2deg(np.angle(correlation))
    return phase


def find_period(corr_data):
    """Search the peaks of a correlation data looking for the change
    in the curvature of the peaks (ie second derivative) Then we look
    for the maximum value in those index.
    https://stackoverflow.com/questions/59265603/how-to-find-period-of-signal-autocorrelation-vs-fast-fourier-transform-vs-power
    """
    inflection = np.diff(np.sign(np.diff(corr_data)))
    peak = (inflection <0).nonzero()[0]+1
    delay = peak[corr_data[peak].argmax()]
    return delay



def cross_corr_dly(adc0, adc1):
    """ Return the delay that maximize the correlation of the
    time domain adc0 and adc1.
    outputs:
            corr0: output of correlate(adc0, adc1)
            corr1: output of correalte(adc1, adc0)
            [delay0, delay1] where delay0 is comes from correlate(adc0, adc1)
            and delay1 comes from correlate(adc1, adc0)
    """
    N = len(adc0)
    adc0_data = adc0-np.mean(adc0)
    adc1_data = adc1-np.mean(adc1)
    corr0 = np.correlate(adc0_data, adc1_data, mode='full')
    corr0 = corr0[-N:]
    corr1 = np.correlate(adc1_data, adc0_data, mode='full')
    corr1 = corr1[-N:]
    delay0 = find_period(corr0)
    delay1 = find_period(corr1)
    return corr0, corr1, delay0, delay1


def adjust_adc_delay(roach, snaps=['adcsnap0', 'adcsnap1'],
        snap_trig='snap_trig', adc_delay=['adc0_delay','adc1_delay']):
    adc0, adc1 = get_snap_sync(roach, snap_names=snaps, trig_reg=snap_trig,
            addr_width=10,word_size=8, dtype='>i1')
    corr0, corr1, dly0, dly1 = cross_corr_dly(adc0, adc1)
    delay = [dly0, dly1]
    ind = np.argmin(delay)
    prev_adc0 = roach.read_int(adc_delay[0])
    prev_adc1 = roach.read_int(adc_delay[1])

    if(ind==0):
        roach.write_int(adc_delay[1], delay[ind]+prev_adc1)
    else:
        roach.write_int(adc_delay[0], delay[ind]+prev_adc0)

def main():
    args = parser.parse_args()
    # initialize roach
    roach = calan.initialize_roach(args.ip, boffile=args.boffile, upload=args.upload)
    # initialize generator
    if args.generator_name is None:
        rm = pyvisa.ResourceManager('@sim')
        args.generator_name = "TCPIP::localhost::2222::INSTR"
    else:
        rm = pyvisa.ResourceManager('@py')
    generator = rm.open_resource(args.generator_name)
    generator.write("power " +str(args.genpow) + " dbm")
    generator.write("freq "+str(args.genfreq)+" mhz")
    # turn on generator
    generator.query("outp on;*opc?")
    fs = args.bandwidth*2

    adc0, adc1 = get_snap_sync(roach, snap_names=args.snap_regs, trig_reg=args.snap_trig,
            addr_width=args.awidth,word_size=args.dwidth, dtype='>i'+str(args.dwidth//8))
    phase_old = get_phase(adc0, adc1, args.genfreq, fs=fs)
    print("phase old: %.4f: "%phase_old)

    fig = plt.figure()
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    ax1.grid()
    ax2.grid()
    ax1.plot(adc0)
    ax1.plot(adc1)
    ax1.set_title('Not synchronized')
    for i in range(int(args.iters)):
        adjust_adc_delay(roach, snaps=args.snap_regs,
            snap_trig=args.snap_trig, adc_delay=args.delay_regs)
        time.sleep(0.1)
        adc0, adc1 = get_snap_sync(roach, snap_names=args.snap_regs, trig_reg=args.snap_trig,
                addr_width=args.awidth,word_size=args.dwidth, dtype='>i'+str(args.dwidth//8))

        phase = get_phase(adc0, adc1, args.genfreq, fs=fs)
        print("phase new: %.4f: "%phase)
    
    # turn off generator and close resource manager
    generator.write("outp off")
    rm.close()
    
    #plot the sync data
    ax2.plot(adc0)
    ax2.plot(adc1)
    ax2.set_title('Synchronized')

    plt.show()
    

if __name__ == '__main__':
    main()
