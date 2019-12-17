import argparse
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

parser = argparse.ArgumentParser(
    description="Initialize ROACH communication and program boffile.")
parser.add_argument("-i", "--ip", dest="ip", required=True,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="boffile to load into the FPGA.")
parser.add_argument("-r", "--rver", dest="roach_version", type=int, default=2,
    help="ROACH verstion to use. 1 and 2 supported.")
parser.add_argument("-s", "--snapshots", dest="snapshots", nargs='+',
    help="snapshot names. Overrides snapshot format.")
parser.add_argument("-sf", "--snapshot_format", dest="snapname", default="adcsnap",
    help="snapshot naming format used to deduce snapshot names.\
    Needs nsnapshot argument also.")
parser.add_argument("-ns", "--nsnapshots", dest="nsnapshots", type=int, default=2,
    help="number of snapshots. Needed to derive snapshot names.")
parser.add_argument("-dt", "--dtype", dest="dtype", default=">i1",
    help="data type of snapshot format. Must be Numpy compatible.")
parser.add_argument("-sa", "--samples", dest="nsamples", type=int, default=256,
    help="samples of snapshot to plot. By default plot all samples.")

def main():
    args = parser.parse_args()
    
    roach = cd.initialize_roach(args.ip, 
        boffile       = args.boffile, 
        roach_version = args.roach_version)

    # get snapshot names
    if args.snapshots is not None:
        snapshots = args.snapshots
    else:
        snapshots = [args.snapname + str(i) for i in range(args.nsnapshots)]

    fig, lines = create_figure(snapshots, args.nsamples, args.dtype)

    def animate(_):
        snapdata_list = cd.read_snapshots(roach, snapshots, args.dtype)
        for line, snapdata in zip(lines, snapdata_list):
            line.set_data(range(args.nsamples), snapdata[:args.nsamples])
        return lines

    ani = FuncAnimation(fig, animate, blit=True)
    plt.show()

def create_figure(snapshots, nsamples, dtype_string):
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    nsnapshots = len(snapshots)
    dtype = np.dtype(dtype_string)

    fig, axes = plt.subplots(*axmap[nsnapshots])
    fig.set_tight_layout(True)

    lines = []
    for ax in axes.flatten():
        ax.set_xlim(0, nsamples)
        ax.set_ylim(np.iinfo(dtype).min-10, np.iinfo(dtype).max+10)
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.grid()

        line, = ax.plot([], [], animated=True)
        lines.append(line)

    return fig, lines

if __name__ == '__main__':
    main()
