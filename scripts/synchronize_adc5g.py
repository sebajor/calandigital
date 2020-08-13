import pyvisa, argparse, time
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats

parser = argparse.ArgumentParser(
    description="Synchronize 2 ADC5G ADCs in ROACH2.")
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
parser.add_argument("-gm", "--genmult", dest="genmult", type=float, default=None,
    help="Frequency multiplier to set in generator settings if the setup \
    includes an RF multiplier after the generator.")
parser.add_argument("-lf", "--lofreq", dest="lofreq", type=float, default=0,
    help="LO frequency in MHz if a downconversion stage is used (use 0 if not).")
parser.add_argument("-b0", "--zdok0brams", dest="zdok0brams", nargs="*",
    help="Bram names for ZDOK0 spectrum.")
parser.add_argument("-b1", "--zdok1brams", dest="zdok1brams", nargs="*",
    help="Bram names for ZDOK1 spectrum.")
parser.add_argument("-cbr", "--crossbramsreal", dest="crossbramsreal", nargs="*",
    help="Bram names for cross spectrum, real part.")
parser.add_argument("-cbi", "--crossbramsimag", dest="crossbramsimag", nargs="*",
    help="Bram names for cross spectrum, imaginary part.")
parser.add_argument("-aw", "--addrwidth", dest="awidth", type=int, default=9,
    help="Width of bram address in bits.")
parser.add_argument("-dw", "--datawidth", dest="dwidth", type=int, default=64,
    help="Width of bram data in bits.")
parser.add_argument("-bw", "--bandwidth", dest="bandwidth", type=float, default=1080,
    help="Bandwidth of the spectra to plot in MHz.")
parser.add_argument("-cr", "--countreg", dest="count_reg", default="cnt_rst",
    help="Counter register name. Reset at initialization.")
parser.add_argument("-ar", "--accreg", dest="acc_reg", default="acc_len",
    help="Accumulation register name. Set at initialization.")
parser.add_argument("-al", "--acclen", dest="acclen", type=int, default=2**16,
    help="Accumulation length. Set at initialization.")
parser.add_argument("-dr", "--delayregs", dest="delay_regs", nargs="*", 
    default=["adc0_delay", "adc1_delay"],
    help="Delay registers. Define the amount of delay for each ADC.")
parser.add_argument("-stc", "--startchnl", dest="startchnl", type=int, default=1,
    help="Start channel for the synchronization sweep.")
parser.add_argument("-spc", "--stopchnl", dest="stopchnl", type=int, default=2047,
    help="Stop channel for the synchronization sweep.")
parser.add_argument("-chs", "--chnlstep", dest="chnlstep", type=int, default=8,
    help="Channel step for the synchronization sweep.")

def main():
    args = parser.parse_args()
    
    # initialize roach
    roach = cd.initialize_roach(args.ip, boffile=args.boffile, upload=args.upload)

    # useful parameters
    nbrams         = len(args.zdok0brams)
    dtype_pow      = '>u' + str(args.dwidth/8)
    dtype_crosspow = '>i' + str(args.dwidth/8)
    nchannels      = 2**args.awidth * nbrams 
    test_channels  = range(args.startchnl, args.stopchnl, args.chnlstep)
    if_freqs       = np.linspace(0, args.bandwidth, nchannels, endpoint=False)
    rf_freqs       = if_freqs + args.lofreq
    test_freqs     = if_freqs[test_channels]
    dBFS           = 6.02*8 + 1.76 + 10*np.log10(nchannels)
    # estimated time for two accumulated spectra to pass
    pause_time     = 2 * 1/(args.bandwidth*1e6) * 2**args.awidth * nbrams * args.acclen
    
    # create figure
    fig, lines = create_figure(args.bandwidth, dBFS, test_freqs)

    # initialize generator
    if args.generator_name is None:
        rm = pyvisa.ResourceManager('@sim')
        args.generator_name = "TCPIP::localhost::2222::INSTR"
    else:
        rm = pyvisa.ResourceManager('@py')
    generator = rm.open_resource(args.generator_name)
    generator.write("power " +str(args.genpow) + " dbm")

    # set multiplier if given
    if args.genmult is not None:
        print("Using frequency multiplier of " + str(args.genmult))
        generator.write("freq:mult " + str(args.genmult))

    # turn on generator
    generator.query("outp on;*opc?")
    
    # initial setting of registers
    print("Setting accumulation register to " + str(args.acclen) + "...")
    roach.write_int(args.acc_reg, args.acclen)
    print("done")
    print("Resseting counter registers...")
    roach.write_int(args.count_reg, 1)
    roach.write_int(args.count_reg, 0)
    print("done")

    # Main synchronization loop
    print "Synchronizing ADCs..."
    time.sleep(pause_time) 
    while True:
        ratios = []

        for i, chnl in enumerate(test_channels):
            # set generator frequency
            freq = rf_freqs[chnl]
            generator.query("freq " + str(freq) + " mhz; *opc?")
            time.sleep(pause_time)

            # get power data
            aa = cd.read_interleave_data(roach, args.zdok0brams,
                args.awidth, args.dwidth, dtype_pow)
            bb = cd.read_interleave_data(roach, args.zdok1brams,
                args.awidth, args.dwidth, dtype_pow)

            # get crosspow data
            ab_re = cd.read_interleave_data(roach, args.crossbramsreal,
                args.awidth, args.dwidth, dtype_crosspow)
            ab_im = cd.read_interleave_data(roach, args.crossbramsimag,
                args.awidth, args.dwidth, dtype_crosspow)

            # combine real and imaginary part of crosspow data
            ab = ab_re + 1j*ab_im

            # compute the complex ratios (magnitude ratio and phase difference)
            # use first input as reference
            ratios.append(np.conj(ab[chnl]) / aa[chnl]) # (ab*)* / aa* = a*b / aa* = b/a

            # plot spectra
            spec_zdok0 = cd.scale_and_dBFS_specdata(aa, args.acclen, dBFS)
            lines[0].set_data(if_freqs, spec_zdok0)
            spec_zdok1 = cd.scale_and_dBFS_specdata(bb, args.acclen, dBFS)
            lines[1].set_data(if_freqs, spec_zdok1)

            # plot mag ratio and angle diff
            lines[2].set_data(test_freqs[:i+1], np.abs(ratios))
            lines[3].set_data(test_freqs[:i+1], np.angle(ratios, deg=True))

            # update plots
            fig.canvas.draw()
            fig.canvas.flush_events()
    
        # get delays between adcs
        delay = compute_adc_delay(test_freqs, ratios, args.bandwidth) 

        # check adcs sync status, apply delay if necesary
        if delay == 0:
            print("ADCs successfully synchronized!")
            break
        elif delay > 0: # if delay is positive adc1 is ahead, hence delay adc1
            current_delay = roach.read_int(args.delay_regs[1])
            roach.write_int(args.delay_regs[1], current_delay + delay)
        else: # (delay < 0) if delay is negative adc0 is ahead, hence delay adc0
            current_delay = roach.read_int(args.delay_regs[0])
            roach.write_int(args.delay_regs[0], current_delay + -1*delay)

    # revert generator multiplier if used
    if args.genmult is not None:
        generator.write("freq:mult 1")

    # turn off generator and close resource manager
    generator.write("outp off")
    rm.close()

