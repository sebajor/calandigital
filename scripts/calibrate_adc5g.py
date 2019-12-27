import argparse
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
import adc5g

parser = argparse.ArgumentParser(
    description="Calibrate ADC5G from ROACH2 using snapshot information.")
parser.add_argument("-i", "--ip", dest="ip", required=True,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="boffile to load into the FPGA.")
parser.add_argument("-g", "--genip", dest="generator_ip",
    help="Generator IP. If not used it doesn't try to use generator.")
parser.add_argument("-gf", "--genfreq", dest="testfreq", 
    help="Frequency (MHz) to set at the generator to perform the calibration.")
parser.add_argument("-gp", "--genpow", dest="testpow", 
    help="Power (dBm) to set at the generator to perform the calibration.")
parser.add_argument("-s0", "--zdok0snaps", dest="zdok0snaps", nargs="*",
    help="names of snapshot blocks (1 or 2) for zdok0 inputs.")
parser.add_argument("-s1", "--zdok1snaps", dest="zdok1snaps", nargs="*",
    help="names of snapshot blocks (1 or 2) for zdok1 inputs.")
parser.add_argument("-ns", "--nsamples", dest="nsamples", type=int, default=256,
    help="number of samples of snapshot to plot.")
parser.add_argument("-ns", "--nsamples", dest="nsamples", type=int, default=256,
    help="number of samples of snapshot to plot.")
parser.add_argument("-di", "--do_inl", dest="do_inl", action="store_true",
    help="if used, do INL calibration")
parser.add_argument("-lo", "--load_ogp", dest="load_ogp", action="store_true",
    help="if used, load OGP calibration.")
parser.add_argument("-li", "--load_inl", dest="load_inl", action="store_true",
    help="if used, load INL calibration.")
parser.add_argument("-psn", "--plot_snap", dest="plot_snapshots", action="store_true",
    help="if used, plot snapshot data for comparison.")
parser.add_argument("-psp", "--plot_spec", dest="plot_spectra", action="store_true",
    help="if used, plot spectra data for comparison.")
parser.add_argument("-cd", "--caldir", dest="caldir", default="adc5gcal",
    help="name of the directory were to save the calibration data (later compressed).")
parser.add_argument("-ld", "--loaddir", dest="loaddir", default="adc5gcal",
    help="name of the directory from were to load the calibration data \
    (assumes is is compressed).")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, boffile=args.boffile, rver=2)
    snapnames = args.zdok0snaps + args.zdok1snaps

    # turn on generator if IP was given
    if args.generator_ip is not None:
        generator = vxi11.Instrument(args.generator_ip)
        generator.write("freq " +str(args.genfreq) + " mhz")
        generator.write("power " +str(args.genpow) + " dbm")
        gererator.write("outp on")

    # get uncalibrated data if we want to plot
    if args.plot_snapshots or args.plot_spectra:
        snapdata_list = cd.read_snapshots(roach, snapshots, ">i1")

    # plot uncalibrated snap data
    if args.plot_snapshots:
        snapfig, snaplines_uncal, snaplines_cal = create_snap_figure(snapnames, args.nsamples)
        for line, snapdata for zip(snaplines_uncal, snapdata_list):
            line.set_data(range(args.snamples), snapdata[:args.nsamples])
        plt.pause(0.001)
    
    # plot uncalibrated spectral data
    if args.plot_spectra:
        specfig, speclines_uncal, speclines_cal = create_spec_figure(snapnames)
        for line, snapdata for zip(speclines_uncal, snapdata_list):
            # compute the fft of snapshot data
            nchannels = len(snapdata)
            uncal_spec = np.square(np.abs(np.fft.rfft(snapdata)))
            uncal_spec = cd.scale_and_dBFS_specdata(uncal_spec, nchannels, 8, nchannels)
            line.set_data(freqs, uncal_spec)



    # first do MMCM calibration (always necessary)
    if args.zdok0snaps is not None:
        perform_mmcm_calibration(roach, 0, args.zdok0snaps)
    if args.zdok1snaps is not None:
        perform_mmcm_calibration(roach, 1, args.zdok1snaps)




    # create calibration folder
    if args.do_ogp or args.do_inl:
        os.mkdir(args.caldir)

    # 



def create_snap_figure(snapnames, nsamples):
    """
    Create figure with the proper axes settings for plotting snaphots.
    """
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    nsnapshots = len(snapnames)
    dtype = ">i1" # harcoded adc5g 8 bit samples

    fig, axes = plt.subplots(*axmap[nsnapshots], squeeze=False)
    fig.set_tight_layout(True)

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

    print("Performing ADC%G MMCM calibration, ZDOK" + str(zdok) + "...")
    opt, gliches = adc5g.calibrate_mmcm_phase(roach, zdok, snapnames)
    adc5g.unset_test_mode(roach, zdok)
    print("done")

if __name__ == '__main__':
    main()
