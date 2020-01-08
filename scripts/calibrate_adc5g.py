import argparse, vxi11
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
import adc5g

parser = argparse.ArgumentParser(
    description="Calibrate ADC5G from ROACH2 using snapshot information.")
parser.add_argument("-i", "--ip", dest="ip", required=True,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="Boffile to load into the FPGA.")
parser.add_argument("-g", "--genip", dest="generator_ip",
    help="Generator IP. Skip if generator is used manually.")
parser.add_argument("-gf", "--genfreq", dest="genfreq", 
    help="Frequency (MHz) to set at the generator to perform the calibration.")
parser.add_argument("-gp", "--genpow", dest="genpow", 
    help="Power (dBm) to set at the generator to perform the calibration.")
parser.add_argument("-s0", "--zdok0snaps", dest="zdok0snaps", nargs="*", default=[],
    help="Names of snapshot blocks (1 or 2) for zdok0 inputs.")
parser.add_argument("-s1", "--zdok1snaps", dest="zdok1snaps", nargs="*", default=[],
    help="If used, do INL calibration")
parser.add_argument("-lo", "--load_ogp", dest="load_ogp", action="store_true",
    help="If used, load OGP calibration.")
parser.add_argument("-li", "--load_inl", dest="load_inl", action="store_true",
    help="If used, load INL calibration.")
parser.add_argument("-psn", "--plot_snap", dest="plot_snapshots", action="store_true",
    help="If used, plot snapshot data for comparison.")
parser.add_argument("-psp", "--plot_spec", dest="plot_spectra", action="store_true",
    help="If used, plot spectra data for comparison.")
parser.add_argument("-ns", "--nsamples", dest="nsamples", type=int, default=256,
    help="number of samples of snapshot to plot.")
parser.add_argument("-bw", "--bandwidth", dest="bandwidth", type=float, default=1080,
    help="Bandwidth of the spectra to plot in MHz.")
parser.add_argument("-cd", "--caldir", dest="caldir", default="adc5gcal",
    help="Name of the directory were to save the calibration data (later compressed).")
parser.add_argument("-ld", "--loaddir", dest="loaddir", default="adc5gcal",
    help="Name of the directory from were to load the calibration data \
    (assumes it is compressed).")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, boffile=args.boffile, rver=2)
    snapnames = args.zdok0snaps + args.zdok1snaps

    # turn on generator if IP was given
    if args.generator_ip is not None:
        generator = vxi11.Instrument(args.generator_ip)
        generator.write("freq " +str(args.genfreq) + " mhz")
        generator.write("power " +str(args.genpow) + " dbm")
        generator.ask("outp on;*opc?")

    # get uncalibrated data if we want to plot
    if args.plot_snapshots or args.plot_spectra:
        snapdata_list = cd.read_snapshots(roach, snapnames, ">i1")

    # plot uncalibrated snap data
    if args.plot_snapshots:
        snapfig, snaplines_uncal, snaplines_cal = create_snap_figure(snapnames, 
            args.nsamples)
        
        for line, snapdata in zip(snaplines_uncal, snapdata_list):
            line.set_data(range(args.nsamples), snapdata[:args.nsamples])
        snapfig.canvas.draw()
    
    # plot uncalibrated spectral data
    if args.plot_spectra:
        # useful parameters for spectra ploting
        nchannels = len(snapdata)/2
        dBFS      = 6.02*8 + 1.76 + 10*np.log10(nchannels)
        specfig, speclines_uncal, speclines_cal = create_spec_figure(snapnames, 
            args.bandwidth, dBFS)
        
        freqs = np.linspace(0, args.bandwidth, nchannels, endpoint=False)
        for line, snapdata in zip(speclines_uncal, snapdata_list):
            # compute the fft of snapshot data
            uncal_spec = np.square(np.abs(np.fft.rfft(snapdata)[:-1]))
            uncal_spec = cd.scale_and_dBFS_specdata(uncal_spec, nchannels, 8, nchannels)
            line.set_data(freqs, uncal_spec)
        specfig.canvas.draw()

    # first do MMCM calibration (always necessary)
    if args.zdok0snaps: # if list is not empty
        perform_mmcm_calibration(roach, 0, args.zdok0snaps)
    if args.zdok1snaps: # if list is not empty
        perform_mmcm_calibration(roach, 1, args.zdok1snaps)

    # get calibrated data if we want to plot
    if args.plot_snapshots or args.plot_spectra:
        snapdata_list = cd.read_snapshots(roach, snapnames, ">i1")

    # plot calibrated snap data
    if args.plot_snapshots:
        for line, snapdata in zip(snaplines_cal, snapdata_list):
            line.set_data(range(args.nsamples), snapdata[:args.nsamples])
        snapfig.canvas.draw()

    # plot calibrated spectral data
    if args.plot_spectra:
        for line, snapdata in zip(speclines_cal, snapdata_list):
            # compute the fft of snapshot data
            uncal_spec = np.square(np.abs(np.fft.rfft(snapdata)[:-1]))
            uncal_spec = cd.scale_and_dBFS_specdata(uncal_spec, nchannels, 8, nchannels)
            line.set_data(freqs, uncal_spec)
        specfig.canvas.draw()

    # turn off generator if IP was given
    if args.generator_ip is not None:
        generator.write("outp off")

    # create calibration folder
    #if args.do_ogp or args.do_inl:
    #    os.mkdir(args.caldir)

    print("Done with all calibrations.")
    if args.plot_snapshots or args.plot_spectra:
        print("Close plots to finish.")
        plt.show()

