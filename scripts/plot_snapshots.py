import argparse
import calandigital as cd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

parser = argparse.ArgumentParser(
    description="Plot snapshots from snapshot blocks in ROACH model.")
parser.add_argument("-i", "--ip", dest="ip", default=None,
    help="ROACH IP address.")
parser.add_argument("-b", "--bof", dest="boffile",
    help="Boffile to load into the FPGA.")
parser.add_argument("-u", "--upload", dest="upload", action="store_true",
    help="If used, upload .bof from PC memory (ROACH2 only).")
parser.add_argument("-sn", "--snapnames", dest="snapnames", nargs="*",
    help="Names of snapshot blocks to read.")
parser.add_argument("-dt", "--dtype", dest="dtype", default=">i1",
    help="Data type of snapshot data. Must be Numpy compatible.")
parser.add_argument("-ns", "--nsamples", dest="nsamples", type=int, default=256,
    help="Number of samples of snapshot to plot.")

def main():
    args = parser.parse_args()
    
    # initialize roach
    roach = cd.initialize_roach(args.ip, boffile=args.boffile, upload=args.upload)
    
    # create figure
    fig, lines = create_figure(args.snapnames, args.nsamples, args.dtype)

    # animation definition
    def animate(_):
        # get snapshot data
        snapdata_list = cd.read_snapshots(roach, args.snapnames, args.dtype)
        for line, snapdata in zip(lines, snapdata_list):
            line.set_data(range(args.nsamples), snapdata[:args.nsamples])
        return lines

    ani = FuncAnimation(fig, animate, blit=True)
    plt.show()

def create_figure(snapnames, nsamples, dtype):
    """
    Create figure with the proper axes settings for plotting snaphots.
    """
    axmap = {1 : (1,1), 2 : (1,2), 4 : (2,2), 16 : (4,4)}
    nsnapshots = len(snapnames)

    fig, axes = plt.subplots(*axmap[nsnapshots], squeeze=False)
    fig.set_tight_layout(True)

    lines = []
    for snapname, ax in zip(snapnames, axes.flatten()):
        ax.set_xlim(0, nsamples)
        ax.set_ylim(np.iinfo(dtype).min-10, np.iinfo(dtype).max+10)
        ax.set_xlabel('Samples')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.set_title(snapname)
        ax.grid()

        line, = ax.plot([], [], animated=True)
        lines.append(line)

    return fig, lines

if __name__ == '__main__':
    main()
