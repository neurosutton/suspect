import numpy
import os


def save_raw(filename, data):
    with open(filename, 'w') as fout:
        fout.write(" $SEQPAR\n")
        fout.write(" ECHOT = {}\n".format(data.te))
        fout.write(" HZPPPM = {}\n".format(data.f0))
        fout.write(" SEQ = 'PRESS'\n")
        fout.write(" $END\n")
        fout.write(" $NMID\n")
        fout.write(" FMTDAT = '(2E15.6)'\n")
        # convert the volume from mm^3 to cc
        fout.write(" VOLUME = {}\n".format(data.voxel_size() * 1e-3))
        fout.write(" $END\n")
        for point in numpy.nditer(data, order='C'):
            fout.write("  {0: 4.6e}  {1: 4.6e}\n".format(float(point.real), float(point.imag)))


def write_all_files(filename, data, wref_data=None, params=None):
    """
    Creates an LCModel control file for processing the supplied MRSData, and
    optional water reference data, updating the default parameters with any
    values supplied through params.

    :param filename: the location where the control file should be saved.
    :param data: MRSData to be processed.
    :param wref_data: Optional MRSData containing water reference.
    :param params: Optional dictionary containing non-default parameter values.
    :return:
    """

    # we assume that the data has one spectral dimension, any others must be
    # spatial
    if len(data.shape) == 1:
        shape = (1, 1, 1)
    elif len(data.shape) == 2:
        shape = (data.shape[0], 1, 1)
    elif len(data.shape) == 3:
        shape = (data.shape[0], data.shape[1], 1)
    elif len(data.shape) == 4:
        shape = data.shape[0:3]
    elif len(data.shape) > 4:
        raise ValueError("LCModel cannot handle data with more than 4 dimensions")

    # We need to save a bunch of files for LCModel to process: a raw file for
    # the data, possibly a raw file for the wref and a control file for each
    # slice. In addition, in the absence of information in the params file
    # about where to save the output (.ps, .csv, .table etc.) that should also
    # be saved in the same folder as the input data for LCModel.
    folder, file_root = os.path.split(filename)
    file_root, ext = os.path.splitext(file_root)

    base_params = {
        "FILBAS": "/home/spectre/.lcmodel/basis-sets/provencher/press_te30_3t_gsh_v3.basis",
        "ICOLST": 1,
        "ICOLEN": shape[0],
        "NDCOLS": shape[0],
        "IROWST": 1,
        "IROWEN": shape[1],
        "NDROWS": shape[1],
        "NDSLIC": shape[2],
        "DOWS": "T" if wref_data is not None else "F",
        "DOECC": "T" if wref_data is not None else "F",
        "FILRAW": os.path.join(folder, file_root + ".RAW"),
        "FILPS": os.path.join(folder, file_root + ".PS")
    }
    if wref_data is not None:
        base_params["FILH20"] = os.path.join(folder, file_root + ".H2O"),

    # add the user supplied parameters to the list
    if params is not None:
        base_params.update(params)

    # make a few modifications based on user edits
    if "FILTAB" in base_params:
        base_params["LTABLE"] = 7
        base_params["FILTAB"] = "'{}'".format(base_params["FILTAB"])
    elif "LTABLE" in base_params:
        base_params["LTABLE"] = 7
        base_params["FILTAB"] = os.path.join(folder, file_root + ".TABLE")
    if "FILCSV" in base_params:
        base_params["LCSV"] = 11
    elif "LCSV" in base_params:
        base_params["LCSV"] = 11
        base_params["FILCSV"] = os.path.join(folder, file_root + ".CSV")
    if "FILCOO" in base_params:
        base_params["LCOORD"] = 9
    elif "LCOORD" in base_params:
        base_params["LCOORD"] = 9
        base_params["FILCOO"] = os.path.join(folder, file_root + ".COORD")

    save_raw(base_params["FILRAW"], data)
    if wref_data is not None:
        save_raw(base_params["FILH20"], wref_data)
    # have to add single quotes to the various paths
    base_params["FILRAW"] = "'{}'".format(base_params["FILRAW"])
    base_params["FILBAS"] = "'{}'".format(base_params["FILBAS"])
    base_params["FILPS"] = "'{}'".format(base_params["FILPS"])
    if wref_data is not None:
        base_params["FILH20"] = "'{}'".format(base_params["FILH20"])

    for slice_index in range(shape[2]):
        control_filename = "{0}_sl{1}.CONTROL".format(file_root, slice_index)
        control_filepath = os.path.join(folder, control_filename)
        with open(control_filepath, 'wt') as fout:
            fout.write(" $LCMODL\n")
            fout.write(" OWNER = ''\n")
            fout.write(" KEY = 123456789\n")
            fout.write(" DELTAT = {}\n".format(data.dt))
            fout.write(" HZPPPM = {}\n".format(data.f0))
            fout.write(" NUNFIL = {}\n".format(data.np))
            for key, value in base_params.items():
                fout.write(" {0} = {1}\n".format(key, value))
            fout.write(" $END\n")