def create_snap_figure(snapnames, nsamples):
    """
    Create figure with the proper axes settings for plotting snaphots.
    """
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    nsnapshots = len(snapnames)
    dtype = ">i1" # harcoded adc5g 8 bit samples

    fig, axes = plt.subplots(*axmap[nsnapshots], squeeze=False)
    fig.set_tight_layout(True)
    fig.show()
    fig.canvas.draw()

    lines_uncal = []; lines_cal = []
    for snapname, ax in zip(snapnames, axes.flatten()):
        ax.set_xlim(0, nsamples)
        ax.set_ylim(np.iinfo(dtype).min-10, np.iinfo(dtype).max+10)
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.set_title(snapname)
        ax.grid()

        lines = ax.plot([], [], [], [])
        lines_uncal.append(lines[0])
        lines_cal.append(  lines[1])

    return fig, lines_uncal, lines_cal

def create_spec_figure(specnames, bandwidth, dBFS):
    """
    Create figure with the proper axes settings for plotting spectra.
    """
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}

    fig, axes = plt.subplots(*axmap[len(specnames)], squeeze=False)
    fig.set_tight_layout(True)
    fig.show()
    fig.canvas.draw()

    lines_uncal = []; lines_cal = []
    for specname, ax in zip(specnames, axes.flatten()):
        ax.set_xlim(0, bandwidth)
        ax.set_ylim(-dBFS-2, 0)
        ax.set_xlabel('Frequency [MHz]')
        ax.set_ylabel('Power [dBFS]')
        ax.set_title(specname)
        ax.grid()

        lines = ax.plot([], [], [], [])
        lines_uncal.append(lines[0])
        lines_cal.append(  lines[1])

    return fig, lines_uncal, lines_cal

def perform_mmcm_calibration(roach, zdok, snapnames):
    """
    Perform MMCM calibration using Primiani's adc5g package.
    :param roach: FpgaClient object to communicate with ROACH.
    :param zdok: ZDOK port number of the ADC to calibrate (0 or 1).
    :param snapnames: list of snapshot blocks used for the calibration.
        Must have either 1 or 2 snapshot names.
    """
    adc5g.set_test_mode(roach, zdok)
    adc5g.sync_adc(roach)

    print("Performing ADC5G MMCM calibration, ZDOK" + str(zdok) + "...")
    opt, gliches = adc5g.calibrate_mmcm_phase(roach, zdok, snapnames)
    adc5g.unset_test_mode(roach, zdok)
    print("done")

if __name__ == '__main__':
    main()
