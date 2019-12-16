import calandigital as cd

params = cd.parse_arguments()
roach = cd.initialize_roach(
    params.ip, 
    boffile       = params.boffile, 
    roach_version = params.roach_version)