def create_figure(bandwidth, dBFS, syncfreqs):
    """
    Create figure with the proper axes for the synchronization procedure.
    """
    fig, axes = plt.subplots(2, 2, squeeze=False)
    fig.set_tight_layout(True)
    fig.show()
    fig.canvas.draw()

    # spectral axes
    axes[0,0].set_xlim(0, bandwidth)       ; axes[0,1].set_xlim(0, bandwidth)         
    axes[0,0].set_ylim(-dBFS-2, 0)         ; axes[0,1].set_ylim(-dBFS-2, 0)
    axes[0,0].set_xlabel('Frequency [MHz]'); axes[0,1].set_xlabel('Frequency [MHz]')
    axes[0,0].set_ylabel('Power [dBFS]')   ; axes[0,1].set_ylabel('Power [dBFS]')
    axes[0,0].set_title('ZDOK0')           ; axes[0,1].set_title('ZDOK1')
    axes[0,0].grid()                       ; axes[0,1].grid()
    linezdok0, = axes[0,0].plot([], [])    ; linezdok1, = axes[0,1].plot([], [])

    # magnitude ratio axes
    axes[1,0].set_xlim(syncfreqs[0], syncfreqs[-1])       
    axes[1,0].set_ylim(0, 2)         
    axes[1,0].set_xlabel('Frequency [MHz]')
    axes[1,0].set_ylabel('Mag Ratio [linear]')   
    axes[1,0].grid()                       
    linemag, = axes[1,0].plot([], [])     

    # magnitude ratio axes
    axes[1,1].set_xlim(syncfreqs[0], syncfreqs[-1])       
    axes[1,1].set_ylim(-200, 200)         
    axes[1,1].set_xlabel('Frequency [MHz]')
    axes[1,1].set_ylabel('Angle diff [degrees]')   
    axes[1,1].grid()                       
    lineang, = axes[1,1].plot([], [])     

    return fig, [linezdok0, linezdok1, linemag, lineang]

def compute_adc_delay(freqs, ratios, bandwidth):
    """
    Compute the adc delay between two unsynchronized adcs. It is done by 
    computing the slope of the phase difference with respect the frequency, 
    and then it translates this value into an integer delay in number of 
    samples.
    :param freqs: frequency array in which the sideband ratios where computed.
    :param ratios: complex ratios array of the adcs. The complex ratios is the 
        complex division of an spectral channel from adc0 with adc1.
    :param bandwidth: spectrometer bandwidth.
    :return: adc delay in number of samples.
    """
    phase_diffs = np.unwrap(np.angle(ratios))
    linregress_results = scipy.stats.linregress(freqs, phase_diffs)
    angle_slope = linregress_results.slope
    delay = int(round(angle_slope * 2*bandwidth / (2*np.pi))) # delay = dphi/df * Fs / 2pi
    print "Computed delay: " + str(delay)
    return delay
   
if __name__ == '__main__':
    main()
