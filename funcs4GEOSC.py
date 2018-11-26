#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Functions for use with the GEOS-Chem chemical transport model (CTM).

Use help(<name of function>) to get details on a particular function.

NOTE(S):
 - This module is underdevelopment vestigial/inefficient code is being removed/updated.
 - Where external code is used credit is given.
"""

# ----------------------------- Section 0 -----------------------------------
# -------------- Required modules:
#
# compatibility with both python 2 and 3
from __future__ import print_function

# -- I/O / Low level
import os
import sys
import csv
import glob
try:
    if (sys.version_info.major <= 2):
        import pygchem
        if pygchem.__version__ == '0.2.0':
            import pygchem.diagnostics as gdiag
        else:
            try:
                from pygchem import datasets
            except:
                import pygchem.datafields as datasets
except ImportError:
    print( 'pygchem not imported!')
import pandas as pd
import xarray as xr
import re
from netCDF4 import Dataset
try:
    import iris
except  ImportError:
    print('WARNING: iris and cartopy have stability issues')
import logging

# -- Math/Analysis
import numpy as np
from time import mktime
import scipy.stats as stats
import math

# -- Time
import time
import calendar
import datetime as datetime
from datetime import datetime as datetime_

# --  This needs to be updated, imports should be specific and in individual functions
# import tms modules with shared functions
from .funcs4core import *
from .funcs4generic import *
from .funcs4time import *
from .funcs4pf import *
from .funcs_vars import *
from .Scripts.bpch2netCDF import convert_to_netCDF



# --------------------------------- Section 2 ----------------------------------
# -------------- Model Data Extractors
#

# ----
# X.XX - Get array of surface area ( m^2 ) for a 2D grid
# ----
def get_surface_area(res=None, wd=None, debug=False):
    """
    Get_surface_area of grid boxes for a given resolution

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    res (str): the resolution if wd not given (e.g. '4x5' )
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    (array) 2D surface area of grid boxes for a given resolution

    Notes
    -----
     - this function accesses previsouly run GEOS-Chem
        1day files with just DXYP / DXYP diagnostic ouptuted
     - back compatibility with PyGChem 0.2.0 is retained
    """

    logging.info( "Getting the surface area for res={}".format(res) )

    if isinstance( res, type(None)) and isinstance( wd, type(None)):
        res = ('4x5')
        logging.warning("No res or wd specified. Assuming 4x5.")

    logging.debug( locals() )

    # if the wd has not been specified then use the previous runs
    if isinstance( wd, type(None)):

        # Get AC_tools location, then set example data folder location
        import os
        import inspect
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.dirname(os.path.abspath(filename))
        dwd = path+'/data/LM/'
        logging.debug("dwd = " + str( dwd) )
        # Choose the correct directory for a given resolution
        dir = {
        '4x5':'LANDMAP_LWI_ctm',  \
        '2x2.5': 'LANDMAP_LWI_ctm_2x25',  \
        '0.5x0.666' :'LANDMAP_LWI_ctm_05x0666',  \
        '0.25x0.3125' :'LANDMAP_LWI_ctm_025x03125',  \
        }[res]
        fd = dwd +dir

        logging.debug( "resolution = {res}, lookup directory = {fd}".format( \
            res=res, fd=fd) )
        wd = fd

    logging.debug("Trying to get surface area from {wd}".format(wd=wd))
    try:
        s_area = get_GC_output( wd, vars=['DXYP__DXYP'] )
    except ValueError:
        logging.debug("Failed getting surface area from wd")
        logging.debug("Trying to get surface area grom bpch file pygchem v0.2")
        if pygchem.__version__ == '0.2.0' :
            ctm = gdiag.CTMFile.fromfile( fd +'/ctm.bpch' )
            diags = ctm.filter(name="DXYP",category="DXYP")#,time=date_list[0])

            # extract diags
            first_time=True
            logging.debug( 'Diags: ', diags )
            while first_time:
                for diag in diags:
                    logging.debug( 'Diag unit: ', diag.unit )
                    s_area = diag.values
                first_time=False
    except:
        logging.error("Could not get the surface area!")
        raise ValueError("Could not find the surface area")

    return s_area

# ----
# X.XX
# ----
def list_variables(wd=None):
    """
    Show a list of variables in a wd that we can get at.

    Parameters
    ----------
    wd (None): Specify the working directory

    Returns
    -------
    (None) prints a list of variables.

    Notes
    -------
    Only currently prints variables in the ctm.nc
    Should be expanded to include planeflight and HEMCO
    """

    logging.info("Listing variables in {wd}".format(wd=wd))
    if isinstance( wd, type(None)):
        raise ValueError("Please specify a working dir")

    # Try listing all bpch variables in ctm.nc
    try:
        logging.info("Listing all variables in netCDF file")
        ctm_nc = os.path.join(wd, 'ctm.nc')
        if not os.path.isfile( ctm_nc ):
            convert_to_netCDF( wd )


        print("""
                -------------------------
                ctm.nc variables:
                -------------------------
                """)
        for var in Dataset( ctm_nc ).variables:
            print(var)
    except:
        logging.info("No ctm.nc (bpch) data found")

    # Try listing all hemco variables
    try:
        logging.info("Listing all variables in HEMCO files")
        hemco_nc = os.path.join(wd, 'hemco.nc' )
        if not os.path.isfile( hemco_nc ):
            convert_to_netCDF( wd )
        print("""
                ---------------------
                 hemco.nc variables:
                ---------------------
                """)
        for var in Dataset( hemco_nc ).variables:
            print(var)
    except:
        logging.info("No HEMCO data found")

    # Try listing all variables form planeflight
#    try:
#        logging.info("Listing all variables in planeflight")

    return

# ----
# X.XX - Get Land map.
# ----
def get_land_map(res='4x5', date=None, wd=None, debug=False):
    """
    Return land, water, and ice indices (LWI ) from GEOS-Chem with integers
    for Land (1) and Water (0). Ice fraction is given as fractional values.

    Parameters
    -------
    res (str): resolution of model to get land map for
    wd (str): directory contain file with LWI

    Returns
    -------

    Notes
    -----
     - This approach is inefficent and requires large files. Could this be improved with
     on-line extract on inclusion of generic output for various resoltions as txt files?
    """
    logging.info( 'called get surface area, for {}'.format(res) )
    # Get AC_tools location, then set example data folder location
    import os
    import xarray as xr
    import inspect
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    path = os.path.dirname(os.path.abspath(filename))
    dwd = path+'/data/LM/'
    # choose the right directory for the data
    dir = {
    '4x5':'LANDMAP_LWI_ctm',  \
    '2x2.5': 'LANDMAP_LWI_ctm_2x25',  \
    '0.5x0.666' :'LANDMAP_LWI_ctm_05x0666',  \
    '0.25x0.3125' :'LANDMAP_LWI_ctm_025x03125',  \
    '0.125x0.125' : 'TEMP_NASA_Nature_run', \
        }[res]
    land_dir = dwd +dir
    if debug: logging.info( land_file )

    # retain backwards compatibility - This is redundant: remove!
    if pygchem.__version__ == '0.2.0':
        ctm_f = gdiag.CTMFile.fromfile( land_dir + '/ctm.bpch' )
        diags = ctm_f.filter(name="LWI",category="LANDMAP")

        # Exctract from ctm.bpch
        first_time=True
        if (first_time):
            for diag in diags:
                scalar = diag.values[:,:,:]
                first_time=False
                logging.info( list(locals().keys()) )
                landmap=scalar

    # use new pygchem (>0.3.0) approach
    else:
        if res == '0.125x0.125':
            #
            ds = xr.open_dataset(land_dir+'ctm.nc')
            # No date? Just use annual average
            if isinstance( date, type(None) ):
                landmap = ds['LWI'].mean(dim='time').values
            if isinstance( date, int ):
                import glob
                # find nearest datetime
#                landmap = ds['LWI']
#                landmap = landmap.sel(time=date, method='nearest').values
                # Kludge, just find nearest month for now.
                months = ds['time.month'].values
                ind = find_nearest( date, months )
                landmap = ds['LWI'][ind,...].values
                # transpose (as PyGChem read was re-ordergin COARDS NetCDF)
                landmap = landmap.T
            else:
                landmap = ds['LWI']

        else:
            landmap = get_GC_output( wd=land_dir, vars=['LANDMAP__LWI'] )
            # Just use NetCDF4 instead of AC_tools function
#            landmap = Dataset(land_dir+'ctm.nc', 'r')['LANDMAP__LWI'][:]

    return landmap

# ----
# X.XX - get air mass (4D) np.array in kg
# ----
def get_air_mass_np( ctm_f=None, wd=None, times=None, trop_limit=True,\
        debug=False ):
    """
    Get array of air mass in kg

    Parameters
    -------
    wd (str): Specify the wd to get the results from a run.
    trop_limit (boolean): limit 4D arrays to troposphere
    ctm_f (file object): PyGChem (v2.0) opened ctm.bpch file  - vestigial
    times (list): list of times to extract model for - vestigial
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    (np.array)
    """
    logging.info( 'get air mass called' )
    # retain PyGChem 0.2.0 version for back compatibility
    if pygchem.__version__ == '0.2.0':
        diagnostics = ctm_f.filter( name='AD', category="BXHGHT-$",time=times )
        logging.debug( diagnostics )
        for diag in diagnostics:
            # Extract data
            scalar = np.array( diag.values[:,:,:] )[...,None]
            logging.debug( '{} - {}'.format(diag.name, scalar.shape) )
            try:
                arr = np.concatenate( (np_scalar, scalar), axis=3 )
            except NameError:
                arr = scalar

        if trop_limit:
            arr = arr[...,:38,...]

    # Or use PyGChem 0.3.0 approach
    else:
        # Get air mass in kg
        arr = get_GC_output( wd=wd, vars=['BXHGHT_S__AD'], \
            trop_limit=trop_limit, dtype=np.float64)

        logging.debug( 'arr type={}, shape={}'.format( type(arr), arr.shape ))
    return arr


# ----
# X.XX - Get OH mean value - [1e5 molec/cm3]
# ----
def get_OH_mean( wd, debug=False, file_type='*geos*log*' ):
    """
    Get mean OH concentration (1e5 molec/cm3) from geos.log files
    in given directory
    """
    logging.debug('get_OH_mean called for wd={}'.format(wd))
    # --- Find all geos log files in directory...
    files = glob.glob( wd+'/'+file_type )
    if len(files) < 1:
        err_str = 'WARNING! - no files found (assuming type={})'
        logging.info( err_str.format(file_type) )
        print( err_str.format(file_type) )
        files = glob.glob( wd+'/logs/'+file_type )
        if len(files) < 1:
            err_str = 'WARNING! - no files found (type={} in wd/log/*)'
            logging.info( err_str.format(file_type) )
            # try
            file_type = 'log.*'
            files = glob.glob( wd+'/logs/'+file_type )
            print( 'Loooking for {} files instead'.format( file_type)  )
            if len(files) < 1:
                err_str = 'WARNING! - no files found (type={} in wd/log/*)'
                logging.info( err_str.format(file_type) )

    # --- If there are any, then
    if len(files) > 1:
        # Loop and extract OH means, take an average if n>0
        z=[]
        for file in files:
            with open(file) as f:
                if debug:
                    print((file, f, z))
                for line in f:
                    if "Mean OH =    " in line:
                        z += [ float(line.split()[3] ) ]
        logging.info( 'mean OH calculated from {} files'.format( len(z) ) )
        return np.mean(z)
    else:
        print('No *log files found! (folder:{})'.format(wd) )
        sys.exit()

# ----
# X.XX - Get CH4 mean value - v/v
# ----
def get_CH4_mean( wd, rtn_global_mean=True, rtn_avg_3D_concs=False, \
        res='4x5', debug=False ):
    """
    Get mean CH4 concentrtaion from geos.log files in given directory

    Parameters
    -------

    Returns
    -------

    Notes
    -----
    """

    if debug:
        print(wd)
    # find all geos log files...
    files = glob.glob( wd+'/*geos*log*' )

    # Loop and extract CH4 means, take an average if n>0
    regex = re.compile( 'CH4{}:'.format('.'*13) )
    z=[]
    for file in files:
        with open(file) as f:
            if debug:
                print((file, f, z))
            for line in f:
                if re.match(regex, line):
                    z += [ float(line.split()[-2])/1E9 ]
    if debug:
        print((z, np.mean(z)))
    if rtn_global_mean:
        rtn_value = np.mean(z)
    if rtn_avg_3D_concs:
        rtn_value = get_CH4_3D_concenctrations( z )
    # return value for UK latitude
    if (not rtn_global_mean) and (not rtn_avg_3D_concs):
        rtn_value = np.array( z )[::4].mean()
    return rtn_value


# ----
# 1.14 - Extract OH and HO2 for a given ctm.bpch file
# ----
def get_OH_HO2( ctm=None, t_p=None, a_m=None, vol=None, \
            wd=None, HOx_weight=False, res='4x5', scale=1E5, trop_limit=True, \
             molec_weight=True, time_averaged=True, debug=False ):
    """
    Get OH/HO2 concentrations from ctm.bpch/NetCDF of GEOS-Chem output
    """
    if debug: print(('get_OH_HO2 called for ', wd))
    # --- Set specs, get constants, and extract output variables
    specs = ['OH','HO2']
    AVG= constants('AVG')
    RMM_air=constants('RMM_air')
    # Load arrays if not provided...
    if not isinstance(t_p, np.ndarray):
        if pygchem.__version__ == '0.2.0':
            t_p = get_gc_data_np( ctm, spec='TIMETROP', category='TIME-TPS', \
                debug=debug)
        else:
            print('WARNING!!! - provide time in trop diag. ')
            t_p = get_GC_output( wd, vars=['TIME_TPS__TIMETROP'], \
                trop_limit=trop_limit )
    if not isinstance(a_m, np.ndarray):
        if pygchem.__version__ == '0.2.0':
            a_m = get_air_mass_np( ctm, debug=debug )
        else:
            print('WARNING!!! - provide air mass diag. ')
            a_m = get_GC_output( wd, vars=['BXHGHT_S__AD'],  \
                trop_limit=trop_limit, dtype=np.float64)
    if not isinstance(vol, np.ndarray):
        if pygchem.__version__ == '0.2.0':
            vol = get_volume_np( ctm, res=res, debug=debug)
        else:
            print('WARNING!!! - provide vol diag. ')
            vol = get_volume_np( wd=wd, res=res, trop_limit=trop_limit, \
                debug=debug)
    # --- Extract OH and HO2 Data ( OH in [molec/cm3], HO2 in [v/v])
    if pygchem.__version__ == '0.2.0':
        OH, HO2 = [get_gc_data_np( ctm, \
            i, category='CHEM-L=$') for i in specs ]
    else:
        OH, HO2 = get_GC_output( wd, trop_limit=trop_limit, \
            vars=['CHEM_L_S__'+i for i in specs], r_list=True )
    # Mask for troposphere.
    OH, HO2  = mask4troposphere( [OH, HO2 ], t_ps=t_p,  \
        use_time_in_trop=True, multiply_method=True)
    # --- Process data
    molecs = ( ( (a_m*1E3) / RMM_air ) * AVG )   # molecules
    moles =  a_m*1E3 / RMM_air # mols
    # Only consider troposphere
    print([ i.shape for  i in (molecs, a_m, vol, moles)  ])
    molecs, a_m, vol, moles = mask4troposphere( \
        [molecs, a_m, vol, moles ], t_ps=t_p,  \
        use_time_in_trop=True,  multiply_method=True)
    if debug:
        vars2debug_prt = [ OH, HO2, molecs, moles, a_m, vol ]
        print([ (i.shape, np.mean(i) ) for i in vars2debug_prt ])
    # convert HO2 [v/v] to [molec/cm3]
    HO2 = convert_v_v_2_molec_cm3( HO2, a_m=a_m, vol=vol, mols=moles )
    # Remove invalid values
    HO2, OH  = [ np.ma.masked_invalid( i) for i in (HO2, OH)   ]
    HO2, OH  = [ np.ma.masked_where( i<0, i) for i in (HO2, OH)   ]
    # Average over provided timesteps ( 4th dimension )
    if time_averaged:
        HO2, OH, molecs, vol = [ i.mean(axis=-1) \
            for i in (HO2, OH, molecs, vol) ]
    if debug:
        print([ ( np.ma.sum(i), np.ma.mean(i) ) for i in (HO2, OH) ])
        print(('volume weighted: ', [ np.ma.sum( i *vol) / np.ma.sum(vol) \
            for i in (HO2, OH) ]))
    if HOx_weight: # weigh by [HO]+[HO2] molecules
        HOx = HO2 + OH
        HO2, OH  = [ np.ma.sum( ( i* HOx )) /np.ma.sum(HOx) for i in (HO2, OH) ]
        if debug:
            print([ i.shape for i in (OH, HO2, moles, vol, HOx) ])
            print(('HOx weighted: ',HO2, OH))
    elif molec_weight: # weight by # of molecules
        HO2, OH  = [ ( i*molecs).sum() /molecs.sum() for i in (HO2, OH) ]
    else: # Volume weight
#       HO2, OH = [ np.ma.sum( i *vol) / np.ma.sum(vol)  for i in HO2, OH ]
        print('Please specify weighting in get_OH_HO2() ')
        sys.exit()
    # Scale to set value ( e.g. 1E6 )
    HO2, OH = [i/scale for i in (HO2, OH) ]
    return OH, HO2


# ----
# X.XX - Process species for given arrays to (v/v) in respective scale + DU
# ----
def process_data4specs( specs=None, titles=None, wds=None, res='4x5', \
        diff=True, pcent=True,
#         ver='1.6',
#        just_bcase_std=True, preindustrial=False, just_bcase_no_hal=False,\
        tight_constraints=True, trop_limit=True,
        NOy_family=False, Bry_family=False, Iy_family=False,
        rtn_specs=False, rtn_titles=False, debug=False ):
    """
    Return species values in v/v and DU. Also return datetimes for CTM output and time in
    troposphere diagnostics

    Parameters
    -------
    specs (list): list of specs to extract
    wds (list): list of working directories containing model output files
    titles (list): reference names for working directories


    Returns
    -------

    Notes
    -----

     - This function is fairly inefficient, but is compbatible with pygchem 0.2.0 and 0.3.0
     ( Since the above comment, the function has been updated to tak a list of
      working directories (wds) and  )

    """
    # Get runs data and descriptors - N/A (moved this to user specific module)
#    if isinstance(
#    wds, titles = MUTD_runs( titles=True, just_bcase_std=just_bcase_std, \
#        res=res, ver=ver, just_bcase_no_hal=just_bcase_no_hal, \
#        preindustrial=preindustrial )
#    if debug:
#        print wds, titles
#    if preindustrial:
#        # Force 'Cl+Br+I (PI)' to be base case and 'Cl+Br+I' to be second entry
#        wds = [wds[3],  wds[1] ]
#        titles = [ titles[3], titles[1] ]
    logging.info('process_data4specs called for wds={},{}'.format(str(wds),
        str(titles)) )
    if debug:
        print((wds, titles))

    # --- Previous pygchem approach <= REDUNDENT
    if pygchem.__version__ == '0.2.0':
        runs  = [ wd2ctms( wd, debug=debug ) for wd in wds ]

        # Get species time Tropopause diagnostic
        t_ps  = [  np.concatenate(  [ get_gc_data_np( ctm, spec='TIMETROP', \
            category='TIME-TPS') for ctm in ctms ] , axis=3 ) \
            for ctms in [r[0] for r in runs] ]

        # get molecs in troposphere
        molecs  = [ arr*1E3/constants( 'RMM_air')*constants('AVG') \
            for arr in [np.concatenate([ get_air_mass_np(ctm) \
            for ctm in ctms ], axis=3 ) for ctms in [r[0] for r in runs] ] ]

        res= runs[0][1]
        s_area  = get_surface_area( res=res, debug=debug )[:,:,0]

        # Extract data for arrays once
        Vars = [ [ np.concatenate( [ get_gc_data_np( ctm, spec) \
            for ctm in ctms], axis=3) for ctms in [r[0] for r in runs] ] \
            for spec in specs ]
        del runs

        # convert to np arrays
        Vars, molecs, t_ps = [ np.ma.array(i) for i in (Vars, molecs, t_ps) ]

        # limit to GEOS-Chem's chemical troposphere
        Vars, molecs = [ i[...,:38,:] for i in (Vars, molecs) ]

        # Get GEOS-Chem datetime
        dlist = [ j for k in [get_gc_datetime(ctm )
            for ctm in  runs[0][0] ] for j in k ]
        dlist = sorted( set([  i[0] for i in dlist ])  )

    # ---- Updated pygchem approach, using iris cubes
    else:

        # Get GC dates as datetimes
        dlist = get_gc_datetime( wd=wds[-1] )

        # Get species time Tropopause diagnostic
        t_ps = [ get_GC_output( wd, vars=['TIME_TPS__TIMETROP'], \
            trop_limit=trop_limit ) for wd in wds ]

        # Get air mass in kg
        a_m = [ get_GC_output( wd, vars=['BXHGHT_S__AD'], \
            trop_limit=trop_limit, dtype=np.float64) for wd in wds ]

        # Get molecs in troposphere
        molecs = [i*1E3/constants( 'RMM_air')*constants('AVG') for i in a_m ]

        # Get surface area
        s_area = get_surface_area( res=res, debug=debug )[:,:,0]

        # Get mixing ratio
        Vars = [ get_GC_output( wd, vars=['IJ_AVG_S__'+i for i in specs ], \
            trop_limit=trop_limit ) for wd in wds ]
#        print [i[0].shape for i in Vars, molecs, t_ps ]
        print([i.shape for i in Vars + molecs + t_ps ])

        # convert to np arrays
        Vars, molecs, t_ps = [ np.ma.concatenate([ii[...,None] for ii in i], \
            axis=-1) for i in (Vars, molecs, t_ps) ]
        logging.debug( *[i.shape for i in (Vars, molecs, t_ps) ] )

        # restore to shape used for previous analysis
        molecs, t_ps= [ np.rollaxis( i, -1, 0 ) for i in (molecs, t_ps) ]
        logging.debug( 'prior to roll', *[i.shape for i in (Vars, molecs, t_ps) ])
        Vars=np.rollaxis( Vars, -1, -5 )
        logging.debug( 'post roll', *[i.shape for i in (Vars, molecs, t_ps) ])

    logging.debug( *[ ( i.shape, i.sum() ) for i in (Vars, molecs, t_ps) ] )

    # apply tight constraints to troposphere? (
    if tight_constraints:
        t_ps = np.ma.masked_where( t_ps != 1, t_ps )
    logging.debug( *[ ( i.shape, i.sum() ) for i in (Vars, molecs, t_ps) ] )

#    Vars, molecs = [ i*t_ps[None,...] for i in Vars, molecs ]
    # remove stratospheric values
    Vars = Vars*t_ps[None,...]
    molecs  =  (molecs*t_ps)[None,...]
    logging.debug( *[ ( i.shape, i.sum() ) for i in (Vars, molecs, t_ps) ] )

    # Get DU values for each array (2D not 3D )
    # molecules O3 in trop. summed
    DUarrs = Vars*molecs
    logging.debug( *[ ( i.shape, i.sum() ) for i in [DUarrs] ] )
    DUarrs = DUarrs.sum(axis=-2)
    # Kludge back to 4D  ( this is due to the conversion to NetCDF for 0.3.0 )
    DUarrs=DUarrs[...,None,:]

    logging.debug( [ ( i.shape, i.sum() ) for i in [DUarrs] ] )

    # adjust to per unit area ( cm3 )
    tmp_s_area = s_area[None, None,...]
    tmp_s_area = tmp_s_area[...,None,None]
    DUarrs =  DUarrs/ tmp_s_area
    logging.debug( *[ (i.shape, i.sum()) for i in (DUarrs, tmp_s_area, s_area) ])

    # convert to DU
    DUarrs = DUarrs/constants('mol2DU')
    logging.debug( *[ (i.shape, i.sum()) for i in (DUarrs, tmp_s_area, s_area) ])

#    if debug:
#        for n in range( len(specs) ):
#            for nn in range(2):
#                print n,nn
#                print '!'*30, (DUarrs[n,nn,...]*tmp_s_area[0,0,...]).sum()/  \
#                    tmp_s_area[0,0,...].sum()

    # ---  Add familys to arrays by conbination of tracers
    # Shape of Vars, DUarrs = [(65, 2, 72, 46, 38, 12), (65, 2, 72, 46, 1, 12)]
    # (NOy_family, Bry_family, Iy_family )
    def add_family2arrays( fam=None, Vars=None, DUarrs=None,
                I=False, N=False, Br=False, specs=None ):

        # get species in family
        d = { 'NOy':'N_specs', 'Iy':'Iy',  'Bry':'Bry' }
        fam_specs = GC_var( d[fam] )
        # Kludge - only consider the specs available in the NetCDF
        fam_specs = [i for i in fam_specs if (i in specs) ]
        logging.debug( [ i.shape for i in (Vars, DUarrs)], fam, d[fam], \
            fam_specs )

        #  find indices and conctruct dictionary
        fam_specs = [(i,n) for n,i in enumerate( specs ) if ( i in fam_specs ) ]
        fam_specs = dict( fam_specs )

        # Add family name to specs
        specs += [ fam ]

        # Extract values and adjust to stiochmetry  ( Vars )
        fam = [ Vars[fam_specs[i],...]*spec_stoich(i, I=I, N=N, Br=Br) \
                for i in list(fam_specs.keys()) ]

        # sum species in family and add to returned array ( Vars )
        logging.debug( np.array( [np.array(i) for i in fam] ).shape )
        fam = np.ma.array( fam ).sum(axis=0)[None,...]
        logging.debug( *[i.shape for i in (fam, Vars) ] )
        Vars = np.ma.concatenate( (Vars, fam) , axis=0 )

        logging.debug( *[ i.shape for i in (Vars, DUarrs)] )
        del fam

        # sum species in family and add to returned array ( DUarrs )
        fam = [ DUarrs[fam_specs[i],...]*spec_stoich(i, I=I, N=N, Br=Br) \
                for i in list(fam_specs.keys()) ]

        # sum species in family and add to returned array ( DUarrs )
        fam = np.ma.array( fam ).sum(axis=0)[None,...]
        logging.debug( *[ i.shape for i in (Vars, DUarrs)] )
        DUarrs = np.ma.concatenate( (DUarrs, fam) , axis=0 )
        logging.debug( *[ i.shape for i in (Vars, DUarrs)] )
        del fam

        return Vars, DUarrs, specs

    logging.debug( *[ i.shape for i in (Vars, DUarrs)] )

    if NOy_family:
        Vars, DUarrs, specs = add_family2arrays(  fam='NOy', N=True,\
                Vars=Vars, DUarrs=DUarrs, specs=specs )
    if Bry_family:
        Vars, DUarrs, specs = add_family2arrays(  fam='Bry', Br=True, \
                Vars=Vars, DUarrs=DUarrs, specs=specs )
    if Iy_family:
        Vars, DUarrs, specs = add_family2arrays(  fam='Iy', I=True, \
                    Vars=Vars, DUarrs=DUarrs, specs=specs )
    logging.debug( *[ str(i.shape) for i in (Vars, DUarrs)] )

    # consider difference in v/v and DU
    if any( [len(i) != 2 for i in (wds, titles) ]):
        err_msg= 'WARNING diff/pcent calcuation require two arrays!'
        print(err_msg)
        logging.info(err_msg)
        sys.exit()

    if diff:
        if pcent:
            Vars, DUarrs = [ np.ma.array(i) for i in (Vars, DUarrs) ]
            Vars = (Vars[:,1,...] - Vars[:,0,...] )/ Vars[:,0,...] *100
            DUarrs = ( DUarrs[:,1,...] - DUarrs[:,0,...] ) / \
                DUarrs[:,0,...] *100
            Vars, DUarrs = [ np.ma.masked_invalid(i) for i in (Vars, DUarrs) ]

        else:
            Vars = Vars[:,1,...] - Vars[:,0,...]
            DUarrs = DUarrs[:,1,...] - DUarrs[:,0,...]
    else:
        Vars = Vars[:,1,...]
        DUarrs = DUarrs[:,1,...]
    logging.debug( *[ i.shape for i in (Vars, DUarrs)] )

    # Close/remove memory finished with
    del molecs, tmp_s_area, wds

    # return requested variables
    rtn_vars =[  Vars, DUarrs, dlist, t_ps.mean(axis=0) ]
    if rtn_specs:
        rtn_vars += [specs]
    if rtn_titles:
        rtn_vars += [titles]
    return rtn_vars

# ----
# X.XX
# ----
def get_HEMCO_output( wd=None, files=None, filename=None, vars=None, \
        use_netCDF=True):
    """
    Data extractor for hemco files and folders. You can specify either a
    working dir or a file to get the data from.

    Parameters
    -------
    wd (str): the directory to search for files in
    vars (None): hemco_file or file list
    files (None): hemco_file or file list

    Returns
    -------
    (list) of numpy arrays the size of the input vars list.

    Notes
    -----
    """
    logging.info("Called get hemco output.")

    # Allow single strings to be input instead of making it have to be a list.
    if isinstance(vars, str):
        vars = [vars]

    # If a filename is supplied put it into a list.
    if isinstance(files, str):
        filename=files
        files = [files]



    if not wd==None:
        fname = os.path.join(wd, "hemco.nc")
        if not os.path.isfile(fname):
            from .bpch2netCDF  import hemco_to_netCDF
            hemco_to_netCDF( wd, hemco_file_list = files )
            pass


        logging.debug("Looking for hemco data in {wd}".format(wd=wd))

        ### Need to confirm hemco file exsits before trying to open it..
        try:
            HEMCO_data = Dataset(fname, 'r')

            arr = []
            for var in vars:
                try:
                    arr.append( HEMCO_data.variables[var][:] )
                except:
                    logging.warning("Could not find {var} in {fname}"\
                                .format(var=var, fname=fname))

        except:
            logging.error("Could not open hemco data from {fn}"\
                    .format(fn=fname))

    elif not filename==None:

        logging.debug("Looking for hemco data in {file}".format(file=filename))

        HEMCO_data = Dataset(filename, 'r')
        arr = []
        for var in vars:
            try:
                arr.append( HEMCO_data.variables[var][:] )
            except:
                logging.warning("Could not find {var} in {fname}"\
                            .format(var=var, fname=filename))

    else:
        logging.error("No wd of filename given to get_hemco_output!")
        return

    if len(arr)==1:
        arr = arr[0]

    return arr;

# ----
# X.XX - Get var data for model run
# ----
def get_GC_output( wd, vars=None, species=None, category=None, r_cubes=False, \
        r_res=False, restore_zero_scaling=True, r_list=False, trop_limit=False,\
        dtype=np.float32, use_NetCDF=True, verbose=False, debug=False):
    """
    Data extractor for GEOS-Chem using PyGChem (>= 0.3.0 ). ctm.bpch files are extracted
    for a given directory, with only the specific category and species returned. This can
    either be as a Iris Cube (retaining metadata) or as a numpy array.

    Parameters
    ----------
    vars (list): variables to extract (in NetCDF form, e.g. ['IJ_AVG_S__CO'])
     ( alterately provide a single species and category through named input variables )
    species (str): species/tracer/variable (gamap) name
    category (str): diagnostic category (gamap) name
    r_cubes (boolean): To return Iris Cubes, set to True
    r_res (boolean): To return resolution of model NetCDF set to True
    r_list (boolean): To return data as list of arrays rather than a single array
    restore_zero_scaling(Boolean): restores scale to ctm.bpch standard (e.g. v/v not pptv)
    trop_limit(boolean): limit to "chemical troposphere" (level 38 of model)
    dtype (type): type of variable to be returned
    use_NetCDF(boolean): set==True to use NetCDF rather than iris cube of output
    verbose (boolean): legacy debug option, replaced by python logging
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    (np.array) of requested output or object of data (iris cube)

    Notes
    -----
     - Credit for PyGChem: Ben Bovy - https://github.com/benbovy/PyGChem
     - Examples and use of pygchem is discussed on Ben Bovy's GITHib
     ( https://github.com/benbovy/PyGChem_examples/blob/master/Tutorials/Datasets.ipynb )
     - This replaces the now defunct AC_tools functions: open_ctm_bpch and get_gc_data_np
     - For simplicity use variable names (species, category) as used in
      the iris cube ( e.g. IJ_AVG_S__CO). if variable is unknown, just
      print full dataset extracted to screen to see active diagnostics.
     - Species and category variables are maintained ( and translated ) to allow for
      backwards compatibility with functions written for pygchem version 0.2.0
    """

# bjn
# This function is not completly clear to me, and could do with a re-write
# The try command would probably be useful here for large parts.
# logging would also be good for replacing debug.
    logging.info("Called get_GC_output")
    logging.debug("get_GC_output inputs:")
    logging.debug(locals())

    if not isinstance( vars, type(None) ):
        logging.info( 'Opening >{}<, for var: >{}<'.format(wd,','.join(vars)) + \
            '(extra) gamap variables provided: >{}< + >{}<'.format(category,species) )

    # Also option to use gamap names ( species  + category ) to and func converts these
    # to iris cube names
    if any( [ (not isinstance(i, type(None) )) for i in (species, category) ] ):
        # convert to Iris Cube name
        if (category == None) and ( vars ==  None ):
            category = "IJ-AVG-$"
        if (species == None) and ( vars ==  None ):
            species =  'O3'

        # remove scaling for 'IJ-AVG-$' - KLUDGE - needed for all ?
        if category == 'IJ-AVG-$':
            category = diagnosticname_gamap2iris( category )

        # setup var for Iris Cube, then remove known rm. chars.
        var = category+'__'+species
        vars = [ var.replace('-', '_').replace('$', 'S') ]

    else:
        # Get default settings for reader
        if isinstance(vars, type(None)):
            vars = [ 'IJ_AVG_S__O3'  ]

    # Work with NetCDF. Convert ctm.bpch to NetCDF if not already done.
    if use_NetCDF:

        # Check for compiled NetCDF file
        # If not found, create NetCDF file from ctm.bpch files
        import os.path
        fname = os.path.join(wd, 'ctm.nc')
        if not os.path.isfile(fname):
            from .bpch2netCDF  import convert_to_netCDF
            convert_to_netCDF( wd )

        logging.debug("Opening netCDF file {fname}".format(fname=fname))
        # "open" NetCDF + extract requested variables as numpy arr.
        netCDF_data = Dataset( fname, 'r' )
        arr = []
        for var in vars:
            try:
                logging.debug("opening variable {var}".format(var=var))
                var_data = netCDF_data.variables[var]
            except:
                logging.warning("Variable {var} not found in netCDF"\
                    .format(var=var))
                logging.warning("Will attempt renaming")
                try:
                    abrv_var = get_ctm_nc_var( var )
                    var_data = netCDF_data.variables[abrv_var]
                except KeyError:
                    logging.error("Renamed variable {var} not found in netCDF"\
                        .format(var=var) )


####################################################################################
#####--- bjn - re-wrote (above) to make more understandable ---###
#
#            with Dataset( fname, 'r' ) as rootgrp:
#                try:
#                    arr = [ np.array(rootgrp[i]) for i in vars ]
#                except IndexError:
#                    if verbose:
#                        print 'WARNING: VAR NOT IN NETCDF '
#                        print 'IndexError was found either due to lack of ' + \
#                            'variable in NetCDF file or error in name' + \
#                            ' species import from *.dat. Will attempt renaming'
#                    arr =[]
#                    for var_ in vars:
#                        if verbose:
#                            print 'Atempting indiviudual extraction of: ', var_
#                        try:
#                            arr += [ np.array( rootgrp[var_] ) ]
#                            if verbose:
#                                print 'successfull indiv. extraction of: ',var_
#                        except IndexError:
#                            logging.error('failed to find {var}'.format(var=var_))
##                            raise ValueError('failed to find {var} in netCDF file'\
##                                    .format(var=var_))
#
#
#                            # If not found try an abreviation
#                            abrv_var_ = get_ctm_nc_var(var_)
#                            arr += [ np.array( rootgrp[ abrv_var_ ] )]
#                            if verbose:
#                                print 'using {} instead of {}'.format( \
#                                     abrv_var_, var_ )
#
##################################################################################


#                # files are stored in NetCDF at GC scaling.
#                # ( This is different to ctm.bpch, rm for back compatibility. )

############################################################################
#    # This is not in a working state currently - needs work
            if restore_zero_scaling:
                try:
                    var_data = np.divide(var_data,get_unit_scaling(var_data.ctm_units))
                except:
                    logging.warning("Scaling not adjusted to previous approach")

            arr.append(var_data[:])

####--- The above re-write does not work so still using old version ---###

# Temp fix for out of place code if true:
#                arr.append(var_data[:]) # temp fix
#        if True:# temp fix
#                rootgrp = netCDF_data #temp fix
#
#                if restore_zero_scaling:
#                    try:
#                        arr =[ arr[n]/get_unit_scaling( rootgrp[i].ctm_units ) \
#                            for n, i in enumerate( vars ) ]
#                    except:
#                        print 'WARNING: SCALING NOT ADJUSTED TO' + \
#                            ' PREVIOUS APPROACH'
#############################################################################


    # Use Iris cubes via PyGChem to extract ctm.bpch files
    else:

        # Get files in dir ( more than one? )
#        fns = sorted( glob.glob( wd+ '/*ctm*' ) )
#        if len(fns) == 0:
#            fns = glob.glob(wd + '*trac_avg*')
#            print 'using *trac_avg* bpch name convention: ', fns

#        if debug:
#            print fns

        # Load files into Iris Cube
#        print 'WARNING - with ctm.bpch files, all variables are loaded.'+\
#            'Convert to NetCDF or HDF for speed up or use use_NetCDF=True)'
#        cubes = datasets.load( fns, vars )

        # If no data extracted, print our variables
#        try:
#            [ i[0].data for i in cubes ]
#        except:
#            print datasets.load( fns[0] )
#            print 'WARNING: no vars found for >{}<'.format( ','.join(vars) )
#            sys.exit( 0 )

        # Temporary fix for back compatibility:
        # Just extract as numpy

#        if not r_cubes:

            # Extract data
#            try:
#                arr = [ cubes[i].data for i in range( len(vars) ) ]
#            except:
#                print 'WARNING: length of extracted data array < vars'
#                print 'vars: >{}<'.format( ','.join(vars) )
#                sys.exit( 0 )

            #  restore to zero scaling (v/v instead of pptv etc ) - only for GC tracers
#            if restore_zero_scaling:
#                if (category == 'IJ_AVG_S') or ('IJ_AVG_S' in vars[0] ):
#                    print [ cubes[i].attributes['ctm_units'] for i in range( len(vars) ) ]
#                    arr = [ arr[n]/get_unit_scaling( cubes[n].attributes['ctm_units'])
#                             for n, var in enumerate( vars ) ]
#            del cubes
        logging.error( 'WARNING this approach has been removed due to time cost')
        sys.exit( 0 )

    # Process extracted data to gamap GC format and return as numpy
    if not r_cubes:

        # Limit to GEOS-Chem "chemical troposphere'
        if trop_limit:
            arr = [ i[...,:38] for i in arr]

        # Convert to GC standard 4D fmt. - lon, lat, alt, time
        if len((arr[0].shape)) == 4:
            logging.info('prior to roll axis: {}'.format(*[i.shape for i in arr]) )
            arr = [np.rollaxis(i,0, 4) for i in arr]
            logging.info( 'post roll axis: {}'.format(*[i.shape for i in arr]) )

        # Convert to GC standard 3D fmt. - lon, lat, time
        # two reasons why 3D (  missing time dim  or  missing alt dim )
        # <= update, there must be a better gotcha than this...
        if ( (len((arr[0].shape)) == 3 ) \
            # -- '4x5'
            and ( (72,46,47) != arr[0].shape ) \
            and ( (72,46,38) != arr[0].shape ) \
            # also consider for vertical levels=72 (full_vertical_grid=True)
            and ( (72,46,72) != arr[0].shape ) \
            # and the prod/loss reduced grid
            and ( (72,46,59) != arr[0].shape ) \
            # -- '2x2.5'
            and ( (144,91,47) != arr[0].shape ) \
            and ( (144,91,38) != arr[0].shape ) \
            # -- '0.25x0.3125':
            and ( (177,115,47) != arr[0].shape ) \
            and ( (177,115,38) != arr[0].shape ) \
            # -- '0.25x0.3125_CH':
            and ( (225,161,47) != arr[0].shape ) \
            and ( (225,161,38) != arr[0].shape ) \
            # -- '0.25x0.3125_WA':
            and ( (145,89,47) != arr[0].shape ) \
            and ( (145,89,38) != arr[0].shape ) \
            # -- '0.25x0.3125_WA':
            and ( (145,133,47) != arr[0].shape ) \
            and ( (145,133,38) != arr[0].shape ) \
            # -- '0.5x0.625' - SA grid
            and ( (121,81,47) != arr[0].shape ) \
            and ( (121,81,38) != arr[0].shape ) ):

            logging.info('prior roll axis: {}'.format(*[str(i.shape) \
                for i in arr]))
            arr = [np.rollaxis(i,0, 3) for i in arr]
            logging.info('post roll axis: {}'.format(*[str(i.shape) \
                for i in arr]))

        # --- loop variables post processing and force inclusions of time dim if applicable
        need_time = ['IJ_AVG', 'GMAO', 'BXHGHT', 'TIME_TPS_', 'PORL_L_S_']
        for n, var in enumerate( vars ):

            # Add altitude dimension to 2D (lon, lat)
            # a bug might occur for emission etc ( where lon, lat, time are dims )
            if len((arr[n].shape)) == 2:
                arr[n] =arr[n][...,None]

            # ensure output for categories in need_time list have 4 dims
            if any([(i in var) for i in need_time]) and (len(arr[n].shape) == 3):
                arr[n] = np.expand_dims( arr[n], -1 )

            # Convert type if dtype not float32
            # ( needed for some arrays e.g. air mass )
            if dtype != np.float32:
                arr[n] = arr[n].astype( dtype )

        # --- concatenate
        # For multiple vars, concatenate to var, lon, lat, lat, time
        if len(vars) >1:
            arr = np.concatenate( [ i[None,...] for i in arr ], axis=0 )
        else:
            arr =arr[0]

    # Get res by comparing 1st 2 dims. against dict of GC dims.
    if r_res:
        try:
            res=get_dims4res( r_dims=True, trop_limit=trop_limit, \
                just2D=True )[arr.shape[:2]]
        except KeyError:
            logging.info('resolution/array shape ({}) not in dictionary:'.format(arr.shape))
            sys.exit()

    if r_list:
        # Make sure returned type is list of arrays
        if len( vars ) > 1:
            arr = [ arr[i,...] for i in range( len(vars) ) ]
        else:
            arr = [ arr ]

    # Sort output - return Cubes?
    if r_cubes:
        output =  cubes
    else:
        output = arr
#        return cubes.data

    # Return model resolution?
    if r_res:
        return output, res
    else:
        return output

# ----
# 1.24 - Get gc resolution from ctm.nc
# ---
def get_gc_res( wd, filename='ctm.nc' ):
    """
    Extract resolution of GEOS-Chem NetCDF

    Parameters
    ----------
    filename (Str): name of NetCDF file (e.g. ctm.nc or ts_ctm.nc)
    wd (str): the directory to search for file in

    Returns
    -------
    (str)
    """
    # create NetCDf if not created.
    fname = wd+ '/'+filename
    if not os.path.isfile(fname):
        from .bpch2netCDF  import convert_to_netCDF
        convert_to_netCDF( wd, filename=filename )

    # "open" NetCDF + extract time
    with Dataset( fname, 'r' ) as rootgrp:
        lon = rootgrp['longitude']
        lat = rootgrp['latitude']
#            lvls = rootgrp['model_level_number']
        lat, lon = [ np.array(i) for i in (lat, lon) ]

    # compare with dictionary to get resoslution
    dims = (len(lon),len(lat))
    res = get_dims4res( r_dims=True, just2D=True )[dims]
    if isinstance(res, type(None)):
        logging.error("Could not find resolution for run in {wd}".format(wd=wd))

    return res

# ----
# X.XX - Get surface area ( m^2 ) for any global resolution
# ----
def calc_surface_area_in_grid( res='1x1', lon_e=None, lat_e=None, \
        lon_c=None, lat_c=None, debug=False ):
    """
    Use GEOS-Chem appraoch for GEOS-Chem grid surface areas.

    Parameters
    -------
    res (str): the resolution if wd not given (e.g. '4x5' )
    debug (boolean): legacy debug option, replaced by python logging
    lon_c (array): centres of longitude boxes
    lat_c (array): centres of latitude boxes
    lon_e (array): edges of longitude boxes
    lat_e (array): edges of latitude boxes

    Returns
    -------
    (array)

    Notes
    -----
     - Adapted for python from Fortrain in GEOS-Chem's grid_mod.F
        Credit: Bob Yantosca
        Original docs from ( grid_mod ):
    !======================================================================
    ! Compute grid box surface areas (algorithm from old "input.f")
    !
    ! The surface area of a grid box is derived as follows:
    !
    !    Area = dx * dy
    !
    ! Where:
    !
    !    dx is the arc length of the box in longitude
    !    dy is the arc length of the box in latitude
    !
    ! Which are computed as:
    !
    !    dx = r * delta-longitude
    !       = ( Re * cos[ YMID[J] ] ) * ( 2 * PI / IIIPAR )
    !
    !    dy = r * delta-latitude
    !       = Re * ( YEDGE[J+1] - YEDGE[J] )
    !
    ! Where:
    !
    !    Re         is the radius of the earth
    !    YMID[J]    is the latitude at the center of box J
    !    YEDGE[J+1] is the latitude at the N. Edge of box J
    !    YEDGE[J]   is the latitude at the S. Edge of box J
    !
    ! So, the surface area is thus:
    !
    !    Area = ( Re * cos( YMID[J] ) * ( 2 * PI / IIIPAR ) *
    !             Re * ( YEDGE[J+1] - YEDGE[J] )
    !
    !    2*PI*Re^2    {                                            }
    ! = ----------- * { cos( YMID[J] ) * ( YEDGE[J+1] - YEDGE[J] ) }
    !     IIIPAR      {                                            }
    !
    ! And, by using the trigonometric identity:
    !
    !    d sin(x) = cos x * dx
    !
    ! The following term:
    !
    !    cos( YMID[J] ) * ( YEDGE[J+1] - YEDGE[J] )
    !
    ! May also be written as a difference of sines:
    !
    !    sin( YEDGE[J+1] ) - sin( YEDGE[J] )
    !
    ! So the final formula for surface area of a grid box is:
    !
    !            2*PI*Re^2    {                                     }
    !    Area = ----------- * { sin( YEDGE[J+1] ) - sin( YEDGE[J] ) }
    !              IIIPAR     {                                     }
    !
    !
    ! NOTES:
    ! (1) The formula with sines is more numerically stable, and will
    !      yield identical global total surface areas for all grids.
    ! (2) The units are determined by the radius of the earth Re.
    !      if you use Re [m], then surface area will be in [m2], or
    !      if you use Re [cm], then surface area will be in [cm2], etc.
    ! (3) The grid box surface areas only depend on latitude, as they
    !      are symmetric in longitude.  To compute the global surface
    !      area, multiply the surface area arrays below by the number
    !      of longitudes (e.g. IIIPAR).
    ! (4) At present, assumes that GEOS-Chem will work on a
    !      Cartesian grid.
    !
    ! (bmy, 4/20/06, 2/24/12)
    !======================================================================
    """
    logging.info('called calc surface area in grid')
    # Get latitudes and longitudes in grid
    if any([isinstance(i, type(None)) for i in (lon_e, lat_e,) ]):
        lon_e, lat_e, NIU = get_latlonalt4res( res=res, centre=False )
    if any([isinstance(i, type(None)) for i in (lon_c, lat_c,) ]):
        lon_c, lat_c, NIU = get_latlonalt4res( res=res, centre=True )
    # Set variables values
    PI_180 = np.pi / 180.0
    Re = np.float64( 6.375E6 ) # Radius of Earth [m]
#    lon_dim = get_dims4res(res=res)[0]
    lon_dim = len(lon_c)
    lon_degrees = float( lon_dim )
    # Loop lats and calculate area
    AREA = []
    for n, lat_ in enumerate( lat_e[:-1] ):
        # Lat at S and N edges of 1x1 box [radians]
        S = PI_180 * lat_e[n]
        N = PI_180 * lat_e[n+1]
        # S to N extent of grid box [unitless]
        RLAT    = np.sin( N ) - np.sin( S )
        # grid surface area [m2] (see [GEOS-Chem] "grid_mod.f" for algorithm)
        AREA += [ 2.0 * np.pi * Re * Re / lon_degrees  * RLAT ]
    AREA = np.array( AREA )
    if debug:
        print(AREA)
        print([ (i.shape, i.min(),i.max() ) for i in [ AREA ] ])
    # Convert to 2D array / apply to all longitudes
    AREA = np.array( [ list( AREA ) ] * int(lon_dim) )
    return AREA

# ----
# X.XX - Process species for given family arrays to (v/v)
# ----
def get_chem_fam_v_v_X( wd=None, fam='Iy', res='4x5', ver='3.0' , specs=None, \
    trop_limit=True, N=False, I=False, Cl=False, Br=False, t_ps=None, a_m=None,\
    vol=None, verbose=True, rm_strat=False, debug=False ):
    """
    Return array of family in mols of X ( e.g. Cl, Br, I, N ) equiv. in mol/mol.

    Parameters
    ----------

    Returns
    -------

    Notes
    -----
     - Is this function just a double up of fam_data_extractor?
     (which is more up to date)
    """
    # Get species time Tropopause diagnostic
    if isinstance( t_ps, type(None) ) and rm_strat:
        t_ps = get_GC_output( wd=wd, vars=['TIME_TPS__TIMETROP'], \
            trop_limit=trop_limit )
    # Get (fam) specs if not given
    if isinstance( specs, type(None) ):
        # get species in family
        d = {
        'NOy':'N_specs', 'Iy':'Iy',  'Bry':'Bry', 'Cly':'Cly', 'HOx':'HOx',  \
        'SOx':'SOx', 'NOx':'NOx'
                }
        specs = GC_var( d[fam] )
    # Use correct stiochmetry
    # ( This is no longer required as ref_spec is passed, however it is retained
    # for back compatibility )    if fam =='Bry':
        Br=True
    if fam =='Iy':
        I=True
    if fam =='Cly':
        Cl=True
    if any( [( fam ==i) for i in  (' NOy', 'NOx') ] ):
        N=True
    # Get mixing ratio
    if fam == 'HOx':
        # OH ( in molec/cm3 )
        OH_arr = get_GC_output( wd=wd, vars=['CHEM_L_S__'+'OH'], \
                trop_limit=trop_limit )
        # HO2 ( in v/v )
        HO2_arr = [ arr, get_GC_output( wd=wd, vars=['CHEM_L_S__'+'HO2'], \
                trop_limit=trop_limit ) ]
        # Convert to  v/v
        HO2_arr = convert_v_v_2_molec_cm3( [HO2_arr], a_m=a_m, vol=vol, wd=wd )
        HO2_arr = HO2_arr[0]
        # combine
        arr = OH_arr + HO2_arr
    else: # Just extract v/v
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ],
            trop_limit=trop_limit, r_list=True )
    # Adjust to stiochmetry  ( Vars )
    arr = [ arr[n]*spec_stoich(i, ref_spec=fam) \
        for n,i in enumerate( specs) ]
    logging.debug('shapes: {}'.format(*[i.shape for i in arr]) )
    logging.debug( 'arr len={}, sum={}'.format(len(arr), np.ma.sum(arr)) )
    logging.debug('specs={}'.format(specs) )
    # Sum over stiochmertically adjusted list of specs
    arr = np.array( arr ).sum(axis=0)
    # Remove stratosphere by multiplication of time in trop. diag.
    if rm_strat:
        arr = mask4troposphere( [arr], t_ps=t_ps )[0]
    return arr, specs


# ----
# X.XX - Convert v/v array to DU array
# ----
def convert_v_v_2_DU( arr, wd=None, a_m=None, trop_limit=True, s_area=None, \
        molecs=None, verbose=True, debug=False):
    """
    Convert a 4D array of v/v for species (or family) to  DU

    Parameters
    -------

    Returns
    -------

    Notes
    -----
    """
    # Get DU values for each array (2D not 3D )
    if isinstance( molecs, type(None) ):
        # If 'a_m' not given, get air mass ('a_m') in kg
        if isinstance( a_m, type(None) ):
            a_m = get_GC_output( wd=wd, vars=['BXHGHT_S__AD'],
                trop_limit=trop_limit, dtype=np.float64)
        # Get molecs in troposphere
        molecs = a_m*1E3/constants( 'RMM_air')*constants('AVG')
    # Get surface area
    if isinstance( s_area, type(None) ):
        s_area = get_surface_area( res=res, debug=debug )
    # Molecules O3 in trop. summed
    DUarrs = arr*molecs
    logging.debug( [ (i.shape, i.sum()) for i in [DUarrs, s_area] ])
    # sum over altitude in 4D array ( lon, lat, alt, time )
    DUarrs = DUarrs.sum(axis=-2)
    logging.debug( [ (i.shape, i.sum()) for i in [DUarrs, s_area] ])
    # adjust to per unit area ( cm3 )
    DUarrs =  DUarrs/ s_area
    logging.debug( [ (i.shape, i.sum()) for i in (DUarrs, tmp_s_area,s_area)] )
    # convert to DU
    DUarrs = DUarrs/constants('mol2DU')
    return DUarrs


# ----
# X.XX - Get common GC diagnostic arrays
# ----
def get_common_GC_vars( wd=None, trop_limit=True, res='4x5', \
        verbose=True, debug=False):
    """
    Returns t_ps, a_m, molecs, s_area

    Parameters
    -------

    Returns
    -------

    Notes
    -----
     - This appraoch is taken to avoid circular calls + reduces code repitions
    """
    # Get species time Tropopause diagnostic
    t_ps = get_GC_output( wd=wd, vars=['TIME_TPS__TIMETROP'], \
            trop_limit=trop_limit )
    # Get air mass in kg
    a_m = get_GC_output( wd=wd, vars=['BXHGHT_S__AD'],
        trop_limit=trop_limit, dtype=np.float64)
    # Get molecs in troposphere
    molecs = a_m*1E3/constants( 'RMM_air')*constants('AVG')
    # Get surface area
    s_area = get_surface_area( res=res, debug=debug )
    return t_ps, a_m, molecs, s_area


# ----
# X.XX - Get 3D CH4 concentrations
# ----
def get_CH4_3D_concenctrations( z, res='4x5', trop_limit=True, debug=False ):
    """
    Takes monthly ( or any equllay spaced output) CH4 concentrations from geos.log
    files. 4 value are given per monthly file, split by laititude, as list "z"

    Which apears in GC output ( geos.log) as: '
    CH4 (90N - 30N) :  X.X [ppbv]
    CH4 (30N - 00 ) :  X.X [ppbv]
    CH4 (00  - 30S) :  X.X [ppbv]
    CH4 (30S - 90S) :  X.X [ppbv]   '

    NOTE:
     - this programme is typically called with z in units of v/v, not ppbv
    """
    # latitudes between which CH4 conc is given
    lats = [90, 30, 0, -30, -90][::-1]
    # make a array of zeros, including time dimension
    arr_shape  = get_dims4res( res=res, trop_limit=trop_limit ) + (len( z )/4, )
    arr  = np.zeros( arr_shape )
    # Get an average of each latitude band ( 4 outputs per geos.log file )
    z = np.array( [ z[i::4] for i in range( 4 ) ] )
    # Also reverse list to allow for increasing indice (for latitude )
    z = z[::-1]
    # Loop time stamps ( 4th dimension )
    for t in range( len( z[0,:] ) ):
        # Apply these values to the GC gird at given resolution
        for n, lat in enumerate( lats[:-1] ):
            lat_0 =  get_gc_lat( lats[n], res=res)
            lat_1 =  get_gc_lat( lats[n+1], res=res)
            arr[:,lat_0:lat_1,:,t] = z[n,t]
        # Check all values have been filled
        if debug:
            print((z.shape, arr.shape, arr[ arr<0 ]))
    return arr


# ----
# X.XX - Get Strat-Trop exchange (from geos.log files )
# ----
def get_STRAT_TROP_exchange_from_geos_log( fn=None, ver='3.0', \
        rtn_date=False, rtn_Tg_per_yr=True, verbose=False, debug=False ):
    """
    Extract all tracer Stat-trop exchange values for a given geos.log file.
    These are then returned as a Pandas Dataframe

    Parameters
    -------

    Returns
    -------

    Notes
    -----
     - Works by extracting all lines between start ("Strat-Trop Exchange")
         and end ("================") of section.
     - file name (fn) is assumed to include directory as well as name
    """
    logging.info( 'get_STRAT_TROP_exchange_from_geos_log called for: '.format(\
        fn) )
    # --- Open the file
    file_ =  open( fn, 'rb' )
    # Read in just the TROP-STRAT exchange section
    start_line =  'Strat-Trop Exchange'
    end_line = '================'
    # --- Loop and extract lines of file with data on exchange
    readline = False
    lines = []
    for row in file_:
        # once at prod/loss section, start added to list
        if start_line in row:
            readline=True
        # if not at end of prod/loss section, add to list
        if end_line in row:
            readline=False
        if readline:
            try:
                lines.append( row )
            except:
                lines = [ row ]
    # --- Process extracted lines
    # remove starting lines
    headers = [ i.strip() for i in lines[5].split('    ') ]
    # remove end line
    lines.pop()
    # What data range is this?
    date_range = lines[3]
    # split into columns
    lines = [ i.split() for i in lines[6:] ]
    # - Kludge to remove double up in file read.
#    if len(lines) >103:
#        lines = lines[:103]
    TRAs = [ i[0].split(':')[0] for i in lines  ]
    # loop columns and extract data
    vars = []
    logging.debug( 'headers= {}, date range={}'.format( headers, date_range ))#, lines )
    # Extract data as floats by header
    vars = [ [ float( i[n+1]) for i in lines ] for n in range( len(headers)-1) ]
    # make a DataFrame of the output
    logging.debug( 'vars:{}'.format([ str(len(i)) for i in vars ]) )
    d = dict( list(zip(headers[1:], vars)) )
    df = pd.DataFrame(  d, index=TRAs )
    if rtn_Tg_per_yr:
        df = df['= [Tg a-1]' ]
    if rtn_date:
        return df, date_range
    else:
        return df


# ----
# X.XX - Get Wind direction from U and V vectors
# ----
def get_mod_WIND_dir(  sdate=datetime.datetime(2012, 8, 1, 0 ), \
            edate = datetime.datetime(2012, 8, 8, 0 ), loc='KEN', \
            scale=1, adjustby=0, period = 'summer', \
            vars = ('GMAO_UWND', 'GMAO_VWND'), \
            verbose=False, debug=False):
    """
    Extract synoptic wind direction

    NOTES:
     - this function was written to work with GEOS-Chem planeflight output
    (thus U/V vector variables are set to pf varaibles), but alternates are accepted
    as arguements
    """
    # Extract U10, W10 ( use 10 m wind? )
    datal = []
    for spec in vars:
        # Extract model data
#        data, dates, units = get_pf_mod_data( sdate=sdate, edate=edate, \
#                loc=loc, spec=spec, scale=scale,adjustby=adjustby, \
#                period=period, units=None, debug=debug)
        data, dates, units = get_NetCDF_mod_data( sdate=sdate, \
                edate=edate, loc=loc, spec=spec, scale=scale,\
                adjustby=adjustby, period=period, EOHemisions=True, \
                units=None, debug=debug)
        datal += [data ]
    # Make dataframe to allow for function mapping
    df = pd.DataFrame( data=np.array(datal).T, columns=vars )
    # Calculate wind dir  " (270-atan2(V,U)*180/pi)%360  "
    def f(x):
        return (270-atan2(x['GMAO_VWND'],x['GMAO_UWND'])*180/pi)%360
    df= df.apply( f, axis=1)
    # Return
    return [ np.array(i) for i in (df, dates) ]


# ----------------------- Section 3 -------------------------------------------
# -------------- Data Processing tools/drivers
#


# ----
# X.XX - get GC years
# ----
def get_gc_years(ctm_f=None, wd=None, filename='ctm.nc', set_=True, \
        debug=False):
    """
    Return list of years in CTM output
    """
    if pygchem.__version__ == '0.2.0':
        diagnostics = ctm_f.filter(name='O3', category="IJ-AVG-$" )
        if (set_):
            return list(set( [diag.times[0].strftime('%Y')  \
                for diag in diagnostics ] ))
        else:
            return [ diag.times[0].strftime('%Y')  for diag in diagnostics ]
    # Use updated PyGChem ( >0.3.0 ) approach
    else:
        dates = get_gc_datetime( wd=wd, filename=filename )
        return [ i.year for i in dates ]

# ----
# X.XX - get GC months
# ----
def get_gc_months(ctm_f=None, wd=None, filename='ctm.nc', \
        verbose=False, debug=False):
    """
    Return list of months in CTM output
    """
    if pygchem.__version__ == '0.2.0':
        diagnostics = ctm_f.filter(name='O3', category="IJ-AVG-$" )
        return [diag.times[0].strftime('%m')  for diag in diagnostics ]
    # Use updated PyGChem ( >0.3.0 ) approach
    else:
        dates = get_gc_datetime( wd=wd, filename=filename, debug=debug,\
             verbose=verbose )
        return [ i.month for i in dates ]


# ----
# X.XX - Get gc datetime
# ----
def get_gc_datetime(ctm_f=None, wd=None, spec='O3', cat='IJ-AVG-$', \
        filename='ctm.nc', date_str='hours since %Y-%m-%d %H:%M:%S', \
        verbose=False, debug=False):
    """
    Return list of dates in datetime output from CTM output

    Parameters
    ----------
    cat (str): GAMAP species category
    ctm_f (file object): PyGChem (v2.0) opened ctm.bpch file  - vestigle
    debug (boolean): legacy debug option, replaced by python logging
    filename (Str): name of NetCDF file (e.g. ctm.nc or ts_ctm.nc)
    spec (str): species/tracer/variable name
    ver (str): The GEOS-Chem halogen version that is being used
    wd (str): Specify the wd to get the results from a run.

    Returns
    -------
    (list)

    Notes
    -----
    """
    logging.info( 'get_gc_datetime called @: {} with file: {}'.format( wd, \
        filename) )
    # REDUNDENT - retain for backwards compatibility
    if pygchem.__version__ == '0.2.0':
        d  = ctm_f.filter(name=spec, category=cat)
        logging.debug( d, sorted(d), '{}'.format(*[ i.times for i in d ]) )
    # Extract datetime from cube
    else:
        # Create NetCDf if not created.
        fname = wd+ '/'+filename
        if not os.path.isfile(fname):
            from .bpch2netCDF  import convert_to_netCDF
            convert_to_netCDF( wd )
        # "open" NetCDF + extract time
        with Dataset( fname, 'r' ) as rootgrp:
            dates = rootgrp['time']
            unit_str = str(dates.units)
            if verbose: print((dates, dates.units, unit_str))
            # Get units from cube, default is 'hours since 1985-01-01 00:00:00'
            if 'hours since' in unit_str:
                if isinstance( date_str, type(None) ):
                    date_str='hours since %Y-%m-%d %H:%M:%S'
                time_unit = 'hours'
            elif 'minutes since' in unit_str:
                if isinstance( date_str, type(None) ):
                    date_str='minutes since %Y-%m-%d %H:%M:%S'
                time_unit = 'minutes'
            elif 'days since' in unit_str:
                if isinstance( date_str, type(None) ):
                    date_str='days since %Y-%m-%d %H:%M:%S'
                time_unit = 'days'
            else:
                err_str = 'WARNING: time unit not setup: {}'.format( unit_str)
                print(err_str)
                logging.info(err_str)
                sys.exit()
            # calculate start time
            starttime = time.strptime( unit_str, date_str )
            starttime = time2datetime( [starttime] )[0]
            dates = np.array(dates)
        logging.info( 'file start date: {}'.format(starttime) )
        # allow for single date output <= is there a better gotcha than this?
        if len(dates.shape)== 0 :
            dates = [float(dates)]
        # Convert to date time
        if time_unit == 'hours':
            dates = [ add_hrs( starttime, i ) for i in dates ]
        elif time_unit == 'minutes':
            dates = [ add_minutes( starttime, i ) for i in dates ]
        elif time_unit == 'days':
            dates = [ add_days( starttime, i ) for i in dates ]
        else:
            err_str = "processing not setup for unit: '{}' ".format( date_str )
            print( err_str )
            logging.info( err_str )
            sys.exit()
        logging.debug( '1st date dates {}'.format(dates[:10])  )
        # Return datetime objects
        return dates


# ----
# X.XX - Get frequency of model output.
# ----
def get_frequency_of_model_output( wd=None, months=None, years=None,
        datetimes=None, filename='ctm.nc', debug=False):
    """
    Get frequency of model output (e.g. monthly, weekly, daily ).

    Parameters
    ----------
    wd (str): the directory to search for file in
    filename (str): name of NetCDF file to extract from
    years, months (list): list of years and months in model output file
    datetimes (list): list of datetimes of output in model output file

    Returns
    ----
    (str)
    """
    from calendar import monthrange
    # Datetimes
    if isinstance(datetimes, type(None)):
        datetimes = get_gc_datetime(wd=wd, filename=filename)
    # Differences between these?
    diffs = [i-datetimes[n+1] for n, i in enumerate( datetimes[:-1] ) ]
    # in days?
    diffs =  [abs(i.total_seconds()/60./60./24.) for i in diffs]
    # all the same value?
    set_of_diffs = list(set(diffs))
    if len(set_of_diffs) > 1:
        # Check if months are full lengths?
        if isinstance(months, type(None)):
            months = [i.month for i in datetimes]
        if isinstance(years, type(None)):
            years = [i.year for i in datetimes]
        # Get number of days in month
        daysinmonth = [monthrange(years[n],i)[-1] for n,i in enumerate(months)]
#        if debug:
#            print daysinmonth, months, years, diffs, set_of_diffs
        # if the lists are the same ...
        if diffs==daysinmonth[:-1]:
            return 'Monthly'
        elif set(diffs) == set(daysinmonth):
            err_msg= 'Please check datetimes of file, issues in days/month'
            print(err_msg)
            logging.info(err_msg)
            return 'Monthly'
        else:
            err_msg= 'WARNING - Unequal timestep in output!'
            print(err_msg)
            logging.info(err_msg)
            # enter to continue?
            sys.exit()
    else:
        try:
            if set_of_diffs[0] == 1.:
                return 'Daily'
            elif set_of_diffs[0] == 7.:
                return 'Weekly'
            else:
                # Check if months are full lengths?
                if isinstance(months, type(None)):
                    months = [i.month for i in datetimes]
                if isinstance(years, type(None)):
                    years = [i.year for i in datetimes]
                # Get number of days in month
                daysinmonth = [monthrange(years[n],i)[-1] \
                    for n,i in enumerate(months)]
                if set_of_diffs==list(set(daysinmonth[:-1])):
                    return 'Monthly'
                else:
                    print(('Cannot work out output frequency for step diff: ', \
                        set_of_diffs, daysinmonth, years, months))
                    sys.exit()
        except IndexError:
            assumed_freq = 'Monthly'
#            assumed_freq 'Weekly'
            err_msg = '1 time dim., assuming {} output!'.format(assumed_freq)
            logging.info(err_msg)
            print(err_msg)
            return assumed_freq


# ----
# X.XX - Get CH4 Lifetime in years
# ----
def get_CH4_lifetime( ctm_f=None, wd=None, res='4x5', \
        vol=None, a_m=None, t_ps=None, K=None, t_lvl=None, n_air=None, \
        years=None, months=None, monthly=False, trop_limit=True, \
        use_OH_from_geos_log=False, average_value=True, LCH4_Cl=None,  \
        use_time_in_trop=True, masktrop=False, include_Cl_ox=False, \
        verbose=True, debug=False ):
    """
    Get amtospheric methane (CH4) lifetime by calculating loss rate against OH.

    Parameters
    -------

    Returns
    -------

    Notes
    -----
     - Multiple options for calculation of this value.
     - uses diagnostic arrays for [OH] instead of goes.log values as default.
     - Calculates the total atmospheric lifetime of CH4 due to oxidation by
     tropospheric OH as default ( aka does not mask  stratosphere. )
     - 1st approach ( set use_time_in_trop=True) uses reaction rate in
     globchem.dat (K(o)= 2.45E-12, Ea/R= -1775 ) and OH/CH4 mean
     concentrations from geos.log. The tropospheric mask uses is defined by
     the time in the troposphere diagnostic. the value is weighted by **air
      mass** if  ( average_value=True  )
     - Other approach: Effectively the same approach, but uses the tropopause
     level to define tropopause ( set use_time_in_trop=False to use this),
     and weights output by **molecules** if ( average_value=True  )
    """
    if debug:
        print(('get_CH4_lifetime called ( using time in trop diag?={})'.format(
            use_time_in_trop )))
    # --- Get shared variables that are not provided
    if not isinstance(vol, np.ndarray): # cm^3
        vol = get_volume_np( ctm_f =ctm_f, wd=wd, trop_limit=trop_limit )
    if not isinstance(a_m, np.ndarray): # Kg
        a_m = get_air_mass_np( ctm_f=ctm_f, wd=wd, trop_limit=trop_limit )
    if not isinstance(K, np.ndarray): # K
        K = get_GC_output( wd=wd, vars=['DAO_3D_S__TMPU'], \
            trop_limit=trop_limit  )
    if not isinstance(t_ps, np.ndarray):
        t_ps = get_GC_output( wd, vars=['TIME_TPS__TIMETROP'], \
            trop_limit=trop_limit )
    if not use_time_in_trop:
        if not isinstance(t_lvl, np.ndarray):
            t_lvl = get_GC_output( wd, vars=['TR_PAUSE__TP_LEVEL'], \
                trop_limit=False )
        if not isinstance(n_air, np.ndarray):
            n_air = get_number_density_variable( wd=wd, trop_limit=trop_limit )
    # Get OH conc [molec/cm3]
    if use_OH_from_geos_log:
        OH   = get_OH_mean( wd ) * 1E5
    else: # Extract from GEOS-Chem fields
        OH = get_GC_output( wd=wd, vars=['CHEM_L_S__'+'OH'], \
            trop_limit=trop_limit )
#        #  What are the units for 'CHEM_L_S__OH' ? need to convert?
          # (NetCDF says molec/m3, and wiki says  [molec/cm3]  )
#        OH = OH *1E6
    if include_Cl_ox:
        # Get mixing ratio [v/v]
        Cl = get_GC_output( wd, vars=['IJ_AVG_S__'+'Cl'], \
            trop_limit=trop_limit)
        # Convert units to [molec/cm3]
        Cl = convert_v_v_2_molec_cm3( Cl, vol=vol, a_m=a_m )
        # Get global CH4 conc  ( v/v )
        CH4 = get_CH4_mean( wd, rtn_avg_3D_concs=True  )
        # Convert to [molec/cm3] from v/v
        CH4 = convert_v_v_2_molec_cm3( CH4, vol=vol, a_m=a_m )
        if use_time_in_trop and masktrop:
            # Mask non tropospheric boxes
            OH = mask4troposphere( [OH], t_ps=t_ps)[0]
            if include_Cl_ox:
                Cl = mask4troposphere( [Cl], t_ps=t_ps)[0]
                CH4 = mask4troposphere( [CH4], t_ps=t_ps)[0]
    if use_time_in_trop and masktrop:
        # Mask non tropospheric boxes
        K, vol, a_m = mask4troposphere( [K, vol, a_m], t_ps=t_ps )
        # get loss rate - in kg/s - only works for CH4 sim.
    #    LCH4 = get_gc_data_np(ctm_f, spec='CH4Loss', \
    #            category='CH4-LOSS')
    # --- Shared processed variables
    # CH4 loss rate (OH) per grid box  ( cm^3  molec.^-1  s^-1  )
    KCH4 = 2.45E-12 * np.ma.exp( (-1775. / K)  )
    # Fixing PD from smvgear tag (LR63) as PD354
    if include_Cl_ox:
        Lrate_CH4_Cl = get_GC_output( wd, vars=['PORL_L_S__'+'PD354'], \
                trop_limit=trop_limit)
    # --- Now Calculate CH4 lifetimes
    if use_time_in_trop:
        # --- Calc from (CH4 +OH) reaction (loss) rate
        # CH4 loss rate via reaction
    #    arr = LCH4 * CH4
        # Get CH4 lifetime with respect to OH
        # (( cm^3  molec.^-1  s^-1  )* [molec/cm3]  =  [s^-1] )
        LCH4 = KCH4 * OH
        # Get CH4 lifetime with respect to Cl
        if include_Cl_ox:
            # ( 1/ ( [molec/cm3]/[molec/cm3/s] ) =  [s^-1]  )
#            LCH4_Cl =1/ np.ma.divide( Cl, Lrate_CH4_Cl  )
            LCH4_Cl =1/ np.ma.divide( CH4, Lrate_CH4_Cl  )
        if debug:
            print((( 1 / ( (LCH4*a_m).sum()/a_m.sum() )   ) /60/60/24/365))
            print([ (i*a_m).sum()/a_m.sum() for i in (OH, LCH4, KCH4) ])
            print((get_OH_mean( wd ) * 1E5))
            print([ ( i.shape, i.sum(), i.mean(), i.min(), i.max()) \
                for i in  (LCH4, LCH4_Cl, Lrate_CH4_Cl, Cl) ])
        if average_value:
            # get mass weighed average
            LCH4 =  (LCH4*a_m).sum()/a_m.sum()
    #        arr = np.ma.mean(  arr  )
            if include_Cl_ox:
                LCH4_Cl =  (LCH4_Cl*a_m).sum()/a_m.sum()
                print([ ( i.shape, i.sum(), i.mean(), i.min(), i.max()) \
                    for i in  (LCH4_Cl, Lrate_CH4_Cl, Cl) ])
        # return CH4 lifetime
        CH4_tau_s =  LCH4
        if include_Cl_ox:
            CH4_tau_s = np.ma.sum( [LCH4_Cl, LCH4] )
        print(('Using 1st apporach: ', LCH4, LCH4_Cl, CH4_tau_s))
        return 1/CH4_tau_s /60/60/24/365

    else: # Second Approach ( as per Schmidt et al 2015)
        # CH3CCl loss rate per grid box  ( cm^3  molec.^-1  s^-1  )
#        LCH3CCl = 1.64E-12 * np.ma.exp( (-1520. / K)  )
        # Mask non tropospheric boxes ( use: tropopause level )
        print([i.shape for i in (K, vol, a_m, n_air, KCH4, OH)  ])
        if masktrop:
            K, vol, a_m, n_air, KCH4, OH = mask4troposphere( \
                [K, vol, a_m, n_air, KCH4, OH ], t_lvl=t_lvl,  \
                use_time_in_trop=use_time_in_trop )
            if include_Cl_ox:
                Lrate_CH4_Cl = mask4troposphere( [Lrate_CH4_Cl], t_lvl=t_lvl,  \
                    use_time_in_trop=use_time_in_trop )[0]
        # get # molecules per grid box
        molecs = n_air *vol
        # Get loss with respect to OH
        # (( cm^3  molec.^-1  s^-1  )* [molec/cm3]  =  [s^-1] )
        LCH4 = KCH4 * OH
        if include_Cl_ox: # Get loss with respect to Cl ?
            # ( 1/ ( [molec/cm3]/[molec/cm3/s] ) =  [s^-1]  )
#            LCH4_Cl =  1/np.ma.divide( Cl, Lrate_CH4_Cl  )
            # ( 1/ ( [molec/cm3]/[molec/cm3/s] ) =  [s^-1]  )
            LCH4_Cl =  1/np.ma.divide( CH4, Lrate_CH4_Cl  )
        if debug:
            print([ ( i.shape, i.sum(), i.min(), i.max(), i.mean() )  \
                for i in [ LCH4, KCH4, molecs ] ])
            print([ ( i.mean(), i.min(), i.max()) \
                for i in  (LCH4, LCH4_Cl, Lrate_CH4_Cl, Cl) ])
        if average_value:
            # Get weighted values per time step
            LCH4_l, LCH4_Cl_l = [], []
            for n in range( LCH4.shape[-1] ):
                # Weight by molecules
                LCH4_l += [ ( LCH4[...,n] * molecs[...,n] ).sum()  \
                    / molecs[...,n].sum() ]
                if include_Cl_ox: # Get loss with respect to Cl ?
                    LCH4_Cl_l += [ ( LCH4_Cl[...,n] * molecs[...,n] ).sum()  \
                        / molecs[...,n].sum() ]
            if debug: print(LCH4_l)
            # take mean
            LCH4 = np.ma.mean( LCH4_l )
            if include_Cl_ox:
                LCH4_Cl = np.ma.mean( LCH4_Cl_l )
        if debug:
            print([ ( i.shape, i.sum(), i.min(), i.max(), i.mean() )  \
                for i in [ LCH4, KCH4, molecs ] ])
        # Convert units from /s to yrs
        CH4_tau_s = LCH4
        if include_Cl_ox:
            CH4_tau_s = np.ma.sum( [LCH4_Cl, LCH4] )
        print(('Using 2nd apporach: ', LCH4, LCH4_Cl, CH4_tau_s))
        return 1/ CH4_tau_s / (3600*24*365)


# ----
# X.XX - get Land / Water /Ice fraction
# ----
def get_LWI(lon, lat, res='4x5', date=None, debug=False):
    """ Return LWI for a given lon and lat """
    lat = get_gc_lat(lat, res=res)
    lon = get_gc_lon(lon, res=res)
    LWI = get_land_map(res=res, date=date)
    return LWI[lon,lat,0]


# ----
# X.XX - get_gc_alt  ( KM/hPa => vertical model box index )
# ----
def get_gc_alt(alt, unit='km'):
    """
    Return index of nearest altitude (km ) of GEOS-Chem box
    """
    if unit=='km':
        alt_c = gchemgrid('c_km_geos5_r')
    elif unit=='hPa':
        alt_c = gchemgrid('c_hPa_geos5')
    else:
        err_str = 'No case setup for altitude unit ({})'.format( unit )
        sys.exit()
    return find_nearest( alt_c, alt )


# ----
# X.XX - species arrary (4D) in v/v to Gg  I/ O3/Species
# ----
def species_v_v_to_Gg(arr, spec, a_m=None, Iodine=True, All =False, \
        Ox=False, ctm_f=None, wd=None, debug=False):
    """
    Convert array of species in v/v to Gg (of spec)

    Parameters
    -------

    Returns
    -------

    Notes
    -----
     - The processing is not clear in this function, NEEDS UPDATE
     - To output in terms of provide spec (e.g. Bry ) set All=True and
      Iodine=False. This should be default bevahiour, but is not for reasons
      of back compatibility.
    """
    var_list = All, Iodine, Ox, spec
    print(('WARNING: Check settings in species_v_v_to_Gg: ',  var_list))
    if not isinstance(a_m, np.ndarray):
        a_m = get_air_mass_np( ctm_f, wd=wd, debug=debug )  # kg
    #  number of moles in box ( g / g mol-1 (air) )
    moles = ( a_m *1E3 ) / constants( 'RMM_air')
    if debug: print([ i.shape for i in (moles, arr) ])
    # I mass ( moles => mass (g) => Gg (in units of I ) )
    if ( (Iodine) and ( (not Ox) and (not All) ) ):
        arr = ( ( arr * moles )  * 127. ) /1E9 * spec_stoich( spec )
    # O3 mass ( moles => mass (g) => Gg (in units of O3 ) )
    if ( (Iodine) and (Ox) ):
        arr = ( ( arr * moles )  * (16.*3.) ) /1E9
    #  In "species" mass terms ( moles => mass (g) => Gg (in units of spec ) )
    if ( ( not Iodine ) and ( All) ):
        arr = ( ( arr * moles )  * (species_mass( spec  )) ) /1E9
    return arr


# ----
# X.XX - retrive volume for geos chem run ( in cm3 )
# ----
def get_volume_np(ctm_f=None, box_height=None, s_area=None, res='4x5', \
        wd=None, trop_limit=False, debug=False):
    """ Get grid box volumes for CTM output in cm3 """
    logging.info( 'get_volume_np called for res={}'.format(res) )
    if not isinstance(box_height, np.ndarray):
        if pygchem.__version__ == '0.2.0':
            box_height =  get_gc_data_np(ctm_f, 'BXHEIGHT',\
                category="BXHGHT-$", debug=debug)  # ( m )
        else:
            try:
                box_height = get_GC_output( wd=wd, vars=['BXHGHT_S__BXHEIGHT'],\
                    trop_limit=trop_limit, debug=debug )
            except:
                logging.info( 'WARNING: Using ref. file for BXHEIGHT' )
                logging.info( 'WARNING: ref file use not implemented' )
                sys.exit()
            # Gotcha for single (None) time dimension output:
            # <= improve this - this only works for 4x5 resolution
            none_time_dim_shapes = (72, 46, 47), (72, 46, 38)
            if any( [ box_height.shape == i for i in none_time_dim_shapes ]) :
                box_height= box_height[...,None]
    if not isinstance(s_area, np.ndarray):
        # m2 land map
        s_area = get_surface_area(res=res)[...,None]
        logging.info('WARNING - inefficent online extraction of s_area')
    # Gotcha for 2D s_area array
    if len(s_area.shape) == 2:
        s_area = s_area[..., None, None]
    # m3 ( *1E6 ) => cm3
    logging.debug( 'shape of box_height={} and s_area={} for res={}'.format( \
        box_height.shape, s_area.shape, res) )
    volume = ( box_height * s_area ) *1E6
    if trop_limit:
        volume =  volume[...,:38,:]
    logging.debug('shapes for box_height={}, s_area={}, volume{}'.format( \
        box_height.shape, s_area.shape, volume.shape ) )
    return volume


# ----
# X.XX - Test is grid box for a given lat and lon is over water
# ----
def loc_is_water_grid_box( lat, lon, res='4x5' ):
    """ Return Boolean for if grid box is water or not """
    # Load masked array, where all ocean is non-masked
    # ( Just look over oceans (use masked array) )
    o_mask = np.ma.equal( get_land_map(res=res)[...,0], 0)
    # Loop Lat and Lon
    for n, l in enumerate( lat ):
        glat, glon = get_gc_lat( l ), get_gc_lon( lon[n] )
        # check aagainst mask and store as boolean
        if o_mask[glon, glat] :
            bool = 'F'
        else:
            bool = 'T'
        try:
            booll.append( bool )
        except:
            booll = [ bool ]
    return booll


# ----
# X.XX - Get dry dep for given spec
# ----
def spec_dep(ctm_f=None, wd=None, spec='O3', s_area=None, months=None, \
        years=None, res='4x5', vol=None, trop_limit=True, Iodine=False, \
        output_freq='Monthly', debug=False ):
    """
    Get array of dry deposition values for a given species

    Parameters
    ----------
    trop_limit (boolean): limit 4D arrays to troposphere
    ctm_f (file object): PyGChem (v2.0) opened ctm.bpch file  - vestigle
    wd (str): the directory to search for file ctm output file in
    vol (array): volumne contained in each grid box (cm^-3)
    years, months (list): list of years and months in model output file
    res (str): GEOS-Chem output configuration resolution ( '4x5' etc... )
    spec (str): species/tracer/variable name
    Iodine (boolean): Return in terms of unit iodine mass
    debug (boolean): legacy debug option, replaced by python logging
    output_freq (str): output step of model e.g.  monthly, daily, weekly

    Returns
    -------
    (array)

    Notes
    -----
     - Values are returned as a spatial array with a time dimension
    (e.g. shape= (72, 46, 12) )
    """
    logging.info( 'spec dep called for: {}'.format(spec) )
    # Get surface area if not provided
    if not isinstance(s_area, np.ndarray):
        s_area = get_surface_area( res )  # m2 land map
    # Extract dry dep flux in  [molec/cm2/s]
    if pygchem.__version__ == '0.02':
        arr = get_gc_data_np( ctm_f, spec=spec+'df', category='DRYD-FLX', \
            debug=debug)
    else:
        arr = get_GC_output( wd, category='DRYD-FLX', species=spec+'df' )
    logging.debug( 'arr (len=={}) descrp: {}'.format( len(arr), \
        *[ str(ii) for ii in [(i.shape, i.sum(), i.mean()) for i in [arr]]]))
    # Convert to Gg "Ox" (Gg X /s)
    arr = molec_cm2_s_2_Gg_Ox_np( arr, spec, s_area=s_area, Iodine=Iodine, \
        res=res, debug=debug )
    logging.debug( 'arr (len=={}) descrp: {}'.format( len(arr), \
        *[ str(ii) for ii in [(i.shape, i.sum(), i.mean()) for i in [arr]]]))
    if isinstance(months, type(None)):
        months = get_gc_months( ctm_f=ctm_f, wd=wd )
    if isinstance(years, type(None)):
        years = get_gc_years( ctm_f=ctm_f, wd=wd, set_=False )
    # Adjust time dimension (to per month)
    if output_freq == 'Monthly':
        day_adjust = d_adjust( months, years)
        arr = np.multiply(arr, day_adjust)
    return arr


# ----
# X.XX - Gg Ox yr^-1 from induvial spec (2D array - dry dep)  ( ([molec/cm2/s] ) to Gg X (or Gg X / s if not year_eq. )
# ----
def molec_cm2_s_2_Gg_Ox_np( arr, spec='O3', s_area=None, ctm_f=None, \
        Iodine=False, res='4x5', year_eq=False, debug=False):
    """
    Convert 2D depositional array from [molec/cm2/s] to Gg Ox yr^-1

    Parameters
    -------
    spec (str): species/tracer/variable name
    s_area (array): 2D array of surface area of grid box (m^2)
    ctm_f (file object): PyGChem (v2.0) opened ctm.bpch file  - vestigle
    Iodine (boolean): return in units of iodine mass?
    res (str): the resolution if wd not given (e.g. '4x5' )
    year_eq (boolean): convert into year equivilents?
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    (array)

    Notes
    -----
     -  NEEDS UPDATE. The code is not clear.
    """
    logging.info( 'molec_cm2_s_2_Gg_Ox_np  called' )

    # Kludge (loads all output surface areas,
    # only requires a single time dimensions as does not chnage... )
    s_area = s_area[...,None]  # tmp bug fix
    #  anti-kludge
#    if fix_Kludge:
#    s_area = s_area[...,0]
    logging.debug( 'arr shape={} and s_area shape={}'.format( arr.shape,
        s_area.shape ) )
    if ( Iodine ):
        # [molec/cm2/s] * cm2 (m*1E4) /  moles * RMM I /1E9 ( convert Gg I /s )
        arr  = ( arr * (s_area*1E4) ) / constants( 'AVG') * (127.) * \
            spec_stoich(spec) /1E9
    elif spec == 'O3':
        arr = ( arr * (s_area*1E4) )  / constants( 'AVG')* \
            species_mass(spec) /1E9  * Ox_in_species( spec)
    else:
        arr = ( arr * (s_area*1E4) )  / constants( 'AVG') * \
            species_mass(spec) /1E9
    if year_eq:
        print("giving 'year_eq' ")
        arr = arr* 60*60*24*365
    if debug: print(('arr', arr.shape))
    return arr


# ----
# X.XX - Get DU mean value
# ----
def get_DU_mean(spec='O3',s_area=None, a_m=None, t_p=None, O3_arr=None, wd=None,
        ctm_f=False, area_weight=True, res='4x5', trop_limit=True, debug=False):
    """
    Get mean DU value weighed by grid box area

    Parameters
    -------
    t_p (ndarray): time in the troposphere diganostic ( float values 0 to 1 )
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )
    ctm_f (ctm.bpch file object): This is vestigle from PyGChem <3.0
    s_area (ndarray): Surface array (array of values in metres)
    area_weight (boolean): weight by area of grid box?
    O3_arr (ndarray): array of mixing ratio (v/v), e.g. ozone

    Returns
    -------
    (array)

    """
    if not isinstance(s_area, np.ndarray):
        print("Extracting s_area in 'get_DU_mean'")
        s_area  =  get_surface_area( res )[...,0]  # m2 land map
    if not isinstance(a_m, np.ndarray):
        print("Extracting a_m in 'get_DU_mean'")
        a_m = get_air_mass_np( ctm_f, wd=wd, trop_limit=trop_limit,
            debug=debug )
    if not isinstance(t_p, np.ndarray):
        print("Extracting t_p in 'get_DU_mean'")
        t_p = get_GC_output( wd=wd, vars=[u'TIME_TPS__TIMETROP'],
            trop_limit=trop_limit, debug=debug)
    if not isinstance(O3_arr, np.ndarray):
        print("Extracting arr in 'get_DU_mean'")
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+spec],
            trop_limit=trop_limit, debug=debug )
    else:
        arr = O3_arr
    if debug: print([ (i.shape, i.mean()) for i in (s_area, a_m, t_p, arr) ])
    # Get molec. of air to get moles of spec
    # molecs air
    molecs_air = (a_m*1E3) / constants( 'RMM_air') * constants('AVG')
    # molecules O3
    arr = np.ma.array(arr) * molecs_air
    # average of time within the troposphere
    # cut columns to tropopause
    arr = np.sum( arr* t_p, axis=2 )
    # average over time
    arr = arr.mean(axis=2)
    # convert to DU
    arr = arr / s_area # adjust to per area
    arr  = arr / constants('mol2DU') # convert to DU
    if area_weight:
        arr = np.sum(arr * s_area)/np.sum(s_area) # weight by area
    return arr


# ----
# X.XX - Get Prod / loss for O3
# ----
def get_POxLOx( ctms=None, vol=None, all_data=False, t_p=None, ver='1.6', \
        wd=None, year_eq=True, res='4x5', return_as_int_sum=False, \
        trop_limit=True, GC_version='v10-01', debug=False):
    """
    Get production and loss terms for O3 from prod/loss diagnostic

    Parameters
    -------
    t_p (np.array): 4D array of (fractional) time a grid box has spent in tropospehre
    vol (array): volume contained in each grid box (cm^-3)
    res (str): GEOS-Chem output configuration resolution ( '4x5' etc... )
    ver (str): The GEOS-Chem halogen version that is being used
    all_data(boolean): return the full data (instead of two single numbers)
    ctms (list): list of ctm.bpch file objects (vestigle from PyGChem <3.0)
    GC_version (str): GEOS-Chem version (e.g. v11-01 or v10-01)

    Returns
    -------
    (list) of two (int)
    """
    logging.info( 'get_POxLOx called with iGC ver={}'.format( ver ) )
    # Get names of POx and LOx diagnostics
    if GC_version == 'v10-01':
        specs = GC_var('POxLOx')
    else:
        specs = ['POx', 'LOx']
    # Get required variables if not provided
    if isinstance( t_p, type(None) ):
        t_p = get_GC_output( wd, vars=['TIME_TPS__TIMETROP'], \
            trop_limit=trop_limit)
    # Get prod/loss in [molec/cm3/s]
    if pygchem.__version__ ==  '0.2.0':
        arrs = [ np.concatenate( [get_gc_data_np( ctm, spec=PLO3_to_PD(spec, \
            ver=ver, fp=True), category="PORL-L=$", debug=debug) \
            for ctm in ctms ], axis=3 ) for spec in specs ]
    else:
        arrs = get_GC_output( wd=wd, vars=['PORL_L_S__'+i for i in specs],
            trop_limit=trop_limit )
        arrs = [ arrs[i,...] for i in range( len(specs) ) ]
    if all_data:
        logging.info( "WARNING 'all_data' only configured for PyGChem 0.2.0")
        # [molec/cm3/s] => Gg Ox / month
        months = [ get_gc_months( ctm) for ctm in ctms ]
        years =  [ get_gc_years( ctm, set_=False ) for ctm in ctms ]
        months = [j for i in months for j in i ]
        years = [j for i in years for j in i ]
        arrs = [ molec_cm3_s_2_Gg_Ox_np(arr, specs[n], vol=vol, months=months, \
                    years=years, debug=debug, wd=wd, \
                    month_eq=True, year_eq=False) \
                    for n, arr in enumerate(arrs) ]
        return arrs  # Gg
    else:
        # [molec/cm3/s] => Gg Ox / yr
        arrs = [ molec_cm3_s_2_Gg_Ox_np(arr, specs[n], vol=vol, wd=wd,res=res,\
            debug=debug, year_eq=year_eq ) for n, arr in enumerate(arrs) ]
        # if not using year_eq in "molec_cm3_s_2_Gg_Ox_np", now convert
        if not year_eq:
            arrs = [ i*60.*60.*24.*365. for i in arrs ]
        # Get mean over time + remove stratosphere
        # NEEDS UPDATE - update troposphere removal method?
        arrs = [ (arr*t_p).mean(axis=3) for arr in arrs ]
        # Return list of two integers
        arrs = [ np.ma.masked_invalid(i) for i in arrs ]
        if return_as_int_sum:
            return [ int(i.sum()/1E3) for i in arrs ] # Tg
        else:
            return [ i/1E3 for i in arrs ] # Tg


# ----
# X.XX - Get wet dep
# ----
def get_wet_dep( ctm_f=None, months=None, years=None, vol=None, \
        scale=1E9, s_area=None, res='4x5', wd=None, specs=None, \
        Iodine=False, all_wdep=False, sep_rxn=False, ref_spec=None, \
        ver='1.6', trop_limit=True, output_freq='Monthly', debug=False):
    """
    Extract wet deposition for given species in terms of X Gg of ref_spec.

    Parameters
    -------
    ctm_f: ctm.bpch file object (vestigle from PyGChem <3.0)
    ver (str): GEOSChem version with halogens (default = 3.0), ignore if not using halogen code
    s_area (array): 4D Surface area array (m2)
    vol (array): volumne of grid boxes
    trop_limit (boolean): limit output to "chemical troposphere" (level 38 )
    Iodine (boolean): return in terms of mass of iodine
    scale (int): scaleing to use (e.g. 1E9 = Gg )
    sep_rxn (boolean): return list of arrays by "reaction"/process
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )
    output_freq (str): e.g. monthly, daily, weekly...

    Returns
    -------
    (Array)

    Notes
    -----
     - If Iodine=True, re_spec == 'I'
     - this fucntion expects list of species
    ( if a species list is not provided, then Iodine deposition is returned)
     - A reference species is expected to define the unit terms of the
    returned values.
    """
    logging_str = 'get_wet_dep called for {}, with ref_spec: {} (Iodine:{})'
    logging.info( logging_str.format( specs, ref_spec, Iodine ) )
    if not isinstance(months, list):
        months = get_gc_months( ctm_f, wd=wd )
    if not isinstance(years, list):
        years  = get_gc_years( ctm_f=ctm_f, wd=wd, set_=False )
    if not isinstance(vol, np.ndarray):
        vol = get_volume_np( ctm_f=ctm_f, s_area=s_area, wd=wd, res=res,\
             debug=debug )
    w_dep = GC_var('w_dep')
    # Special settings for iodine
    if Iodine and isinstance( specs, type(None) ):
        if (all_wdep):
            specs = GC_var('w_dep_specs')
            if ver =='3.0':
                specs += ['ISALA', 'ISALC' ]
        else:
            specs = GC_var('w_dep_specs')[:-1] # skip AERI - Kludge
            if ver =='3.0':
                specs = GC_var('w_dep_specs')[:-2] # skip ISALA/ISALC
        ref_spec = 'I'
    # Check whether a reference species ("ref_spec") has been set
    assert ref_spec != type(None), 'PLEASE PROVIDE REF SPEC'
    if debug: print((specs , len(specs)))
    # --- Extract and convert [kg/s] => g / s of ref_spec ( e.g. I equiv. )
    # Retain back compatibility
    if pygchem.__version__ == '0.2.0':
        dep_w = [ [ get_gc_data_np(ctm_f, spec ,category=var, \
            debug=debug )*1E3 /species_mass(spec)*  \
            species_mass(ref_spec)*spec_stoich(spec) \
            for spec in specs[ii] ]  \
            for ii,var in enumerate(w_dep)]
    else:
        # Frontal rain? [kg/s]
        WETDLS_S__ = get_GC_output( wd=wd, vars=['WETDLS_S__'+i \
            for i in specs ], r_list=True, trop_limit=trop_limit )
        # Get convective scavenging  [kg/s]
        WETDCV_S__ = get_GC_output( wd=wd, vars=['WETDCV_S__'+i \
            for i in specs ], r_list=True, trop_limit=trop_limit )
        if debug:
            print([ [ i.shape for i in l ] for l in (WETDLS_S__, WETDCV_S__) ])
        # Convert to g/ s X(ref_spec) equiv.  + conbine two lists
        dep_w = []
        for n, spec in enumerate( specs ):
            if debug:
                print((n, spec, ref_spec ), )
                print(( spec_stoich( spec, ref_spec=ref_spec) ))
            # Combine convective scavenging and Frontal rain
            dep_w += [ WETDLS_S__[n] + WETDCV_S__[n] ]
            # Convert [kg/s] to [g], then moles of species
            dep_w[n] = dep_w[n]*1E3/species_mass( spec )
            # Convert to unit terms of ref_spec
            dep_w[n] = dep_w[n]* species_mass(ref_spec)
            # Adjust to stoichiometry of ref_spec
            dep_w[n] = dep_w[n]*spec_stoich( spec, ref_spec=ref_spec)
    # Adjust to monthly values...
    if output_freq=='Monthly':
        m_adjust = d_adjust( months, years) # => Gg / month
        dep_w = [m_adjust *i for i in dep_w ]
    # List wet dep rxns, concat. and sum of rxns ( and convert to Gg )
    if sep_rxn:
        return np.concatenate( [ i[None,...] /scale for i in dep_w ], axis=0 )
    # List wet dep rxns and concat.
    else:
        return np.concatenate( [ i[...,None] /scale \
                        for i in dep_w ], axis=-1 ).sum(axis=-1 )

# ----
# X.XX - molecule weighted array average value
# ----
def molec_weighted_avg( arr, wd=None, ctm_f=None, vol=None, t_p=None,\
        trop_limit=True, multiply_method=False, rm_strat=True, molecs=None,\
        weight_lon=False, weight_lat=False, LON_axis=0, LAT_axis=1, n_air=None,\
        annual_mean=True, res='4x5', debug=False ):
    """
    Takes an array and retuns the average (molecular weighted) value

    Parameters
    -------
    weight_lat, weight_lon (boolean): weight over latitude or longitude
    annual_mean (boolean): average the time axis?
    n_air (array): number desnity of air
    molecs (array): number of molecules in air
    vol (array): volumne of grid boxes
    trop_limit (boolean): limit output to "chemical troposphere" (level 38 )
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )
    t_p (array): taime in the troposphere diganostic ( float values 0 to 1 )
    - definition of troposphere to use?
    use_time_in_trop (boolean): time a given box is in the troposphere
        ( if use_time_in_trop=False, the level of the troposphere is used )
     multiply_method (boolean): use a multiplication method, rather than masking for
        the arrays (aka set stratosphere to have zero values)
    LON_axis, LAT_axis (float): Index of longitudinal or latitudinal

    Returns
    -------
    (array)

    Notes
    -----
    Uses mask of given array if given array is a numpy masked array
    Assume axis dimensions are  (LON, LAT, ALT ), aka the array does not
        have a TIME dimension. Any shape can be handled as long as given molecs
        and arr have the same shape
    Molecs is the same as n_air ( [molec air/m3] * [m3]  vs.
       air mass [kg] / RMM [kg mol^-1] * Avogadros [mol^-1] )
    """
    logging.info('molec_weighted_avg called for arr.shape={}'.format(arr.shape))
    if isinstance( molecs, type(None) ):
        if not isinstance( n_air, np.ndarray): # [molec air/m3]
            n_air = get_number_density_variable( wd=wd, trop_limit=trop_limit )
        if not isinstance(vol, np.ndarray):
            vol = get_volume_np( ctm_f=ctm_f, wd=wd, res=res, \
                trop_limit=trop_limit )
            vol = vol /1E6 # [cm^3 ]
        # Calculate molecules per grid box
        molecs =  n_air * vol # [molec air]
        if annual_mean:
            molecs = molecs.mean(axis=-1)
    # Limit for troposphere?
    if trop_limit:
        # Get species time Tropopause diagnostic
        if isinstance( t_p, type(None) ) and rm_strat:
            t_p = get_GC_output( wd=wd, vars=['TIME_TPS__TIMETROP'], \
                trop_limit=trop_limit )
            # Mask for troposphere
            arr, molecs = mask4troposphere( [arr, molecs], t_ps=t_p, res=res,\
                use_time_in_trop=True, multiply_method=multiply_method)
    # If masked array provided, applied same mask to molecules
    if isinstance( arr, np.ma.core.MaskedArray ):
        try:
            molecs  = np.ma.array( molecs, mask=arr.mask )
        except:# MaskError:
            print(("MaskError for array shapes in 'molec_weighted_avg': ", \
                [ i.shape for i in (molecs, arr) ]))
    # Weight over which axis?
    if weight_lon and (not weight_lat):  # 1st axis
        return (arr *molecs).sum(axis=LON_axis)/molecs.sum(axis=LON_axis)
    elif weight_lat and (not weight_lon):  # 2nd axis (LON, LAT, ALT, TIME )
        return (arr *molecs).sum(axis=LAT_axis)/molecs.sum(axis=LAT_axis)
    elif weight_lat and weight_lon:  # 1st+2nd axis (LON, LAT, ALT, TIME )
        return (arr *molecs).sum(axis=LAT_axis).sum(axis=LON_axis)/  \
            molecs.sum(axis=LAT_axis).sum(axis=LON_axis)
    else: # weight whole array to give single number
        return (arr *molecs).sum()/molecs.sum()

# ----
# X.XX -
# ----
def get_number_density_variable( wd=None, trop_limit=True  ):
    """ Get number density variable from GEOS-Chem output NetCDF """
    try:
        n_air_var = 'BXHGHT_S__N(AIR)'
        n_air = get_GC_output( wd, vars=[n_air_var], \
            trop_limit=trop_limit, dtype=np.float64 )  # [molec air/m3]
    except UnboundLocalError:
        n_air_var = u'BXHGHT_S__AIRNUMDE'
        n_air = get_GC_output( wd, vars=[n_air_var], \
            trop_limit=trop_limit, dtype=np.float64 )  # [molec air/m3]
    return n_air


# ----
# X.XX - split 4D ( lon, lat, alt, time) output by season
# ----
def split_4D_array_into_seasons( arr, annual_plus_seasons=True, \
        debug=False ):
    """
    Split 4D ( lon, lat, alt, time) output by season, then take
    average of the seasons

    NOTE(s):
     - currently seasons index is mannual set assuming Jan-Dec
     - TODO - update to use extract data?
    """
    if debug: print((arr.shape))
    if annual_plus_seasons:
        seasons  = ['Annual', 'DJF', 'MAM', 'JJA', 'SON']
        # assume calender month order
        # ( this can be automated using get_GC_datetime )
        indices = [
        list(range(0,12)), [11, 0, 1], [2, 3, 4], [5, 6, 7], [8, 9, 10]
        ]
    else:
        seasons  = ['DJF', 'MAM', 'JJA', 'SON']
        # assume calender month order
        # ( this can be automated using get GC datetime )
        indices = [[11, 0, 1], [2, 3, 4], [5, 6, 7], [8, 9, 10]]
    ars = []
    # Extract data by month
    for n, s in enumerate( seasons ):
        if debug:
            print((s, n , indices[n]))
        ars += [ [ arr[...,i] for i in indices[n] ] ]
    # Average by season
    if debug:
        print(([ np.ma.array(i).shape for i in ars ], seasons))
    ars =  [ np.ma.array(i).mean(axis=0) for i in ars]
    if debug:
        print(([ i.shape for i in ars ], np.ma.array(ars).mean(), seasons))
    # Return list array averaged by season
    return ars, seasons


# ----
# X.XX - Convert v/v to ng/m^3
# ----
def convert_v_v2ngm3( arr, wd=None, spec='AERI', trop_limit=True, \
        s_area=None, vol=None, a_m=None, res='4x5', debug=False ):
    """
    Take v/v array for a species, and conver this to mass loading
    units used as standard are ng/m3

    Parameters
    -------
    spec (str): species/tracer/variable name
    a_m (np.array): 4D array of air mass
    vol (array): volume contained in each grid box (cm^-3)
    trop_limit (boolean): limit 4D arrays to troposphere
    res (str): the resolution if wd not given (e.g. '4x5' )

    Returns
    -------
    (array)
    """
    # Get volume (m^3, adjusted (x1E6) from cm^3)
    if not isinstance(vol, np.ndarray):
        vol = get_volume_np( wd=wd, trop_limit=trop_limit, s_area=s_area, \
                    res=res ) /1E6
    # Get air mass ( kg )
    if not isinstance(a_m, np.ndarray):
        a_m = get_GC_output( wd, vars=['BXHGHT_S__AD'], trop_limit=trop_limit,
                    dtype=np.float64)
    # Get moles  ( converting airmass from kg 1st)
    mols = a_m*1E3/constants( 'RMM_air' )
    # Adjust to mols, then mass
    arr = arr*mols*species_mass( spec )
    if debug: print((species_mass( spec ), np.sum( arr )))
    # Convert to (nano, x1E9)g/m3
    arr = arr*1E9/vol
    return arr


# ----
# X.XX - Convert v/v to ug/m^3
# ----
def convert_v_v2ugm3( arr, wd=None, spec='AERI', trop_limit=True, \
        s_area=None, vol=None, a_m=None, res='4x5', debug=False ):
    """
    Take v/v array for a species, and conver this to mass loading
    units used as standard are ng/m3

    Parameters
    -------
    spec (str): species/tracer/variable name
    a_m (np.array): 4D array of air mass
    vol (array): volume contained in each grid box (cm^-3)
    trop_limit (boolean): limit 4D arrays to troposphere
    res (str): the resolution if wd not given (e.g. '4x5' )

    Returns
    -------
    (array)
    """
    # Get volume (m^3, adjusted (x1E6) from cm^3)
    if not isinstance(vol, np.ndarray):
        vol = get_volume_np( wd=wd, trop_limit=trop_limit, s_area=s_area, \
                    res=res ) /1E6
    # Get air mass ( kg )
    if not isinstance(a_m, np.ndarray):
        a_m = get_GC_output( wd, vars=['BXHGHT_S__AD'], trop_limit=trop_limit,
                    dtype=np.float64)
    # Get moles  ( converting airmass from kg 1st)
    mols = a_m*1E3/constants( 'RMM_air' )
    # Adjust to mols, then mass
    arr = arr*mols*species_mass( spec )
    if debug: print((species_mass( spec ), np.sum( arr )))
    # Convert to (micro, x1E9)g/m3
    arr = arr*1E6/vol
    return arr


# ----
# X.XX - Print seasonal values array
# ----
def prt_seaonal_values( arr=None, res='4x5', area_weight=True, zonal=False, \
        region='All', monthly=False, mask3D=True, trop_limit=True, \
        prt_by_3D_region=False, hPa=None, wd=None, \
        verbose=True, debug=False ):
    """ Print zonal/surface area weighted values for seasons"""
    if verbose:
        print(('function prt_seaonal_values called for region: ', region, \
            'debug: {},verbose: {}'.format( debug, verbose )))
        print([ (i.min(), i.max(), i.mean() ) for i in  [arr] ])
        print([ (i.min(), i.max(), i.mean() ) \
            for i in [ arr.mean(axis=-1)[...,0] ]])
    # Get surface area
    s_area =  get_surface_area( res=res ) # m2 land map
    s_area = s_area[...,0]
    months = list(range(12))
    # --- If region provided, mask elsewhere - else
    if ( 'asked' not in str( type( arr ) ) ):
        print('WARNING: converting array to masked array')
        arr = np.ma.array( arr )
    if debug:
        print([ ( i.min(), i.max(),i.mean(), len(i.mask[i.mask==True].ravel()) )
                        for i in [arr] ])
    m = mask_all_but( region=region, mask3D=True, debug=debug,\
                use_multiply_method=False, \
                trop_limit=trop_limit )[...,:38]
    print([i.shape for i in (m, arr.mask) ])
    m = np.ma.concatenate( [m[...,None]] *len( months), axis=-1 )
    # Mask array individually
    print([i.shape for i in (m, arr.mask, arr) ])
    arr = np.ma.array( arr, mask=np.ma.mask_or(m, arr.mask) )
    #    ars = [ np.ma.array( i, mask=m ) for i in ars ]
    if debug:
        print((m, region, [ (type(i), i.shape) for i in [ m ] +[arr] ], \
                    arr.mask, [ ( i.min(), i.max(),i.mean() ) for i in [arr] ]))
    if debug:
        print([ ( i.min(), i.max(),i.mean(), len(i.mask[i.mask==True].ravel()) )
                        for i in [arr] ])
    # Also mask surface to also for area weighting of data
    s_area = np.ma.array( s_area, mask=m[...,0,0] )
    # --- Split array by seasons ( on months if monthly==True)
    if monthly:
        # this is assuming monthly output
        ars = [ arr[...,i] for i in range( 12 ) ]
        seasons = list(num2month( rtn_dict=True).values())
        # Also plot annual value
        ars += [ arr.mean( axis=-1 ) ]
        seasons += ['Annual']
    else:
        ars, seasons = split_4D_array_into_seasons( arr, \
                                        annual_plus_seasons=True )
    # --- Print values by 3D region
    if prt_by_3D_region:

        # Get pressure levels
        if isinstance( hPa, type(None) ):
            hPa = get_GC_output( wd=wd, vars=['PEDGE_S__PSURF'] )
            hPa = hPa.mean(axis=-1)[...,:38]
        # Setup makes for BL, FT, UT
        regions = [ 'MBL','BL','FT',  'UT']
        sects3D = [ mask_3D( hPa, i, res=res )[:,:,:38] for i in regions]
        print([i.shape for i in sects3D ])
        # --- Print values by 3D region
        pstr  = '{:<20}'*( len(regions) +1 )
        npstr  = '{:<20}'+ '{:<20,.3f}'*len(regions)
        print((pstr.format( 'spec' , *regions )))
        print((seasons, ars[0].mean()))
        # Mean of 3D region
        for n, s in enumerate( seasons ):
            vars = [ float( (i*ars[n]).mean() ) for i in sects3D]
            print((npstr.format( s, *vars )))
        # Min of 3D region
        for n, s in enumerate( seasons ):
            vars = [float( (i*ars[n]).min() ) for i in sects3D]
            print((npstr.format( s, *vars )))
        # Max of 3D region
        for n, s in enumerate( seasons ):
            vars = [ float( (i*ars[n]).max() ) for i in sects3D]
            print((npstr.format( s, *vars )))
    # ---- Get surface or Zonal array ( prt by 2D region )
    else:
        if zonal:
            ars = [i.mean(axis=0) for i in ars ]
        # If not zonal return surface values
        else:
#            ars = [ i[...,0] for i in ars ]
            ars = [ np.ma.array( i[...,0], mask=m[...,0,0] ) for i in ars ]
        if debug:
            print(([i.shape for i in ars ], s_area.shape, \
                    [type(i) for i in (ars, ars[0],  s_area) ]))
        # --- Print out
        header = [
         'Season./Month', 'Min', 'Max','5th','95th', 'Mean' , 'Median', \
         "wtg'd Mean"
        ]
        pstr =  '{:<15}'*(len( header))
        npstr =  '{:<15}'+'{:<15,.4f}'*(len( header)-1)
        print((pstr.format( *header )))
        for n, s in enumerate( seasons ):
            # Get vars for printing
            vars = [
            ( float( i.min() ), float( i.max() ),  \
            float( np.percentile( i.compressed(), 5)),  \
            float( np.percentile( i.compressed(), 95) ), \
            float( i.mean() ), \
            float( np.median( i.compressed() ) ),   \
            float( (i*s_area).sum()/s_area.sum() )   ) \
            for i in [ ars[n] ]
            ][0]
            # Print vars
            print((npstr.format( s,  *vars )))


# ----
# X.XX - Extract data by family for a given wd
# ----
def fam_data_extractor( wd=None, fam=None, trop_limit=True, ver='3.0', \
        annual_mean=True, t_ps=None, a_m=None, vol=None, res='4x5', \
        title=None, rtn_list=False, use_time_in_trop=True,\
        multiply_method=True,rtn_specs=False, verbose=False, rtn_units=False,\
        units=None, debug=False ):
    """
    Driver to extract data for a given family requested

    Parameters
    -------
    fam (str): "family" to extract ( e.g. NOy, NOx, POx, CH4 loss rate, ... )
    a_m (array): array of air mass
    vol (array): volumne of grid boxes
    trop_limit (boolean): limit output to "chemical troposphere" (level 38 )
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )
    rtn_specs (boolean): return list of species extracted?
    t_ps (array): time in the troposphere diganostic ( float values 0 to 1 )
    title (str): run title, ignore if not using halogen code
    ver (str): GEOSChem version with halogens (default = 3.0), ignore if not using halogen code

    definition of troposphere to use?
        - use_time_in_trop (boolean): time a given box is in the troposphere
        ( if use_time_in_trop=False, the level of the troposphere is used )
         - use a multiplication method, rather than masking for the arrays
         (aka set stratosphere to have zero values)

    Returns
    -------
    (array) and optionally names of species (list) and units (str)

    Notes
    -----
     - Used as families often have different units in diagnostics
     - to return species as list ( not fully implimented ) set rtn_list=True
     - to return species extract, set  rtn_species=True
     - this function should be used in preference to other bulk output
     extractors in this module.
    """
    func_call_str = 'fam_data_extractor called for ', fam, wd, title, res
    logging.info(func_call_str)
    if verbose: print(func_call_str)
    # --- Nitrogen Oxides NOx ( NO + NO2)
    if fam == 'NOx' :
        # Select species in family
        specs = [ 'NO2', 'NO' ]
        scale = 1E12
#        units, scale = tra_unit(specs[0], IUPAC_unit=True, scale=True)
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit )
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in [arr ] ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'pmol mol${^-1}$'
    # --- OH ( in molec/cm3 )
    elif fam == 'OH' :
        # Set specs list to just contain fam
        specs = [ fam ]
        arr = get_GC_output( wd=wd, vars=['CHEM_L_S__'+fam], \
            trop_limit=trop_limit )
        units = 'molec. cm$^{-3}$'
    # --- HO2 ( in v/v  )
    elif fam == 'HO2' :
        # Set specs list to just contain fam
        specs = [ fam ]
        arr = get_GC_output( wd=wd, vars=['CHEM_L_S__'+fam], \
            trop_limit=trop_limit )
        units = 'pmol mol$^{-1}$'
    # --- HOX
    elif fam == 'HOx' :
        # Set specs list to just contain fam
        specs = [ 'OH', 'HO2' ]
        # OH ( in molec/cm3 )
        OH_arr = get_GC_output( wd=wd, vars=['CHEM_L_S__'+'OH'], \
            trop_limit=trop_limit )
        # Get HO2
        HO2_arr = get_GC_output( wd=wd, vars=['CHEM_L_S__'+'HO2'], \
            trop_limit=trop_limit )
        # Convert HO2 to molec/cm3
        HO2_arr = convert_v_v_2_molec_cm3( HO2_arr, a_m=a_m, vol=vol, wd=wd, \
            res=res )
        # HOx ( HO + HO2)
        arr = OH_arr + HO2_arr
#        arr = OH_arr #+ HO2_arr
#        arr =  HO2_arr
        # units ?
#        units = 'molec. cm$^{-3}$'
        # convert to 1E6 molecules per cm3
        units = '1x10$^{6}$ molec. cm$^{-3}$'
        arr = arr / 1E6
    # --- Cl
    elif fam == 'Cl':
        # Set specs list to just contain fam
        specs = [ fam ]
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+'Cl' ], \
                    trop_limit=trop_limit )
        # if units already set, then convert to these
        if units == 'molec. cm$^{-3}$':
            # Convert HO2 to molec/cm3
            arr = convert_v_v_2_molec_cm3( arr, a_m=a_m, vol=vol, wd=wd, \
                res=res )
        # else return in v/v
        else:
            scale = 1E12
            units = 'pmol mol${^-1}$'
            arr = arr *scale
    # --- NOy
    elif fam == 'NOy' :
        # Select species in family
#        specs = GC_var('N_specs' )
#        if (ver == '3.0') or (ver == '4.0') :
#            if not any( [ (title != i) for i in 'NOHAL', 'BROMINE' ]):
#                specs  += ['ClNO2', 'ClNO3']
        specs = GC_var('NOy' )
#        units, scale = tra_unit(specs[0], IUPAC_unit=True, scale=True)
        scale =1E12
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='N') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'pmol mol${^-1}$'
    # --- All NIT (inc. HNO3)
    elif fam == 'NIT_ALL' :
        # Select species in family
        specs = 'HNO3', 'NIT', 'NITs'
        scale =1E12
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='N') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'pmol mol${^-1}$'
    # --- all sulfate
    elif fam == 'SO4' :
        # Select species in family
        specs = 'SO4', 'SO4s',
        scale =1E12
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='S') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'pmol mol${^-1}$'
    # --- all sulfate
    elif fam == 'NH4' :
        # Select species in family
#        specs = GC_var('NIT_ALL' )
        specs = 'NH4',
        scale =1E12
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='N') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'pmol mol${^-1}$'

    # --- Ozone (O3)
    elif fam == 'O3' :
        # Set specs list to just contain fam
        specs = [ fam ]
        # Select species in family
        units, scale = tra_unit(fam, IUPAC_unit=True, scale=True)
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+fam ], \
                    trop_limit=trop_limit )
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in [arr ] ])
        arr = arr *scale
        units = 'nmol mol${^-1}$'

    # Get Ox prod (POx/POX) ([molec/cm3/s])
    elif fam == 'POX' :
        # Set specs list to just contain fam
        specs = [ fam ]
        # Select species in family
        arr = get_GC_output( wd=wd, vars=['PORL_L_S__'+fam],
                    trop_limit=trop_limit )
        units = 'molec. cm$^{-3}$ s$^{-1}$'
    # Get Ox prod (POx/POX) ([molec/cm3/s])
    elif fam == 'CH4 loss' :
        # Set specs list to just contain fam
        specs = [ fam ]
        # Select species in family
        arr = get_CH4_lifetime( wd=wd, use_OH_from_geos_log=False,\
            average_value=False )
        # Want in units of yr^-1
        arr = 1/arr
        units = 'yr$^{-1}$'
    # ---  Inorganic bromine ( Bry )
    elif fam == 'Bry' :
        # Select species in family
        specs = GC_var('Bry' )
        # Also consider Br- on SS
#        specs += [ 'BrSALA', 'BrSALC', ]
        if ver == 'v11-1':
            specs.pop(specs.index('IBr'))
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='Br') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1)
        units = 'v/v'
    # ---  Inorganic iodine ( Iy )
    elif fam == 'Iy' :
        # Select species in family
        specs = GC_var('Iy' )
        # Also include iodine aerosol and CH3I
#        specs = GC_var('Iy' ) + ['AERI', 'ISALA', 'ISALC', 'CH3I' ]
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='I') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1)
        units = 'v/v'
    # ---  Inorganic iodine ( Cly )
    elif fam == 'Cly' :
        # Select species in family
        specs = GC_var('Cly' )
        if ver == 'v11-1':
            specs.pop(specs.index('ICl'))
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='Cl') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1)
        units = 'v/v'
    # ---  Reactive chlorine ( ClOx )
    elif fam == 'ClOx' :
        # Select species in family
        specs = ['Cl', 'ClO', 'Cl2O2', 'ClOO', ]
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='Cl') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1)
        units = 'v/v'
    # --- Nitrogen Oxides NOx ( NO + NO2)
    elif fam == 'VOC' :
        # Select species in family
        specs = [
        'ALK4', 'ISOP', 'ACET', 'MEK',  'ALD2', 'PRPE', 'C2H6', 'C3H8'
        ]
        scale = 1E9
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit )
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in [arr ] ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'nmol(C) mol${^-1}$'
    # --- Get PM2.5 (Approximation from gas-phase species )
    elif fam == 'PM2.5' :
        # Select species in family
        specs =[
    'BCPI', 'NH4', 'OCPI', 'SO4', 'BCPO', 'SALA', 'DST1', 'DST2', 'NIT', 'OCPO'
        ]
        # Extract data
        ars = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True )
        ars = convert_tracers2PM25( specs=specs, ars=ars )
        arr = np.array( ars )
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in [arr ] ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1) * scale
        units = 'ug m${^-3}$'
    # --- NOy
    elif fam == 'TNO3' :
        # Select species in family
        specs = ['HNO3', 'NIT', 'NITs']
        # Extract data
        arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+i for i in specs ], \
                    trop_limit=trop_limit, r_list=True  )
        # Adjust to stoichiometry
        arr = [ arr[n]*spec_stoich(i, ref_spec='N') \
             for n,i in enumerate( specs ) ]
        if debug:
            print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in arr  ])
        if not rtn_list:
            arr = np.ma.concatenate( [ i[...,None] for i in arr ], axis=-1 )
            arr = arr.sum( axis=-1)
        units = 'nmol mol${^-1}$'
    # --- Try extracting as a species rather than family?
    else:
        try:
            err_str = 'NO CASE SETUP FOR FAM={}, trying as spec'.format(fam)
            logging.info( err_str )
            arr = get_GC_output( wd=wd, vars=['IJ_AVG_S__'+fam ] )
            units, scaleby = tra_unit(fam, scale=True)
            arr= arr*scaleby
            # set the specs list to just be the family
            specs = [ fam ]
        except:
            err_str = 'No case for {} - PLEASE CHECK INPUT FAM OR ADD CASE'.format( fam )
            print( err_str )
            logging.info( err_str )

    if debug and (not rtn_list):
        print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in [arr ] ])
    # --- Mask for troposphere if t_ps provided (& trop_limit=True)
    if not isinstance( t_ps, type(None) ) and trop_limit:
        if rtn_list:
            arr = mask4troposphere( arr, t_ps=t_ps,  \
                use_time_in_trop=use_time_in_trop, \
                multiply_method=multiply_method, )
        else:
            arr = mask4troposphere( [arr], t_ps=t_ps, \
                use_time_in_trop=use_time_in_trop, \
                multiply_method=multiply_method  )[0]
    if debug and (not rtn_list):
        print([ ( i.shape, i.min(), i.max(), i.mean() ) for i in [arr ] ])
    # Take average (mean) over time? (if annual_mean==True)
    if annual_mean:
        if rtn_list:
            arr = [ i.mean( axis=-1 ) for i in arr ]
        else:
            arr = arr.mean( axis=-1 )
    # Return data and (optionally) specs
    if rtn_units:
        return arr, units
    if rtn_specs:
        return arr, specs
    else:
        return arr


# ----
# X.XX - Convert GC tracers to PM2.5
# ----
def convert_tracers2PM25( ars=[], specs=[], region='Europe' ):
    """
    Aproximate PM2.5 from PM2.5 ratios

    Parameters
    -------
    ars (list): list of arrays
    specs (list): list of species to convert
    region (str): region for which PM2.5 is being approximated? (RH differs)

    Returns
    -------
    (list)

    Notes
    -----
     - for details see GEOS-Chem wiki:
    http://wiki.seas.harvard.edu/geos-chem/index.php/Particulate_matter_in_GEOS-Chem#PM2.5_in_the_1-yr_benchmark_plots
    """
    # - Convert to PM2.5 ('$\mu$g m$^{-3}$')
    # Note. below list does not contain SOA species
    if region == 'USA':
        PM25_convertion_factor = {
        'NH4'  : 1.33,
        'NIT'  : 1.33,
        'SO4'  : 1.33,
        'BCPI' : 1.00, # no scaling
        'BCPO' : 1.00, # no scaling
        'OCPI' : 1.16*2.1,
        'OCPO' : 2.1,
        'DST1' : 1.00, # no scaling
        'DST2' : 0.38,
        'SALA' : 1.86,
        # Other species
        }
    elif region == 'Europe':
        PM25_convertion_factor = {
        'NH4'  : 1.51,
        'NIT'  : 1.51,
        'SO4'  : 1.51,
        'BCPI' : 1.00, # no scaling
        'BCPO' : 1.00, # no scaling
        'OCPI' : 1.24*2.1,
        'OCPO' : 2.1,
        'DST1' : 1.00, # no scaling
        'DST2' : 0.38,
        'SALA' : 2.42,
        # Other species
        }
    else:
        print('ERROR - Region not in list - please set available region!!')
        sys.exit()
    # RMM of air
    RMM_air = constants('RMM_air') # g/mol
    # assume standard air density
    # At sea level and at 15 °C air has a density of approximately 1.225 kg/m3
    #(0.001225 g/cm3, 0.0023769 slug/ft3, 0.0765 lbm/ft3) according to
    # ISA (International Standard Atmosphere).
    AIRDEN = 0.001225 # g/cm3
    # moles per cm3
    #  (1/(g/mol)) = (mol/g) ; (mol/g) * (g/cm3) = mol/cm3
    MOLS = (1/RMM_air) * AIRDEN
    # loop ars and convert to PM2.5 equiv
    for n, spec in enumerate( specs ):
        # moles * spec RMM * microgram
        # e.g. v/v * mols/cm3 = mols of X per cm3; / spec RMM = mass
        # unitless * mols * g/mol * conversion
        scale = MOLS * species_mass( spec ) *1E6 *1E6
        units = '$\mu$g m$^{-3}$'
        # convert...
        ars[n] = ars[n]*scale*PM25_convertion_factor[spec]
    return ars


# ----
# X.XX - Extract 2D data from *ts*bpch* files (e.g. hourly surface data)
# ----
def fam_data_extractor4ts_bpch_files(spec='NOy', wd=None, \
        filename='ts_ctm.nc'):
    """
    Driver to extract data requested ( as families have differing diagnostic units)

    Parameters
    ----------
    spec (str): species/tracer/variable name
    fam (str): "family" to extract ( e.g. NOy, NOx, POx, CH4 loss rate, ... )
    wd (str): the directory to search for file in

    Returns
    -------
    data (pd.DataFrame object) and units (str)
    """
    # --- Nitrogen Oxides NOx ( NO + NO2)
    non_IJ_AVG_specs = ['HOx', 'POX']
    if spec in non_IJ_AVG_specs :
        # --- OH ( in molec/cm3 )
#        if fam == 'OH' :
#           spec = 'OH'
#            arr = get_GC_output( wd=wd, vars=['CHEM_L_S__'+spec], \
#                trop_limit=trop_limit )
        # --- HOX
#        if fam == 'HOx' :
        print('NOT SETUP!!! for non_IG_AVG_specs')
        sys.exit()
    else:
        # setup list to store stoichiometry of species  in
        stioch4fam=[]
        # get specs to extract
        # ---  NO + NO2 ( NOx )
        if spec == 'NOx' :
            # Select species in family
            specs = [ 'NO2', 'NO' ]
#        scale = 1E12
#        units, scale = tra_unit(specs[0], IUPAC_unit=True, scale=True)
        # ---  Inorganic nitrogen ( NOy )
        elif spec == 'NOy' :
            specs = GC_var('NOy' )
            # get stiochiometry
            stioch4fam = [ spec_stoich(i, ref_spec='N') \
                for n,i in enumerate( specs ) ]
        # ---  Inorganic iodine ( Cly )
        elif spec == 'Cly' :
            specs = GC_var('Cly' )
            # get stiochiometry
            stioch4fam = [ spec_stoich(i, ref_spec='Cl') \
                for n,i in enumerate( specs ) ]
        # ---  Inorganic iodine ( Iy )
        elif spec == 'Iy' :
            specs = GC_var('Iy' )
            # get stiochiometry
            stioch4fam = [ spec_stoich(i, ref_spec='I') \
                for n,i in enumerate( specs ) ]
        # ---  Inorganic bromine ( Bry )
        elif spec == 'Bry' :
            specs = GC_var('Bry' )
            # get stiochiometry
            stioch4fam = [ spec_stoich(i, ref_spec='I') \
                for n,i in enumerate( specs ) ]
        # --- total nitrate TNO3 ( NO3 + NIT + NITs )
        elif spec == 'TNO3' :
            # Select species in family
            specs = [ 'HNO3', 'NIT', 'NITs' ]
        # --- nitrate aerosol ( NIT + NITs )
        elif spec == 'NIT+NITs' :
            # Select species in family
            specs = [ 'NIT', 'NITs' ]
        # --- anthropogenic aerosol ( NIT + NH4 + SO4 )
        elif spec == 'NIT+NH4+SO4' :
            # Select species in family
            specs = [ 'NIT', 'NH4', 'SO4' ]
        # --- total sulfate ( SO4, SO4s )
        elif spec == 'TSO4' :
            # Select species in family
            specs = [ 'SO4', 'SO4s' ]
        # --- total nitrate TNO3 ( NO3 + NIT + NITs )
        elif spec == 'PM2.5' :
            # Select species in family
            specs =[
    'BCPI', 'NH4', 'OCPI', 'SO4', 'BCPO', 'SALA', 'DST1', 'DST2', 'NIT', 'OCPO'
            ]
        # --- Try just extracting the provided species
        else:
            specs = [spec]
        # Get output for all speices
        data_l = []
        # "Open" NetCDF ... Metadata...
        with Dataset( wd+'/'+filename, 'r') as rootgrp:
           for fam_spec in specs:
                # Extract
                print(("Extracting spec='{}'".format( fam_spec )))
                data_ = rootgrp['IJ_AVG_S__'+fam_spec]
                print(('Extracted data:', data_))
                print(('data shape: ', data_.shape))
                # extract units - WARNING assuming same for all species
                units = data_.ctm_units
                # save extracted data to list
                data_l += [ data_[:] ]
        # Add stiochmetric scaling for species if applicable (from stioch4fam)
        if len(stioch4fam) > 0:
            data_l = [i*stioch4fam[n] for n, i in enumerate(data_l) ]
        # If PM2.5
        if spec == 'PM2.5':
            # get data and scale from ppbv (assumed) to v/v
            data_l = [ i/1E9 for i in data_l ]
            # v/v of tracers to ug/m3
            data_l = convert_tracers2PM25( specs=specs, ars=data_l )
            units = '$\mu$g m$^{-3}$'
        # If NIT+NH4+SO4
        if spec == 'NIT+NH4+SO4':
#        if False:
            for n, fam_spec in enumerate(specs):
                # get data and scale from ppbv to v/v
                data=data_l[n] /1E9
                # update data in list
                data_l[n] = convert_spec_v_v_2_ugm3( data=data, spec=fam_spec )
            # convert to ug m3
            units = '$\mu$g m$^{-3}$'
        # Sum family...
        data = np.array( data_l )
        data = data.sum( axis=0) #* scale
        logging.debug('Shape for array:{}, units={}'.format( data.shape, units))
        return data, units


# ----
# X.XX - Convert species from v/v to ug/m^3
# ----
def convert_spec_v_v_2_ugm3( spec=None, data=None, explicitly_caculate=False,
        press=None, T=None ):
    """
    Convert mixing ratio (v/v) to ug m^-3

    Parameters
    -------
    spec (str): species/tracer/variable name
    data (array): array of data
    press (float or array): pressure (hPa) as a float on array with size of data
    T (float or array): temperature (K) as a float on array with size of data

    Returns
    -------
    (array)
    """
    logging.info('convert_spec_v_v_2_ugm3 called for spec={}'.format(spec) )
    # Get Air density
    if explicitly_caculate:
        # calculate using provide pressions
        assert_str = 'variable ({}) needed to explicitly caculate!'
        assert not isinstance(press, type(None)), assert_str.format( 'press')
        assert not isinstance(T, type(None)), assert_str.format( 'T (Kelvin)')
        # Use the ideal gas law to calculate p (air density kg/m3)
        # press (pressure in hPa), T (temperature in Kelvin),
        # R (specific gas constant for dry air (J/(kg·K))),
        R = constants('Rdry')
        # Convert pressure to HPa=>Pa & kg=g concurrently
        AIRDEN = (press*100) / (R*1000 * T )
    else:
        # assume standard air density
        # At sea level and at 15 °C air has a density of
        # approximately 1.225 kg/m3
        # (0.001225 g/cm3, 0.0023769 slug/ft3, 0.0765 lbm/ft3) according to
        # ISA (International Standard Atmosphere).
        AIRDEN = 0.001225 # g/cm3
    # RMM of air
    RMM_air = constants('RMM_air') # g/mol (of dry air)
    # moles per cm3
    #  (1/(g/mol)) = (mol/g) ; (mol/g) * (g/cm3) = mol/cm3
    MOLS = (1/RMM_air) * AIRDEN
    # --- convert spec
    # v/v * mols/cm3 = mols of X per cm3;
    data *= MOLS
    # convert to grams of X per cm3; ( * RMM of species )
    data *= species_mass( spec )
    # convert to ug per cm3 (*1E6)
    data *= 1E6
    # convert to ug per m3 (*1E6)
    data *= 1E6
    units = '$\mu$g m$^{-3}$'
    # scale data and return
    return data


# ----
# X.XX - Extract timeseries data from *ts*bpch* files (e.g. hourly surface data)
# ----
def get_LOC_df_from_NetCDF(site=None, spec='O3', wd=None, res=None, \
        filename='ts_ctm.nc', LON=None, LAT=None, rtn_units=False, \
        LON_ind=None, LAT_ind=None, rtn_ctm_units=False,
        verbose=True, debug=False ):
    """
    Extract *ts*bpch* (1D) data from file for a specific site

    Parameters
    ----------
    spec (str): species/tracer/variable name
    fam (str): "family" to extract ( e.g. NOy, NOx, POx, CH4 loss rate, ... )
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )
    wd (str): the directory to search for file in
    stioch4fam (list): list of
    filename (str): name of NetCDF file to extract from
    rtn_units (boolean): return units
    rtn_ctm_units (boolean): return "ctm_units" (e.g. ppbC, instead of ppb)
    LON (float): londitude in units of degrees East
    LAT (float): londitude in units of degrees North
    LON_int (int): (Optional) londitude index of degrees East
    LAT_int (int): (Optional) londitude index of degrees North
    site (Str): name of a location (must be present in "get_loc" dictionary)

    Returns
    -------
    (pd.DataFrame object)
    """
    if debug:
        err_str = 'get_LOC_df_from_NetCDF called for {} ({},{}) ({},{})'
        err_str = err_str.format( site, LON, LAT, LON_ind, LAT_ind )
        print( err_str )
    # Get LAT and LON for site, if values not given.
    if any( [ isinstance(i, type(None)) for i in (LON, LAT) ] ):
        # Get LON and LAT for site if provided (from "get_loc" dictionary)
        try:
            LON, LAT, ALT = get_loc( loc=site )
        except KeyError:
            err_msg = 'SITE not defined in get_loc'
            print(err_msg)
            logging.info(err_msg)
            sys.exit()
        except:
            err_msg = 'LON+LAT or SITE must be provided!!!'
            print(err_msg)
            logging.info(err_msg)
            sys.exit()
    # Find index for grid box.
    if any( [ isinstance(i, type(None)) for i in (LON_ind, LAT_ind) ] ):
        LON_ind = get_gc_lon( LON, res=res, wd=wd, filename=filename )
        LAT_ind = get_gc_lat( LAT, res=res, wd=wd, filename=filename)
    # Extract data for location
    with Dataset( wd+'/'+filename, 'r') as rootgrp:
        data = rootgrp['IJ_AVG_S__'+spec]
        if verbose:
            print(('Extracted data:', data))
            print(('data shape: ', data.shape))
        # Extract for location (array shape = TIME, LON, LAT)
        data = data[:, LON_ind, LAT_ind]
        # Also extract NetCDF units
        # NOTE: iris.unit is deprecated in Iris v1.9. (using cf_units instead)
        try:
#            units = rootgrp['IJ_AVG_S__'+spec].units
#        except AttributeError:
            units = rootgrp['IJ_AVG_S__'+spec].cf_units
        except:
            units ='UNITS NOT IN FILE'
        try:
#             ctm_units = rootgrp['IJ_AVG_S__'+spec].ctm_units
#         except AttributeError:
            units = rootgrp['IJ_AVG_S__'+spec].cf_units
        except:
            units ='UNITS NOT IN FILE'

    # Extract dates in NetCDF
    dates = get_gc_datetime( filename=filename, wd=wd )
    # Make dataframe and return
    df = pd.DataFrame( data, index=dates, columns=[spec] )
    if rtn_units:
        return df, units
    elif rtn_ctm_units:
        return df, ctm_units
    else:
        return df

# ----
# X.XX - Convert v/v to molec/cm3
# ----
def convert_v_v_2_molec_cm3( arr=None, wd=None, vol=None, a_m=None, \
        mols=None, res='4x5', trop_limit=True, \
        explicitly_caculate=True, debug=False):
    """
    Covnerts mixing ratio (v/v) into number density (molec/cm3).

    Parameters
    ----------
    arr (array): arrray input
    a_m (array): array of air mass
    mols (array): array of molecule number density
    trop_limit (boolean): limit output to "chemical troposphere" (level 38 )
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )

    Returns
    -------
    (array)

    NOTES
    -------
    required variables of volume (vol) and airmass (a_m) can be provided as
    arguements or are extracted online (from provided wd )
    """
    logging.info('convert_v_v_2_molec_cm3 called for res={}'.format(res) )
    if explicitly_caculate:
        # Get volume ( cm^3  )
        if not isinstance(vol, np.ndarray):
            vol = get_volume_np( wd=wd, res=res, trop_limit=trop_limit, \
                debug=debug)
            logging.info( 'WARNING: extracting volume online' )
        # Get air mass ( kg )
        if not isinstance(a_m, np.ndarray):
            a_m = get_GC_output( wd, vars=['BXHGHT_S__AD'], \
                trop_limit=trop_limit, dtype=np.float64)
            logging.info( 'WARNING: extracting air mass online' )
        # Get moles
        if not isinstance(mols, np.ndarray):
            mols = a_m*1E3/constants( 'RMM_air')
        #  Convert to molecules
        arr = ( arr * mols )*constants('AVG')
        #  convert to per unit area ( molecs / cm^3  )
        arr = arr / vol
    # use an approximation assuming SATP
    else:
        # RMM
        RMM_air = constants('RMM_air') # g/mol
        # assume standard air density
        # At sea level and at 15 °C air has a density
        # of approximately 1.225 kg/m3
        #(0.001225 g/cm3, 0.0023769 slug/ft3, 0.0765 lbm/ft3) according to
        # ISA (International Standard Atmosphere).
        AIRDEN = 0.001225 # g/cm3
        # moles per cm3
        #  (1/(g/mol)) = (mol/g) ; (mol/g) * (g/cm3) = mol/cm3
        MOLS = (1/RMM_air) * AIRDEN
        # v/v * mols * AVG's # (to get molecules)
        arr = arr * MOLS * constants('AVG')
    return arr


# ----
# X.XX - Convert molec cm^-3 to v/v
# ----
def convert_molec_cm3_2_v_v( arr=None, wd=None, vol=None, a_m=None, \
        mols=None, res='4x5', trop_limit=True, press=None, T=None, \
        explicitly_caculate=False, debug=False):
    """
    Covnerts number density (molec/cm3) into mixing ratio (v/v).

    Parameters
    ----------
    arr (array): arrray input
    a_m (array): array of air mass
    mols (array): array of molecule number density
    trop_limit (boolean): limit output to "chemical troposphere" (level 38 )
    res (str): resolution of the model input (e.g. 4x5, 2x2.5 )
    press (array): pressure in hPa

    Returns
    -------
    (array)

    NOTES
    -------
    required variables of volume (vol) and airmass (a_m) can be provided as
    arguements or are extracted online (from provided wd )
    """
    logging.info('convert_molec_cm3_2_v_v called for res={}'.format(res) )
    # Get Air density
    if explicitly_caculate:
        # calculate using provide pressions
        assert_str = '{} needed to explicitly caculate!'
        assert not isinstance(press, type(None)), assert_str.format( 'press')
        assert not isinstance(T, type(None)), assert_str.format( 'T (Kelvin)')
        # Use the ideal gas law to calculate p (air density kg/m3)
        # press hPa), T (temperature in Kelvin),
        # R (specific gas constant for dry air (J/(kg·K))),
        R = constants('Rdry')
        # convert pressure to HPa=>Pa & kg=g concurrently
        AIRDEN = (press*100) / (R*1000 *  T )
    else:
        # assume standard air density
        # At sea level and at 15 °C air has a density of approximately 1.225 kg/m3
        # (0.001225 g/cm3, 0.0023769 slug/ft3, 0.0765 lbm/ft3) according to
        # ISA (International Standard Atmosphere).
        AIRDEN = 0.001225 # g/cm3
    # RMM ( g/mol )
    RMM_air = constants('RMM_air')
    # moles per cm3
    #  (1/(g/mol)) = (mol/g) ; (mol/g) * (g/cm3) = mol/cm3
    MOLS = (1/RMM_air) * AIRDEN
    # v/v * mols * AVG's # (to get molecules)
    # get moles/cm3 ( from molecules/cm3 )
    arr = arr/constants('AVG')
    # get mol/mol and remove cm3 by dividing by mol/cm3
    arr = arr /MOLS
    return arr


# ----
# X.XX - Mask non tropospheric boxes of 4D array
# ----
def mask4troposphere( ars=[], wd=None, t_ps=None, trop_limit=False, \
        t_lvl=None, masks4stratosphere=False, use_time_in_trop=True, \
        multiply_method=True, res='4x5', debug=False ):
    """ Mask for the troposphere using either the time in troposphere
    diagnostic ( use_time_in_trop=True ) or troposphere level
    ( use_time_in_trop=False )

    ARGUMENTS:
     - ars (list): arrays to apply masks to
     - t_ps: time in the troposphere diganostic ( float values 0 to 1 )
     - t_lvl: the model grid box level of the troposphere
     - trop_limit: limit output to "chemical troposphere" (level 38 )
     ( (boolean) options for this include using
     - multiply_method
     - definition of troposphere to use?
        - use_time_in_trop (boolean): time a given box is in the troposphere
        ( if use_time_in_trop=False, the level of the troposphere is used )
     - conbine_ars (boolean): return arrays as a single array?
     - month_eq (boolean): convert units to monthly equiivlents.
     - res: resolution of the model input (e.g. 4x5, 2x2.5 )

    NOTES:
     - The default option is not a mask. The time in troposphere (a fraction
        value 0-1) is simply multipled by the provided array.
     - The tropospause is diagnosed mulitple ways. This fucntion can mask
        for the troposphere using either time in trop ( use_time_in_trop=True )
        or tropopause level. Each array is done on a timestep by timestep basis.
     - The 'chemical troposphere' in GEOS-Chem is the boxes for which
        differential chemical equations are solved. Only these boxes (1st 38)
        are consdidered if trop_limit=True ( e.g. array shape is (72,46,38,12)
        instead of (72,46,47,12)
    """
    logging.info( 'mask4troposphere called for arr of shape: {},'.format( \
            ars[0].shape)  )
    logging.debug('mask4troposphere - with multiply method?={}' + \
        ',use_time_in_trop={}, type of t_lvl&t_ps:{}&{}'.format( \
        multiply_method, use_time_in_trop, type(t_lvl), type(t_ps) )  )
    # --- Get time tropopause diagnostic (if not given as argument)
    if not isinstance(t_ps, np.ndarray) and use_time_in_trop:
        t_ps = get_GC_output( wd, vars=['TIME_TPS__TIMETROP'], \
            trop_limit=trop_limit )
        if masks4stratosphere:
            # Extend to all full atmosphere ( 47 levels )
            a = list( get_dims4res(res) )
            a[-1] = 47-38
            a = np.zeros(  tuple( a+[t_ps.shape[-1]] ) )
            t_ps = np.ma.concatenate( (t_ps,a),  axis=-2 )
    # Get tropopause level (if not given as argument)
    if not isinstance(t_lvl, np.ndarray) and ( not use_time_in_trop):
        t_lvl = get_GC_output( wd, vars=['TR_PAUSE__TP_LEVEL'], \
            trop_limit=False )
    # ---  Multiply by fractional time in trop. array
    if multiply_method and use_time_in_trop:
        # Invert values if masking troposphere
        if masks4stratosphere:
            t_ps = 1 - t_ps
        # If 3D array with is given without a time dimension, average t_ps
        if len(ars[0].shape) == 3:
            t_ps = t_ps.mean(axis=-1)
        # Multiply fractional array by provided array
        ars = [i*t_ps for i in ars ]
    # ---  Mask by fractional time in trop. array
    elif (not multiply_method) and use_time_in_trop:
        # Mask area that are not exclusively stratospheric
        if masks4stratosphere:
            # mask troposphere
            t_ps = np.ma.masked_where( t_ps != 0, t_ps )
        # Mask area that are not exclusively tropospheric
        else:
            t_ps = np.ma.masked_where( t_ps != 1, t_ps )
    # ---  Mask using tropopause level diagnostic values
    else:
        # Setup dummy array with model numbers as values
        t_ps = np.zeros( ars[0].shape  )
        logging.debug( [ i.shape for i in (t_ps, t_lvl, ars[0]) ] )
        for i, n in enumerate( range(1,ars[0].shape[-2]+1) ):
            t_ps[:,:,i,:] =n
        if masks4stratosphere:
            # mask where the levels are greater that the tropopause level
            t_ps = np.ma.masked_where( t_ps<t_lvl[:,:,None,:], t_ps)
        else:
            # mask where the levels are greater that the tropopause level
            t_ps = np.ma.masked_where( t_ps>t_lvl[:,:,None,:], t_ps)
    # --- Set array mask to have strat mask (trop if masks4stratosphere=True)
    if (not multiply_method):
        for n, arr in enumerate( ars ):
            log_str = 'Using multiply_method={}, use_time_in_trop={}'
            logging.debug( log_str.format( multiply_method, use_time_in_trop ) )
            try:
                ars[n] = np.ma.array( arr, mask=t_ps.mask )
            except:
                if len(arr.shape) == 3:
                    logging.debug( 'using tps averaged over time' )
                    # Apply mask
                    ars[n] = np.ma.array( arr, mask=t_ps.mean(axis=-1).mask )
                else:
                    # Log error
                    log_str = 'Using multiply_method={}, use_time_in_trop={}'
                    log_str = log_str.format(multiply_method, use_time_in_trop )
                    logging.debug( log_str )
                    log_str = 'mask not applied for shapes',
                    log_str += str([i.shape  for i in (arr, t_ps)  ])
                    logging.debug( log_str )
                    sys.exit()
    return ars


# ----
# X.XX - Convert [molec/cm3/s ] to [molec/yr]
# ----
def convert_molec_cm3_s2_molec_per_yr( ars=None, vol=None ):
    """
    Takes a list of arrays (4D) and converts their units from molec/cm3/s to
    molec./yr

    Parameters
    -------
    ars (list): list of np.arrays
    vol (array): volume contained in each grid box (cm^-3)

    Returns
    -------
    (list)
    """
    # Loop provided arrays
    for n, arr in enumerate( ars ):
        # Times by volume
        ars[n]  = arr *vol
        # Convert /s to /yr
        ars[n] = arr *60*60*24*365
    return ars


# ----
# X.XX - Convert molec/cm3/s to g/s
# ----
def convert_molec_cm3_s_2_g_X_s( ars=None, specs=None, ref_spec=None, \
        months=None, years=None, vol=None, t_ps=None, trop_limit=True, \
        s_area=None, rm_strat=True, ctm_f=None, wd=None, res='4x5', \
        multiply_method=True, use_time_in_trop=True, conbine_ars=True, \
        month_eq=False, limit_Prod_loss_dim_to=38,
        verbose=False,  debug=False ):
    """
    Convert molec/cm3/s to g/grid box. This is used for converting prod/loss
    output units

    Parameters
    -------
    s_area (array): Surface array (array of values in metres)
    vol (array): volumne of grid boxes
    specs (list): species (Prod loss variaables from input.geos)
    months (list) and years (list): list of integer values for
    t_ps (array): time in the troposphere diganostic ( float values 0 to 1 )
    trop_limit (boolean): limit output to "chemical troposphere" (level 38 )
    rm_strat (boolean): mask out stratosphere
     ( (boolean) options for this include using multiply_method and use_time_in_trop )
    conbine_ars (boolean): return arrays as a single array?
    month_eq (boolean): convert units to monthly equiivlents.
    limit_Prod_loss_dim_to (int): level to cut off arrays at
     (38 in <v10, 59 in >=v11-1)

    Returns
    -------
    (array) of (list) of arrays if conbine_ars==True

    Notes
    -----
     - re-write of molec_cm3_s_2_Gg_Ox_np for clarity/split functionaltity
     - units of g/month can also be returned if month_eq=True
     - All functions that use "get_pl_in_Gg" should be updated to use this
     - It is most efficency to provide shared variables as arguements if this
        function is call more that once by a single driver
    """
    logging.info( 'convert_molec_cm3_s_2_g_X_s called' )
    # --- Extract core model variables not provide
    if (not isinstance(months, list)) and month_eq:
        months = get_gc_months( ctm_f, wd=wd )
    if (not isinstance(years, list)) and month_eq:
        years  = get_gc_years( ctm_f=ctm_f, wd=wd, set_=False )
    if isinstance( s_area, np.ndarray):
        s_area = get_surface_area( res=res, debug=debug )
    if not isinstance(vol, np.ndarray):
        vol = get_volume_np( ctm_f=ctm_f, s_area=s_area, wd=wd, res=res,\
             debug=debug )
        logging.info( 'WARNING: extracting volume online - inefficent' )
    logging.debug( [ (i.sum(), i.shape) for i in ars ] )
    # --- loop spec ars
    for n, arr in enumerate( ars ):
        # convert from molec/cm3/s to  molec/s
        # limit arrays to the region of the atmosphere in which prod/loss is
        # calculated (38 in <v10, 59 in >=v11-1)
        arr  = arr[...,:limit_Prod_loss_dim_to,:] * \
            vol[...,:limit_Prod_loss_dim_to,:]
        # conver to to molec/s = > Gg/s
        arr =  arr / constants( 'AVG') * species_mass(ref_spec)
        # to / yr
        if month_eq:
            day_adjust = d_adjust( months, years)
            ars[n] = arr * day_adjust
    logging.debug( [ (i.sum(), i.shape) for i in ars ] )
    # only consider troposphere ( update this to use mask4troposphere )
    if rm_strat:
        ars = mask4troposphere( ars,  t_ps=t_ps, wd=wd, trop_limit=trop_limit, \
            use_time_in_trop=use_time_in_trop, multiply_method=multiply_method )
    if debug:
        logging.debug( [ (i.sum(), i.shape) for i in ars ] )
        logging.debug( [ (i.sum(), i.shape) \
            for i in [ i[...,None] for i in ars ] ] )
        logging.debug( np.concatenate( [ i[...,None] for i in ars ], \
            axis=-1 ).shape )
    if conbine_ars:
        return np.concatenate( [ i[...,None] for i in ars ], axis=-1 )
    else:
        return ars

# ----
# X.XX - Print out stats on a list of 2D arrays in terms of masked areas
# ----
def prt_2D_vals_by_region( specs=None, res='4x5', arrs=None, prt_pcent=False, \
        add_total=False, months=list(range(12)), summate=True, \
        csv_title='regional_vals.csv', save2csv=False, \
        debug=False ):
    """
    Print values of a 2D (lon, lat) arry masked for regions
    """
    # Which regions?
    m_titles = [ 'Tropics', 'Mid lats', 'Extratropics', 'Oceanic', 'NH', 'SH' ]
    # Get maskes
    masks = [ mask_all_but( i, mask2D=True, trop_limit=True, res=res)  \
        for i in m_titles ]
    if debug:
        print([( m_titles[n] , i.shape ) for n, i in enumerate( masks ) ])
    # --- Average or total ?
    if add_total:
        arrs += [ np.ma.concatenate( [ i[...,None] for i in arrs ], \
            axis=-1 ).sum(axis=-1) ]
        specs += ['Total']
    # --- Print out actual values
    pstr  = '{:<25}'+'{:<15}'*( len(m_titles)-1 )
    pstrn = '{:<25}' +'{:<15,.3f}'*( len(m_titles)-1 )
    arrsn = [ 'Species', 'Total'] + m_titles
    print((m_titles, arrsn))
    print((pstr.format( *arrsn )))
    for n, s in enumerate( specs ):
        if summate:
            vars = [ s, np.ma.sum(arrs[n]) ]
            vars += [ np.ma.sum(arrs[n]*m) for m in masks ]
        else:
            vars = [ s, np.ma.mean(arrs[n]) ]
            vars += [ np.ma.mean(arrs[n]*m) for m in masks ]
        print((pstrn.format( *vars )))
    # --- Print out percent values
    if prt_pcent :
        print([i.shape for i in arrs ])
        if len(arrs[0].shape) == 4:
            s_arrs = [ (i/len(months)*12).sum(axis=2) for i in arrs ]
        else:
            s_arrs = arrs
        # update titles
        arrsn = [ 'Species', 'Run Total / Tg ','Yr. Equiv. / Tg'] + \
            [ '% '+i for i in m_titles ]
        # update numerical string to print
        pstr  = '{:<25}'+'{:<15}'*( len(arrsn)-1 )
        pstrn = '{:<25}' +'{:<15,.3f}'*( len(arrsn)-1 )
        print((pstr.format( *arrsn )))
        # loop maskes and print
        vars_l = []
        for n, s in enumerate( specs ):
            vars = [ s, np.ma.sum(arrs[n]), np.ma.sum(s_arrs[n]) ]
            vars += [ np.ma.sum(s_arrs[n]*m)/np.ma.sum(s_arrs[n])*100 \
                for m in masks ]
            vars_l += [ vars ]
            print((pstrn.format( *vars )))
        # --- Convert to DataFrame, then save to csv
        if save2csv:
            # construct df
            d = dict( list(zip( specs, [i[1:] for i in vars_l ] )) )
            df = pd.DataFrame( d ).T
            # assign titles to columns
            df.columns = arrsn[1:]
            # save to csv
            df.to_csv( csv_title )

# ----
# X.XX -
# ----
def get_2D_arr_weighted_by_X( arr, spec=None, res='4x5', print_values=False, \
        s_area=None):
    """
    Get weighted average 2D value by another array (e.g. area weighted)

    Parameters
    ----------
    arr (array): 2D array to average weighted by 2nd'y array (s_area)
    res (str): the resolution if wd not given (e.g. '4x5' )
    print_values (boolean): print calculated values
    s_area (array): array of areas of grid boxes (could be any variable)
    spec (str): species/tracer/variable name

    Returns
    -------
    (float)
    """
    # Get surface area if not provided
    if isinstance( s_area, type(None) ):
        s_area = get_surface_area( res )[...,0]  # m2 land map
    # Calculate average and area weighted average
    area_weighted_avg = ( arr*s_area ).sum()/ s_area.sum()
    if print_values:
        print(('mean surface {} conc {}'.format(spec, arr.mean() )))
        print(('area weighted mean surface {} conc {}'.format( \
            spec, area_weighted_avg )))
    return area_weighted_avg


# ----
# X.XX -
# ----
def get_avg_surface_conc_of_X( spec='O3', wd=None, s_area=None, res='4x5' ):
    """
    Get area weighted concentration of Y (mean over time)

    Parameters
    ----------
    s_area (array): array of areas of grid boxes (could be any variable)
    spec (str): species/tracer/variable name

    Returns
    -------
    (float)
    """
    # Get species concentration in v/v
    arr = get_GC_output( vars=['IJ_AVG_S__'+spec], wd=wd)[:,:,0]
    # Average over time
    arr = arr.mean( axis=-1 )
    # Get surface area if not provided
    if isinstance( s_area, type(None) ):
        s_area = get_surface_area( res )[...,0]  # m2 land map
    # Area weight and return
    return get_2D_arr_weighted_by_X( arr, s_area=s_area )


# ----
# X.XX -
# ----
def get_avg_trop_conc_of_X( spec='O3', wd=None, s_area=None, res='4x5',\
        vol=None, t_p=None, n_air=None, molecs=None, units='v/v', mols=None,\
        multiply_method=False, rm_strat=True, trop_limit=True, ctm_f=None,
        a_m=None, annual_mean=True, rtn_units=False ):
    """
    Get average (molecule weighted) concentration of Y (mean over time)

    Parameters
    ----------
    s_area (array): array of areas of grid boxes (could be any variable)
    spec (str): species/tracer/variable name

    Returns
    -------
    (float)
    """
    # Get species concentration in v/v
    arr = get_GC_output( vars=['IJ_AVG_S__'+spec], wd=wd, trop_limit=trop_limit)
    # convert units if 'units' argument != 'v/v'
    if units == 'v/v':
        pass
    elif units == 'molec/cm3':
        arr = convert_v_v_2_molec_cm3( arr, a_m=a_m, vol=vol, mols=mols, wd=wd )
    else:
        print ('unit ({}) conversion not setup'.format( units ) )
        sys.exit()
    # Average over time
    if annual_mean:
        arr = arr.mean( axis=-1 )
    # Area weight and return
    val =  molec_weighted_avg( arr, res=res, trop_limit=trop_limit, \
#        vol=vol, t_p=t_p, n_air=n_air, molecs=molecs,
        rm_strat=rm_strat, wd=wd, annual_mean=annual_mean)
    if rtn_units:
        return val, units
    else:
        return val


# ----
# X.XX - Get shared variables as a dictionary object.
# ----
def get_default_variable_dict( wd=None,
        full_vertical_grid=False, limit_vertical_dim=False ):
    """
    Get a dictionary of default analysis variables.

    Parameters
    ----
    full_vertical_grid (boolean): usings all levels of grid (e.g. 72 or 47)
    wd (str): Specify the wd to get the results from a run.

    Returns
    ----
    (dict)
    """
    # initialise dictionary
    Var_rc = {}
    # --- Get command line arguments as inputs?
    # Which working directory?
    if isinstance( wd, type(None) ):
        try:
            wd = sys.argv[1]
        except:
            wd = '/work/home/ts551/data/all_model_simulations/iodine_runs/'
            wd += 'iGEOSChem_5.0/run.Iodine.v1.0.red_timestep.XII.1month.tagged/'
    Var_rc['wd'] = wd
    if Var_rc['wd'][-1] != '/':
        Var_rc['wd']+='/'
    # What is the filename?
    try:
        Var_rc['filename'] = sys.argv[2]
    except:
        Var_rc['filename'] = 'ctm.nc'
    # Debug settings? (default = No )
    Var_rc['debug'] = False
    Var_rc['verbose'] = False
    # --- Analysis settings?
    # Consider just troposphere or consider full atmosphere?
    if full_vertical_grid:
        Var_rc['trop_limit'] = False # limit arrays to 38 levels...
        Var_rc['rm_strat'] = False # This is for convert_molec_cm3_s_2_g_X_s
        Var_rc['full_vertical_grid'] = full_vertical_grid # for get_dims4res
        Var_rc['limit_Prod_loss_dim_to'] = 59 # limit of levels for chemistry?
        Var_rc['limit_vertical_dim'] = limit_vertical_dim # apply dim. limiting?
    else:
        Var_rc['trop_limit'] = True # limit arrays to 38 levels...
        Var_rc['rm_strat'] = True # This is for convert_molec_cm3_s_2_g_X_s
        Var_rc['full_vertical_grid'] = full_vertical_grid # for get_dims4res
        Var_rc['limit_Prod_loss_dim_to'] = 38 # limit of levels for chemistry
        Var_rc['tight_constraints'] =  False # only consider boxes that are 100 % tropospheric
        if Var_rc['trop_limit']:
            Var_rc['limit_vertical_dim'] = True
        else:
            Var_rc['limit_vertical_dim'] = False
    return Var_rc


# ----
# X.XX - Get shared data variables as a dictionary object.
# ----
def get_shared_data_as_dict( Var_rc=None, var_list=[], \
        full_vertical_grid=False, Data_rc={} ):
    """
    Returns (requested) common vairables as a dictionary object. Give requested
    variables as a list of strings ("var_list").

    Parameters
    ----
    Var_rc (dict): dictionary containing variables for working directory ('wd')
    Data_rc (dict): dictionary containing model data (default intiallised empty)
    var_list (list): list of names (strings) of variables to extract
    full_vertical_grid (boolean): usings all levels of grid (e.g. 72 or 47)

    Returns
    ----
    (dict)
    """
    # Use default variable dictionary if non given
    if isinstance(Var_rc, type(None)):
        Var_rc = get_default_variable_dict(
            full_vertical_grid=full_vertical_grid )
    # --- Extract basic variables by default
    # Resolution?
    Data_rc['res'] = get_gc_res(wd=Var_rc['wd'], filename=Var_rc['filename'])
    # Version?
    iGC_ver, GC_version = iGEOSChem_ver(Var_rc['wd'], \
        also_return_GC_version=True )
    Data_rc['ver'] = iGC_ver
    Data_rc['GC_version'] = GC_version
    # Model output vertical grid - write this!
#    if 'output_vertical_grid' in var_list:
    Data_rc['output_vertical_grid'] = check_output_vertical_grid( \
        wd=Var_rc['wd'], filename=Var_rc['filename'])
    # ---  Now add specifically requested variables?
    # Add a reference 4x5 dir that has all generic output (e.g. N/AIR.)
    if 'generic_4x5_wd' in var_list:
        generic_4x5_wd = '/work/home/ts551/data/all_model_simulations/iodine_runs/'
        generic_4x5_wd += 'iGEOSChem_3.0_v10/run/'
        Data_rc['generic_4x5_wd'] = generic_4x5_wd
    # Months?
    if 'months' in var_list:
        Data_rc['months'] = get_gc_months(wd=Var_rc['wd'], \
            filename=Var_rc['filename'])
    # Years?
    if 'years' in var_list:
        Data_rc['years'] = get_gc_years(wd=Var_rc['wd'], \
            filename=Var_rc['filename'])
    # Datetime?
    if 'datetimes' in var_list:
        Data_rc['datetimes'] = get_gc_datetime( wd=Var_rc['wd'], \
            filename=Var_rc['filename'] )
    # Model output frequency?
    if 'output_freq' in var_list:
        Data_rc['output_freq'] = get_frequency_of_model_output( \
            wd=Var_rc['wd'], filename=Var_rc['filename'],
            datetimes=Data_rc['datetimes'], )
    # Surface area (m^2)
    dependacies_for_this_var = ['vol']
    if ('s_area' in var_list) or (dependacies_for_this_var in var_list):
        Data_rc['s_area'] = get_surface_area( Data_rc['res'] )
    # Volume (cm^3)
    if 'vol' in var_list:
        assert_str = "please add 's_area' to var_rc (dependent)"
        assert ('s_area' in var_list), assert_str
        Data_rc['vol'] = get_volume_np( wd=Var_rc['wd'], \
            trop_limit=Var_rc['trop_limit'],\
            s_area=Data_rc['s_area'][...,None], res=Data_rc['res'] )
    # Get time in troposphere diagnostic (fraction)
    if 't_ps' in var_list:
        Data_rc['t_ps'] = get_GC_output( Var_rc['wd'], \
            vars=['TIME_TPS__TIMETROP'], trop_limit=Var_rc['trop_limit'] )
    # Get N in air [molec air/m3]
    if 'n_air' in var_list:
        # variable name has just changed in v11
        Data_rc['n_air'] = get_number_density_variable( wd=Var_rc['wd'], \
            trop_limit=Var_rc['trop_limit'] )
        # Kludge! - restrict length of array to main wd.
        Data_rc['n_air'] = Data_rc['n_air'][...,:Data_rc['vol'].shape[-1]]
    # Pressure ? ( in hPa )
    if 'hPa' in var_list:
        Data_rc['hPa'] = get_GC_output( wd=Var_rc['wd'], \
            vars=['PEDGE_S__PSURF'])
    # Calculate molecules per grid box - [molec air]
    if 'molecs' in var_list:
        # (Note: volumne ('vol') is converted from [m^3] to [cm^3] concurrently)
        Data_rc['molecs'] = Data_rc['n_air'] * Data_rc['vol']/1E6
        # limit shape of array to prod/loss size (59 or 38)
        # Only if troposphere only run (with trop_limit=True) or
        # limit_vertical_dim=True
        if Var_rc['limit_vertical_dim'] or Var_rc['trop_limit']:
            Data_rc['molecs'] = Data_rc['molecs'][...,:Var_rc['limit_Prod_loss_dim_to'],:]
    # Air mass? ("a_m")
    if 'a_m' in var_list:
        Data_rc['a_m'] = get_air_mass_np( wd=Var_rc['wd'], \
            trop_limit=Var_rc['trop_limit'])
    # Altitude?
    if 'alt' in var_list:
        # Get altitude
        Data_rc['alt'] = gchemgrid('c_km_geos5')
        if Var_rc['trop_limit']:
            Data_rc['alt']  = Data_rc['alt'][:Var_rc['limit_Prod_loss_dim_to']]
        elif (Data_rc['output_vertical_grid'] == 'Full_72') and \
            (Var_rc['limit_vertical_dim']):
            Data_rc['alt'] = Data_rc['alt'][:Var_rc['limit_Prod_loss_dim_to']]
    # Latitude (lat) and longitude (lon)?
    if ('lon' in var_list) or ('lat' in var_list):
        # Why is this variable extracted from an offline dictionary?
        # UPDATE to use NetCDF coordinate variable.
        lon, lat, NIU = get_latlonalt4res( res=Data_rc['res'], wd=Var_rc['wd'],\
            full_vertical_grid=Var_rc['full_vertical_grid'],\
            filename=Var_rc['filename']  )
        Data_rc['lon'] = lon
        Data_rc['lat'] = lat
    # Tracer names? (aka those included in IJ_AVG_S__ diagnostic )
    if 'tracers' in var_list:
        with Dataset( Var_rc['wd']+Var_rc['filename'], 'r' ) as d:
            tracers = [i for i in d.variables if ('IJ_AVG_S__' in i)]
            tracers = [i.split('IJ_AVG_S__')[-1] for i in tracers ]
            Data_rc['tracers'] = tracers
    # Add a dictionary for converting between planeflight and input.geos names
    if 'tracers2planeflight' in var_list:
        Data_rc['tracers2planeflight'] = get_dict_of_tracers2planeflight_IDs(\
            wd=Var_rc['wd'])
    # Check all requested variables were extract? or call stop...
    vars_not_extracted = [i for i in var_list if i not in list(Data_rc.keys())]
    if len(vars_not_extracted) > 0:
        err_msg = 'NOT ALL VARS extracted! ({})'.format(vars_not_extracted)
        print(err_msg)
        logging.info(err_msg)
        sys.exit()
    return Data_rc


# ----
# X.XX -
# ----
def get_dict_of_tracers2planeflight_IDs( wd=None ):
    """
    Make dictionary of tracers and planeflight IDs from input.geos file
    """
    # Local variables
    filename ='input.geos'
    tracer_str = 'Tracer #'
    header_str ='Tracer Entries ------->'
    tracers_l = []
    tracer_num = []
    mwt_l =[]
    # Open file and read the lines with tracer infomation
    with open( wd+filename, 'rb') as file_:
        # Loop lines in file
        for line_ in file_:
            # Get header
            if header_str in line_:
                headers =line_[25:47]
            if tracer_str in line_:
                num, tracer, mwt = line_[25:47].strip().split()
                # Save tracer number
                tracer_num +=[num]
                # Save tracer name
                tracers_l +=[tracer]
                mwt_l+=[mwt]
    return dict( list(zip(tracers_l, tracer_num)) )


# ----
# X.XX -
# ----
def check_output_vertical_grid(wd=None, filename=None):
    """
    Return whether output contains full or reduced grid
    """
#    return 'Reduced_47'
    # TODO - Kludge for now.
    return 'Full_72'


# ----
# X.XX -
# ----
def process_to_X_per_s( spec=None, ars=None, tags=None, ref_spec=None,  \
        Var_rc=None, Data_rc=None, summate_routes=True, summate_altitudes=True):
    """
    Process arrays of molec/cm3/s to g(ref_spec)/s.

    Parameters
    ----
    Var_rc (dict): dictionary containing variables for working directory ('wd')
    var_list (list): list of names (strings) of variables to extract
    summate_altitudes (boolean): sum over altitude dimension
    summate_routes (boolean): sum all "routes" (all of arrays provided)
    Data_rc (dict): Data dictionary object (contains details on model data)
    Var_rc (dict): Variable dictionary object (contains analysis variabl deatail)

    Returns
    ----
    (array) or (list) of array (if summate_routes==True)
    """
    # Covert units based on whether model output is monthly
    if Data_rc['output_freq']=='Monthly':
        month_eq=True # use conversion in convert_molec_cm3_s_2_g_X_s
    else:
        month_eq=False
    # Convert to g X/s
    ars = convert_molec_cm3_s_2_g_X_s( ars=ars, ref_spec=ref_spec, \
        # shared settings...
        months=Data_rc['months'], years=Data_rc['years'],
        vol=Data_rc['vol'], t_ps=Data_rc['t_ps'], \
        trop_limit=Var_rc['trop_limit'], rm_strat=Var_rc['rm_strat'],
        # ... and function specific settings...
        month_eq=month_eq,
#        month_eq=False,
        conbine_ars=False )
    # Adjust for # of X in tag
    # is the broadcasting right here? should the array just be overwritten?
    ars = [ ars[n]* spec_stoich(tag, ref_spec=ref_spec)  \
        for n, tag in enumerate( tags ) ]
    # Summate altitudes
    if summate_altitudes:
        ars = [ i.sum(axis=2) for i in ars ]
    # Summate routes?
    if summate_routes:
        # add buffer dimension for broadcasting.
        ars = [ i[...,None] for i in  ars ]
        # concatenate and sum
        arr = np.ma.concatenate( ars, axis=-1 ).sum( axis=-1 )
        # return...
        return arr
    else:
        return ars


# ----
# X.XX -
# ----
def concvert_df_VOC_C2v( df=None, verbose=True ):
    """
    Convert VOC species in dataframt from ppbC/pptC to ppbv/pptv

    Parameters
    -------
    df (dataframe): pd dataframe containing timeseries data (tracers as columns)
    verbose (boolean): print verbose output?

    Returns
    -------
    (list)

    Notes
    -------
    """
    # List of GEOS-Chem pptC/ppbC species
    C_equiv_species = [
    'ALK4', 'ISOP', 'ACET', 'MEK',  'ALD2', 'PRPE',  'C2H6', 'C3H8'
    ]
    # Loop these and try and convert
    for spec in C_equiv_species:
        try:
            # is it in the dataframe? if so convert to C units
            df[spec] = df[spec] / spec_stoich( spec, C=True, \
                ref_spec='C' )
        except:
            if verbose:
                print(('Did not convert C/v to v/v for: ', spec))
    return df


# ----
# X.XX -
# ----
def process_bpch_files_in_dir2NetCDF(bpch_file_type="*tra*avg*",
        filename='ctm.nc', \
        folder=None, ext_str='_TEST_', file_prefix='ctm_',
        split_by_month=False, mk_single_NetCDF_file=True, \
        mk_monthly_NetCDF_files=False, mk_weekly_NetCDF_files=False,
        verbose=True):
    """
    Wrapper function to process ctm bpch files in folder to NetCDF file(s)

    Parameters
    -------
    bpch_file_type (str): str of standard file (wildcard) str with file naming structure
    filename (str): name of NetCDF file to make
    verbose (boolean): print verbose output?
    folder (str): directory address for folder contain files
    ext_str (str): extra str to inc. in monthly filenames
    file_prefix (str): prefox str to use for monthly split files
    split_by_month (boolean): split new NetCDF file by month? (post making file)
    mk_monthly_NetCDF_files (boolean): make a NetCDF per month of files
    mk_weekly_NetCDF_files (boolean): make a NetCDF per week of files

    Returns
    -------
    (None)

    Notes
    -------
    """
    logging.info('process_bpch_files_in_dir2NetCDF called for:', locals())
    from .bpch2netCDF import convert_to_netCDF
    import os
    import sys
    import time
    # Get folder from command line.
    if isinstance( folder, type(None)):
        folder = sys.argv[1]
        if folder[-1] != '/':
            folder+='/'
    # Get list of files
    files = glob.glob(folder+bpch_file_type)
    df = pd.DataFrame( files, columns=['folder+file'] )
    nfiles = len(files)
    if nfiles >0:
        if verbose: print(('Found {} files'.format(nfiles)))
    else:
        if verbose: print(('No files found in wd:{}'.format( folder )))
        sys.exit()
    # split off file names
    filenames = [i.split('/')[-1] for i in files ]
    df['filenames'] = filenames
    # Convert files on bulk or make files by month/week?
    if mk_monthly_NetCDF_files or mk_weekly_NetCDF_files:
        # get times of model out in file
        if bpch_file_type == "*ts*bpch*":
            filename_format = 'ts%Y%m%d.bpch'
        elif bpch_file_type == "*tra*avg*":
            # trac_rst.geosfp_2x25_tropchem.201308010000
            print('NOT SETUP!')
            sys.exit()
        elif bpch_file_type == "*ctm*bpch*":
            filename_format = 'ctm.bpch.%Y%m%d%m%s'
        else:
            print('NO CASE FOR {}'.format(bpch_file_type))
            sys.exit()
        # now extract start times of files
        intial_ts = [ time.strptime(i, filename_format) for i in filenames]
        df.index = time2datetime(intial_ts)
        df['month'] = df.index.month
        df['woy'] = df.index.weekofyear
        # Make files by month?
        if mk_monthly_NetCDF_files:
            for year in list( sorted( set( df.index.year ) ) ):
                # select files for given year
                df_year = df[ df.index.year == year ]
                for month in list( sorted( set( df_year.index.month ) ) ):
                    # select files for given month (within year)
                    df_month_tmp = df_year[ df_year.index.month == month ]
                    bpch_file_list= df_month_tmp['filenames'].values.tolist()
                    # add the month to the filename
                    filename4month = filename.split('.nc')[0]
                    filename4month +='_{}{:0>2}'.format(year, month)
                    if verbose: print((filename4month, df_month_tmp.shape))
                    # Convert to NetCDF all files to a single NetCDF
                    convert_to_netCDF( folder=folder, filename=filename4month, \
                        bpch_file_list=bpch_file_list,\
                        bpch_file_type=bpch_file_type )
        # Make files by week of year?
        elif mk_weekly_NetCDF_files:
            for year in list( sorted( set( df.index.year ) ) ):
                # select files for given year
                df_year = df[ df.index.year == year ]
                for week in list( sorted( set( df_year.weekofyear ) ) ):
                    # select files for given month (within year)
                    df_week_tmp = df_year[ df_year.index.month == week ]
                    bpch_file_list= df_week_tmp['filenames'].values.tolist()
                    # add the month to the filename
                    filename4month = filename.split('.nc')[0]
                    filename4month +='_{}{:0>2}.nc'.format(year, week)
                    if verbose: print((filename4month, df_week_tmp.shape))
                    # Convert to NetCDF all files to a single NetCDF
                    convert_to_netCDF( folder=folder, filename=filename4month, \
                        bpch_file_list=bpch_file_list,\
                        bpch_file_type=bpch_file_type )
        # Re-combine the split files into one file
        if mk_single_NetCDF_file:
            ncfiles = glob.glob( folder+'ts_ctm_*.nc' )
            # open files with xarray
            ds_l = [ xr.open_dataset(i) for i in ncfiles ]
            # make sure the time dimension is unlimitetd
            ds = xr.concat( ds_l, dim='time' )
            # now save the combined file
            ds.to_netcdf(folder+filename, unlimited_dims={'time_counter':True})
            # TODO: Now delete monthly files?
    # Convert files on bulk
    elif mk_single_NetCDF_file:
        print('WARNING - all files being convert to single NetCDF in one go!')
        # Convert to NetCDF all files to a single NetCDF
        convert_to_netCDF( folder=folder, filename=filename, \
            bpch_file_list=filenames, bpch_file_type=bpch_file_type )
    else: print('Please specify whether to make a sinlge or multiple .nc files')
    # If split by month
    if split_by_month:
        print(('Splitting NetCDF file by month - {}'.format(folder+filename)))
        split_NetCDF_by_month(folder=folder, filename=filename,
            ext_str=ext_str, file_prefix=file_prefix)
        print(('Split NetCDF file by month - {}'.format(folder+filename)))


# ----
# X.XX -
# ----
def process_all_bpch_files_in_dir(folder=None, ext_str=None):
    """
    Process all bpch files in a given directory
    (Warpper of process_bpch_files_in_dir2NetCDF for *ts*bpch* and *ctm*bpch*
    files)

    folder (str): directory address for folder contain files
    ext_str (str): extra str to inc. in monthly filenames

    Returns
    -------
    (None)
    """
    # - Process *ctm*bpch* files
    # Temporary variables
    bpch_file_type = '*ctm.bpch.*'
    filename = 'ctm.nc'
    file_prefix ='ctm_'
    # process *ctm*bpch* to NetCDF
    process_bpch_files_in_dir2NetCDF( folder=folder, filename=filename, \
        ext_str=ext_str, file_prefix=file_prefix, \
        bpch_file_type=bpch_file_type, split_by_month=True)
    # - Process *ts*bpch* files
    # Temporary variables
    bpch_file_type = 'ts*bpch*'
    filename = 'ts_ctm.nc'
    file_prefix ='ts_ctm_'
    # Process *ts*bpch* to netCDF4
    process_bpch_files_in_dir2NetCDF( folder=folder, filename=filename, \
        ext_str=ext_str, file_prefix=file_prefix, \
        bpch_file_type=bpch_file_type, split_by_month=True)


# ----
# X.XX -
# ----
def get_Lightning_NOx_source( Var_rc=None, Data_rc=None, debug=False ):
    """
    Extract Lightning NOx, convert units and return scaled to Tg(N) yr^-1

    Parameters
    -------
    Var_rc (dict): dictionary of variables (inc. working dir and filenname)
    Data_rc (dict): dictionary of variables (inc. res)
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    (np.array)
    """
    # Get NetCDF file
    d = Dataset( Var_rc['wd']+Var_rc['filename'], 'r')
    # Get Lightning
    arr = d['NO_LI_S__NO'][:]
    if debug: print(( arr.shape ))
    # Average over time
    arr = arr.mean(axis=0)
#    arr = arr[0,...]
#    months= 7, 8
#    arr = arr[[i-1 for i in months],...].mean(axis=0)
    if debug: print(( arr.shape ))
    # Sum over altitude
    arr_2D = arr.sum(axis=-1)
    if debug: print(( arr_2D.shape ))
    # Remove space dim
    s_area = get_surface_area( res=Data_rc['res'], debug=debug ) * 10000
    s_area_2D = s_area[...,0]
    # Get moles per s
    arr_mol_s = arr_2D * s_area_2D
    # Convert to Tg (N)
    a = ( arr_mol_s / constants('AVG') ) * species_mass( 'N' )  /1E12
    return (a *60 *60 *24 *365 )


# ----
# X.XX -
# ----
def move_spin_files_to_spin_up_folder( wd=None, spinup_dir=None ):
    """ move spin up spins into a seperate "spin_up" folder """
    import glob
    import shutil
    # Set spin-up directory and make (if not already present)
    if isinstance( spinup_dir, type(None)):
        spinup_dir = wd +'/spin_up/'
    if not os.path.exists(spinup_dir):
        os.makedirs(spinup_dir)
    # Get log files
    log_files = glob.glob( wd+'*geos.log*' )
    log_files += glob.glob( wd+'/logs/*geos.log*' )
    log_files += glob.glob( wd+'*hemco.log*' )
    log_files += glob.glob( wd+'/logs/*HEMCO.log*' )
    log_files += glob.glob( wd+'*log.log*' )
    log_files += glob.glob( wd+'/logs/*log.log*' )
    assert len(log_files) != set(log_files), 'double up in log filenames!'
    # Get output files too
    out_files = glob.glob( wd+'*trac*avg*' )
    out_files += glob.glob( wd+'*spec*avg*' )
    out_files += glob.glob( wd+'*ctm.bpch*' )
    out_files += glob.glob( wd+'*HEMCO_restart*' )
    out_files += glob.glob( wd+'*HEMCO_diagnostics*' )
    out_files += glob.glob( wd+'*info.dat*' )
    out_files += glob.glob( wd+'*GEOSChem_restart*' )
    out_files += glob.glob( wd+'/queue_files/*' )
    assert len(out_files) != set(out_files), 'double up in output filenames!'
    # get input files
    in_files = glob.glob( wd+'/input_files/*' )
    in_files += glob.glob( wd+'/queue_files/*' )
    assert len(out_files) != set(out_files), 'double up in output filenames!'
    # move files to "spin_up" folder
    d = {'log':log_files, 'output':out_files, 'input': in_files}
    for key in d.keys():
        files = d[key]
        print('moving {} {} files'.format( len(files), key ) )
        just_names = [i.split('/')[-1] for i in files ]
        fails = []
        for n_file, file in enumerate( files ):
            try:
                shutil.move(file, spinup_dir+just_names[n_file])
            except:
                fails += [ file ]
        if len( fails ) > 0 :
            print( 'FAILED to move: {}'.format( fails ) )
        print('moved {} {} files'.format( len(d[key])-len(fails), key ) )


# ----
# X.XX -
# ----
def clean_run_dir4monthly_run( wd=None,
        edate = datetime.datetime(2014, 1, 1, 0),
        sdate = datetime.datetime(2013, 1, 1, 0), debug=False ):
    """ Remove existing model output and input files """
    import shutil
    import os
    # Spinup  directory
    spinup_dir= wd +'/spin_up/'
    # Move the spin up files to a seperate spin up folder
    move_spin_files_to_spin_up_folder(wd=wd, spinup_dir=spinup_dir )
    # Remove temporary files
    [ os.remove(i) for i in glob.glob(wd+'*~') ]
    # Remove the old input.geos file (symbolically linked)
    try:
        os.unlink( wd+'input.geos' )
    except:
        print( 'FAILED to unlinke input.geos (from input_files folder)' )
    # Try and replace it with the input.geos.org
    try:
        shutil.move( wd+'input.geos.orig', wd+'input.geos')
    except:
        print( 'FAILED to replace input.geos with input.geos.orig' )
    # Sym link the last file spun up file to start the new run
    file_strs = [
    'GEOSChem_restart.{}{:0>2}{:0>2}0000.nc',
    'HEMCO_restart.{}{:0>2}{:0>2}0000.nc'
    ]
    oldfiles = [i.format(edate.year, edate.month, edate.day) for i in file_strs]
    newfiles = [i.format(sdate.year, sdate.month, sdate.day) for i in file_strs]
    for nfile, file in enumerate( oldfiles ):
        if debug: print( spinup_dir+file, wd+newfiles[nfile] )
        try:
            os.symlink(spinup_dir+file, wd+newfiles[nfile])
        except:
            prt_str = 'FAILED to sym link new restart files to spin up ones {}'
            print( prt_str.format( file ) )


# ----
# X.XX - print stats on model run times
# ----
def get_model_run_stats( wd=None, file_type='*geos.log*', debug=False ):
    """ Get model stats (e.g runtime) """
    # Get log files
    logging.debug('get_model_run_stats called for wd={}'.format(wd))
    # --- Find all geos log files in directory...
    files = glob.glob( wd+'/'+file_type )
    if len(files) < 1:
        err_str = 'WARNING! - no files found (assuming type={})'
        logging.info( err_str.format(file_type) )
        print( err_str.format(file_type) )
        files = glob.glob( wd+'/logs/'+file_type )
        if len(files) < 1:
            err_str = 'WARNING! - no files found (type={} in wd/log/*)'
            logging.info( err_str.format(file_type) )
            # try
            file_type = 'log.*'
            files = glob.glob( wd+'/logs/'+file_type )
            print( 'Loooking for {} files instead'.format( file_type)  )
            if len(files) < 1:
                err_str = 'WARNING! - no files found (type={} in wd/log/*)'
                logging.info( err_str.format(file_type) )
    # --- If there are any, then
    if len(files) > 1:
        # Define some variable names
        Rstart = 'Real Start'
        Rend = 'Real End'
        Mend = 'Model End'
        Mstart = 'Model Start'
        Mtime = 'Model time (days)'
        Rtime = 'Real time (hours)'
        vars4df = [ Rstart, Rend, Mend, Mstart, ]
        # Loop and extract OH means, take an average if n>0
        filenames = [i.split('/')[-1] for i in files]
        for n_file, file in enumerate( files ):
            d = {}
            with open(file) as f:
                if debug: print((file, f))
                for line in f:
                    if '=> SIMULATION ' in line:
                        date = line.split('TIME:')[1][:-5].strip()
                        date = time.strptime( date, '%Y/%m/%d %H:%M' )
                        if 'START' in line:
                            d[Rstart] = time2datetime( [date] )[0]
                        if 'END' in line:
                            d[Rend] = time2datetime( [date] )[0]
                    elif 'Start time of run' in line:
                        sdate = line[30:].strip()
                        sdate = time.strptime( sdate, '%Y%m%d %H%M%S' )
                        d[Mstart] = time2datetime( [sdate] )[0]
                    elif 'End time of run' in line:
                        edate = line[30:].strip()
                        edate = time.strptime( edate, '%Y%m%d %H%M%S' )
                        d[Mend] = time2datetime( [edate] )[0]
                if all([i in d.keys() for i in vars4df]):
                    # Add differences
                    d[Mtime] = (d[Mend]-d[Mstart]).total_seconds() / 60 /60 / 24
                    d[Rtime] = (d[Rend]-d[Rstart]).total_seconds() / 60 /60
                    # keys
                    keys = vars4df + [Mtime, Rtime]
                    try:
                        df[ filenames[n_file] ] = [ d[i] for i in keys ]
                    except:
                        df = pd.DataFrame( index=keys )
                else:
                    print('Exc. incomplete file: {}'.format(filenames[n_file]) )
        # - Now calculate some stats
        df = df.T
        # Get average times
        AvgMtime = df[Mtime].mean()
        AvgRtime = df[Rtime].mean()
        # Print model output frequency
        prt_str = 'Model output freg. = {:.2f} days (min={}, max={})'
        print( prt_str.format( AvgMtime, df[Mtime].min(), df[Mtime].max() ) )
        # Print time taken for model output
        prt_str = 'Time taken per Model output = {:.2f} hours (min={}, max={})'
        print( prt_str.format( AvgRtime, df[Rtime].min(), df[Rtime].max() ) )
        # print model
        prt_str = 'Avg. Model days per Real hour = {:.2f}'
        print( prt_str.format( AvgMtime/AvgRtime ) )

    else:
        print('No *log files found! (folder:{})'.format(wd) )
        sys.exit()

# ----
# X.XX -
# ----
def get_general_stats4run_dict_as_df( run_dict=None, extra_str='', REF1=None, 
            REF2=None, REF_wd=None, res='4x5', trop_limit=True, 
            save2csv=True, prefix='GC_', run_names=None, debug=False ):
    """ 
    Get various stats on a set of runs in a dictionary ({name: location})
    
    Parameters
    ----------
    run_dict (dict): dicionary of run names and locations 
    run_names (list): provide the names of run_dict keys to order df index
    REF_wd (str): name of run in dictionary to use to extract shared variables 
    REF1 (str): name of (1st) run in dictionary to to % change calculations from
    REF1 (str): name of (2nd) run in dictionary to to % change calculations from
    prefix (str):  string to include as a prefix in saved csv's filename
    extra_str (str):  string to include as a suffx in saved csv's filename
    res (str): reolusiotn of model run (e.g. 4x5)
    save2csv (boolean): save dataframe as a csv file
    trop_limit (boolean): limit analysis to the troposphere?

    Returns
    -------
    (colormap)

    Notes
    -----    
    
    """
    # Extract names and locations of data 
    if isinstance( run_names, type(None) ):
        run_names = sorted(run_dict.keys())
    wds = [ run_dict[i] for i in run_names ]
    # mass unit scaling
    mass_scale = 1E3
    mass_unit = 'Tg'
    # v/v scaling?
    ppbv_unit = 'ppbv'
    ppbv_scale = 1E9
    pptv_unit = 'pptv'
    pptv_scale = 1E12
    # Get shared variables from a single model run
    if isinstance( REF_wd, type(None) ):
        REF_wd = wds[ 0 ]
    # get time in the troposphere diagnostic
    t_p = AC.get_GC_output( wd=REF_wd, vars=[u'TIME_TPS__TIMETROP'], \
        trop_limit=True)
    # Temperature
    K = AC.get_GC_output( wd=REF_wd, vars=[u'DAO_3D_S__TMPU'], trop_limit=True)        
    # airmass
    a_m = AC.get_air_mass_np( wd=REF_wd, trop_limit=True )
    # Surface area?
    s_area = AC.get_surface_area( res )[...,0]  # m2 land map

    # ----  ----  ----  ----  ----  ----  ----
    # ---- Now build analysis in pd.DataFrame

    # ---- Tropospheric burdens?
    # Get tropospheric burden for run
    varname = 'O3 burden ({})'.format(mass_unit)
    ars = [ AC.get_O3_burden(i, t_p=t_p).sum() for i in wds ]
    df = pd.DataFrame( ars, columns=[varname], index=run_names )

    # Get NO2 burden
    NO2_varname = 'NO2 burden ({})'.format(mass_unit)
    ars = [ AC.get_trop_burden( spec='NO2', t_p=t_p, wd=i, all_data=False).sum()
        for i in wds ]
    # convert to N equivalent
    ars = [i/AC.species_mass('NO2')*AC.species_mass('N') for i in ars]
    df[NO2_varname] = ars

    # Get NO burden
    NO_varname = 'NO burden ({})'.format(mass_unit)
    ars = [ AC.get_trop_burden( spec='NO', t_p=t_p, wd=i, all_data=False).sum()
        for i in wds ]
    # convert to N equivalent
    ars = [i/AC.species_mass('NO')*AC.species_mass('N') for i in ars]
    df[NO_varname] = ars

    # Combine NO and NO2 to get NOx burden
    NOx_varname = 'NOx burden ({})'.format(mass_unit)
    df[NOx_varname] = df[NO2_varname] + df[NO_varname]

    # Get NIT burden
    NIT_varname = 'NIT burden ({})'.format(mass_unit)
    ars = [ AC.get_trop_burden( spec='NIT', t_p=t_p, wd=i, all_data=False).sum()
        for i in wds ]
    # convert to N equivalent
    ars = [i/AC.species_mass('NIT')*AC.species_mass('N') for i in ars]
    df[NIT_varname] = ars

    # Get NITs burden
    NITs_varname = 'NITs burden ({})'.format(mass_unit)
    ars = [ AC.get_trop_burden(spec='NITs', t_p=t_p, wd=i, all_data=False).sum()
        for i in wds ]
    # convert to N equivalent
    ars = [i/AC.species_mass('NITs')*AC.species_mass('N') for i in ars]
    df[NITs_varname] = ars

    # sum NIT+NITs
    varname = 'NIT+NITs burden ({})'.format(mass_unit)
    df[varname] = df[NITs_varname] + df[NIT_varname]

    # Get N2O5 burden
    NITs_varname = 'N2O5 burden ({})'.format(mass_unit)
    ars = [AC.get_trop_burden(spec='N2O5', t_p=t_p, wd=i,  all_data=False).sum()
        for i in wds ]
    # convert to N equivalent
    ars = [i/AC.species_mass('N2O5')*AC.species_mass('N') for i in ars]
    df[NITs_varname] = ars

    # Scale units
    for col_ in df.columns:
        if 'Tg' in col_:
            df.loc[:,col_] = df.loc[:,col_].values/mass_scale

    # ---- Surface concentrations?
    # Surface ozone
    O3_sur_varname = 'O3 surface ({})'.format(ppbv_unit)
    ars = [ AC.get_avg_surface_conc_of_X( spec='O3', wd=i, s_area=s_area) \
        for i in wds ]
    df[O3_sur_varname] = ars

    # Surface NOx
    NO_sur_varname = 'NO surface ({})'.format(ppbv_unit)
    ars = [ AC.get_avg_surface_conc_of_X( spec='NO', wd=i, s_area=s_area) \
        for i in wds ]
    df[NO_sur_varname] = ars
    NO2_sur_varname = 'NO2 surface ({})'.format(ppbv_unit)
    ars = [ AC.get_avg_surface_conc_of_X( spec='NO2', wd=i, s_area=s_area) \
        for i in wds ]
    df[NO2_sur_varname] = ars
    NOx_sur_varname = 'NOx surface ({})'.format(ppbv_unit)
    df[NOx_sur_varname] =  df[NO2_sur_varname]+ df[NO_sur_varname]

    # Surface N2O5
    N2O5_sur_varname = 'N2O5 surface ({})'.format(pptv_unit)
    ars = [ AC.get_avg_surface_conc_of_X( spec='N2O5', wd=i, s_area=s_area) \
        for i in wds ]
    df[N2O5_sur_varname] = ars

    # ---- OH concentrations?
    # first process the files to have different names for the different years
    try:
        OH_global_varname = 'Global mean OH'
        ars = [ AC.get_OH_mean(i) for i in wds ]
        df[OH_global_varname] = ars
    except:
        print('Unable to add OH values - please check the file directory! ')

    # ---- CH4 concentrations?
    try:
        CH4_lifetime_varname = 'CH4 lifetime (yr)'
        ars = [ AC.get_CH4_lifetime( wd=i, use_OH_from_geos_log=False, K=K, \
            t_ps=t_p, average_value=True, use_time_in_trop=True, a_m=a_m )
            for i in wds ]
        df[CH4_lifetime_varname] = ars
    except:
        print('Unable to add CH4 lifetimes - please check the file directory! ')

    # ---- Scale units
    for col_ in df.columns:
        if 'ppbv' in col_:
            df.loc[:,col_] = df.loc[:,col_].values*ppbv_scale
        if 'pptv' in col_:
            df.loc[:,col_] = df.loc[:,col_].values*pptv_scale

    # ---- Processing and save?
    # Calculate % change from base case for each variable
    if not isinstance(REF1, type(None) ):
        for col_ in df.columns:
            pcent_var = col_+' (% vs. {})'.format( REF1 )
            df[pcent_var] = ( df[col_]-df[col_][REF1] ) / df[col_][REF1] *100
    if not isinstance(REF2, type(None) ):
        for col_ in df.columns:
            pcent_var = col_+' (% vs. {})'.format( REF2 )
            df[pcent_var] = ( df[col_]-df[col_][REF2] ) / df[col_][REF2] *100

    # Re-order columns
    df = df.reindex_axis(sorted(df.columns), axis=1)
    # Reorder index 
    df = df.T.reindex_axis(sorted(df.T.columns), axis=1).T
    # Now round the numbers
    df = df.round(3)
    # Save csv to disk
    csv_filename = '{}_summary_statistics{}.csv'.format( prefix, extra_str )
    df.to_csv(csv_filename)    

    # return the DataFrame too
    return df

# ------------------ Section X.X -------------------------------------------
# -------------- Smvgear input/output file Processing
#


def prt_Prod_Loss_list4input_geos(spec_list=None, prefix_list=None, start_num=1):
    """
    Print to screen lines to be inserted into input.geos to track prod/loss of species

    Parameters
    -------
    spec_list (list): list of species to print lines for
    start_num (int): number to start labeling reaction index for input.geos
    prefix_list (list): list of prefixs to dictacte if prod or loss calc ("P" or "L")

    Returns
    -------
    (None)

    Notes
    -------
    """
    # Formatted string to be filled by variables
    line_str = '{:<6}chemical family   : {}: {}'
    # Activity for species?
    if isinstance(prefix_list, type(None)):
        prefix_list =['P']* len(spec_list)
    # Loop species (specs) provided
    for n, spec in enumerate( spec_list ):
        index = start_num+n
        print(( line_str.format( get_suffix(index), prefix_list[n]+spec, spec) ))


def prt_Species_List_lines4globchem_dat(spec_list=None, activty_list=None):
    """
    Print to screen lines to be inserted into globchem.dat for given
    list of species

    Parameters
    -------
    spec_list (list): list of species to print lines for
    acvtivty_list (list): list of activitys ("A"=Active, "L"=live, "D"=Dead)

    NOTES
    -------
    - Globchem.dat contains the chemistry for the smvgear solver.
    - These lines must be present at the top to initialise each species
    """
    line1_str ='{} {:<10}         1.00 1.000E-20 1.000E-20 1.000E-20 1.000E-20'
    line2_str ='                     0   0   0   0   0   0   0   0   0     '
    # Activity for species?
    if isinstance(activty_list, type(None)):
        activty_list =['A']* len(spec_list)
    # Print lines to insert into globchem.dat
    for n, spec in enumerate( spec_list ):
        print(( line1_str.format( acvtivty_list[n], spec ) ))
        print( line2_str )


# ------------------ Section X.X -------------------------------------------
# -------------- KPP input/output file Processing
#

# --------------
# -------------- Funcs specifically for v11-1g and later
# (tested on v11-2d-R1,v11-2d-R2, v11-2d-R3...)


def get_fam_prod_loss_for_tagged_mechanism( wd=None, fam='LOx', ref_spec='O3',\
        tags=None, RR_dict=None, Data_rc=None, Var_rc=None, tags2_rxn_num=None,\
        RR_dict_fam_stioch=None, region=None, rm_strat=False, \
        weight_by_num_molecules=False, verbose=True, debug=False):
    """
    Extract prod/loss for family from wd and code directory

    Parameters
    -------
    fam (str): tagged family to track (already compiled in KPP mechanism)
    ref_spec (str): reference species to normalise to
    region (str): region to consider (by masking all but this location)
    wd (str): working directory ("wd") of model output
    debug, verbose (bool): switches to turn on/set verbosity of output to screen
    RR_dict (dict): dictionary of KPP rxn. mechanism (from get_dict_of_KPP_mech)
    RR_dict_fam_stioch (dict): dictionary of stoichiometries for
        get_stioch_for_family_reactions
    tags2_rxn_num (dict): dicionary mapping tags to reaction numbers
    tags (list): list of prod/loss tags to extract
    Var_rc (dict): dictionary containing variables for working directory ('wd')
        ( made by AC_tools' get_default_variable_dict function)
    Data_rc (dict): dictionary containing model data
        (made by AC_tools' get_shared_data_as_dict function )
    rm_strat (boolean): (fractionally) replace values in statosphere with zeros
    weight_by_num_molecules (boolean): weight grid boxes by number of molecules

    Returns
    -------
    (None)
    """
    # --- Get tags
    # Get dictionaries (reaction, tags, stoichiometry ) if not provided
    if isinstance( RR_dict, type(None) ):
        RR_dict = get_dict_of_KPP_mech( wd=CODE_wd,
            GC_version=Data_rc['GC_version' ], Mechanism=Mechanism )
        if debug: print( len(RR_dict), [RR_dict[i] for i in RR_dict.keys()[:5]])
    if isinstance( tags2_rxn_num, type(None) ):
        tags2_rxn_num = {v: k for k, v in tags_dict.items()}
    if isinstance( RR_dict_fam_stioch, type(None)):
        RR_dict_fam_stioch = get_stioch_for_family_reactions(
            fam=fam, RR_dict=RR_dict, Mechanism=Mechanism )
    # --- Get data
    # get prod/loss arrays
    ars = get_GC_output( wd=Var_rc['wd'], r_list=True,\
        vars=['PORL_L_S__'+i for i in tags ], trop_limit=Var_rc['trop_limit'])
    # limit prod/loss vertical dimension?
    limit_Prod_loss_dim_to = Var_rc[ 'limit_Prod_loss_dim_to' ]
    # Covert units based on whether model output is monthly
    if Data_rc['output_freq'] == 'Monthly':
        month_eq=True # use conversion in convert_molec_cm3_s_2_g_X_s
    else:
        month_eq=False
    # Now convert the units (to G/s)
    ars = convert_molec_cm3_s_2_g_X_s( ars=ars, ref_spec=ref_spec, \
        # shared settings...
        months=Data_rc['months'], years=Data_rc['years'],
        vol=Data_rc['vol'], t_ps=Data_rc['t_ps'], \
        trop_limit=Var_rc['trop_limit'], rm_strat=Var_rc['rm_strat'],
        # there are 59 levels of computation for P/l in v11-1+ (so limit to 59)
        limit_Prod_loss_dim_to=limit_Prod_loss_dim_to,
        # ... and function specific settings...
        month_eq=month_eq,
        conbine_ars=False )
    # Add stoichiometric scaling (# of Ox losses per tagged rxn. )
    ars = [ i*RR_dict_fam_stioch[tags2_rxn_num[tags[n]]] \
        for n,i in enumerate(ars)]
    # Scale to annual
    if Data_rc['output_freq'] == 'Monthly':
        # Should this be summated then divided adjusted to time points.
        # sum over time
        ars = [i.sum(axis=-1) for i in ars ]
        # Adjust to equivalent months.
        ars = [i/len(Data_rc['months'])*12 for i in ars ]
    else:
        # Average over time?
        ars = [i.mean(axis=-1) for i in ars ]
        # Scale to annual
        ars = [i*60.*60.*24.*365. for i in ars]
    # Get time in troposphere diagnostic
    print( Data_rc['t_ps'].shape )
    print( Data_rc['t_ps'].mean(axis=-1).shape )
    t_ps = Data_rc['t_ps'].mean(axis=-1)[...,:limit_Prod_loss_dim_to]
    # Check tropospheric LOx total
    arr = np.ma.array( ars )
    print( arr.shape, t_ps.shape, limit_Prod_loss_dim_to )
    LOx_trop = ( arr* t_ps[None,...]).sum()/ 1E12
    if verbose: print( 'Annual tropospheric Ox loss (Tg O3): ', LOx_trop )
    # Remove the stratosphere by multiplication through by "time in troposphere"
    if rm_strat:
        ars = [ i*t_ps for i in ars ]
    # Select data by location or average globally?
    if not isinstance(region, type(None)):
        # also allow for applying masks here...
        print( 'NOT SETUP!!!')
        sys.exit()
    else:
        if weight_by_num_molecules:
            ars = [ molec_weighted_avg( i, weight_lon=True, res=Data_rc['res'],\
                weight_lat=True, wd=Var_rc['wd'],\
                trop_limit=Var_rc['trop_limit'], rm_strat=Var_rc['rm_strat'], \
                # provide shared data arrays averaged over time...
                molecs=Data_rc['molecs'].mean(axis=-1), t_p=t_ps ) \
                for i in ars ]
    if debug: print( [i.shape for i in ars ])
    return ars


# -------------- Functions to produce KPP ***input*** file(s)
# ----
# X.XX -
# ----
def print_out_dfs2KPP_eqn_file( species_df=None, headers=None,
        extr_str='OUTPUT', rxn_dicts=None ):
    """ print out DataFrames to *.eqn file """
    # ---- Create KPP Mechanism file to save lines to
    a=open('{}.eqn'.format(extr_str),'w')
    # ---  Print headers to file (list of strings)
    for line in headers:
        print(line.replace('\n', ''), file=a)
    # ----  Print species to file
    print( '', file=a )
    print( '#include atoms', file=a)
    print( '', file=a )
    print( '#DEFVAR', file=a)
    print( '', file=a )
    # Now print active species
    ptr_str = '{:<11}= IGNORE; '
    for spec in species_df[ species_df['inactive'] == False].index:
        df_tmp = species_df[species_df.index == spec]
#        print( spec)
        dsp_str = df_tmp['Description'].values[0]
        if ('{' not in dsp_str):
            dsp_str = '{'+dsp_str+'}'
#        print( ptr_str.format(spec)+dsp_str)
        print( ptr_str.format(spec)+dsp_str, file=a )
#        print( df_tmp['Description'].values[0] )
    # Now print inactive species
    print( '', file=a )
    print( '#DEFFIX', file=a)
    print( '', file=a )
    for spec in species_df[species_df['inactive'] == True].index:
        df_tmp = species_df[species_df.index == spec]
        dsp_str = df_tmp['Description'].values[0]
        if ('{' not in dsp_str):
            dsp_str = '{'+dsp_str+'}'
        print( ptr_str.format(spec)+dsp_str, file=a )
    # ----  Print equations to file
    print( '', file=a )
    print( '#EQUATIONS', file=a)
#    rxn_types = sorted(rxn_dicts.keys())
    rxn_types = ['Gas-phase', 'Heterogeneous', 'Photolysis']
    for rxn_type in rxn_types:
        # Setup print strings
        KPP_line_max = 43
        if (rxn_type == 'Photolysis'):
            func_max_len = 15
            ptr_str = '{:<44} {:<15} {}'
        else: # Heterogeneous and Gas-phase
            func_max_len = 36.
            ptr_str = '{:<44} {:<36} {}'
        # print out headers for mech
        print('//', file=a )
        print('// {}'.format(rxn_type) +' reactions', file=a )
        print('//', file=a )
        # now loop by reaction
        rxn_dict = rxn_dicts[rxn_type]
        for ind in rxn_dict.index:
            print
            df_tmp = rxn_dict[ rxn_dict.index == ind ]
            rxn = df_tmp['rxn_str'].values[0]
            eqn = df_tmp['eqn'].values[0]
            metadata = df_tmp['metadata'].values[0].strip()
            # Check if rxn is longer than KPP rxn strin max...
            if (len( rxn ) < KPP_line_max):
                ptr_vars = rxn+' :', eqn+';', metadata
                print( ptr_str.format( *ptr_vars), file=a )
            else:
                print(rxn, KPP_line_max)
                # Just split substrings ? (NO, must split by reactant)
#                 frac_of_max = len( rxn ) / KPP_line_max
#                 nchunks = AC.myround( frac_of_max, base=1, round_up=True )
#                 sub_strs = AC.chunks(l=rxn, n=int(KPP_line_max)-2 )
                sub_strs = split_KPP_rxn_str_into_chunks( rxn )
                # loop sub strings
                for n, sub_str in enumerate( sub_strs ):
                    # If not the final sub string, then just print sub string
                    if (n+1 != len(sub_strs) ):
                        print( sub_str, file=a )
                    # Now print substring
                    else:
                        ptr_vars = sub_str+' :', eqn+';', metadata
                        print( ptr_str.format( *ptr_vars ), file=a )
    # ---  Now close the file...
    a.close()


# -------------- Extract rxn data from KPP ***output*** files
# ----
# X.XX - Read the headers (top part) of the KPP mechanism file
# ----
def KPP_eqn_file_headers( folder=None, filename=None ):
    """ Get headers from KPP *.eqn file """
    # ----open file and loop by line
    header_lines = []
    with open( folder+filename, 'rb') as file_:
        for line in file_:
            header_lines += [ line ]
            if (line.strip() == '}'):
                break
    return header_lines


# ----
# X.XX -
# ----
def get_reactants_and_products4tagged_fam( fam='LOx', KPP_output_mech=None, \
        folder=None ):
    """ Return a list of reactants and products of reactions making fam tag """
    import pandas as pd
    # Get the outputted KPP mechanism if not provided.
    if isinstance(KPP_output_mech, type(None)):
        KPP_output_mech = get_dict_of_KPP_mech( wd=folder )
    # Make a DataFrame from the dictionary
    df = pd.DataFrame( KPP_output_mech.values(), index=KPP_output_mech.keys() )
    df.columns = ['rxn str']
#    df.index = df.index - 1 # Adjust Fortran numbering in output to Pythonic #
    # Split apart reaction str to give products and reactants
    def extract_products(input):
        return input.split(' --> ')[-1].strip()
    def extract_reactants(input):
        return input.split(' --> ')[0].strip()
    df['prod'] = df['rxn str'].map(extract_products)
    df['react'] = df['rxn str'].map(extract_reactants)
    # Make the formating the same as in input files
    # ---- Check if the file mapping can work between KPP input & output
    df['KPP input react'] = df['react'].map(update_KPP_rxn_str)
#    KPP_Input_df['KPP input react'] = KPP_Input_df['react'].map(update_rxn_str)
    find_breakpoint=False
    if find_breakpoint:  # Seems to be C3H8 + OH = A3O2 :
#        for s,e in [ [0, 50], [] ]:
        for s,e in  zip(range(0, 700, 50 ) ,range(50, 750, 50 ) ):
            bool = df['react'][s:e] == KPP_Input_df['KPP input react'][s:e]
            a_ = df['react'][s:e][~bool]
            b_ = KPP_Input_df['KPP input react'][s:e][~bool]
#            print dict( zip( a_, b_ )  )
            # turn into sorted lists
            a_ = [list(sorted([ii.strip()for ii in i.split('+')])) for i in a_ ]
            b_ = [list(sorted([ii.strip()for ii in i.split('+')])) for i in b_ ]
            # compare these and only print if they differ
            for n, a__ in enumerate( a_ ):
                if a__ != b_[n]:
                    print( a__, b_[n])
    # Only consider reaction that include family in the products
    def fam_in_rxn(input):
        return (fam in input)
    rtn_vars= [ 'react', 'prod', 'KPP input react']
    df = df[ df['prod'].map(fam_in_rxn) ][ rtn_vars ]
    return  df


# ----
# X.XX - Get reaction numbers
# ----
def get_KPP_tagged_rxns( fam='LOx', filename='gckpp_Monitor.F90',
        Mechanism='Halogens', RR_dict=None, wd=None ):
    """
    Search compiled KPP mechanism for reactions with a certain tag ("fam") in
    their mechanism (e.g. LOx for loss of Ox)

    Parameters
    -------
    fam (str): prod/loss family in KPP file (e.g. Ox loss or "LOx" )
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (list)
    """
    # Get dictionary of reactions in Mechanism
    if isinstance( RR_dict, type(None)):
        RR_dict = get_dict_of_KPP_mech(Mechanism=Mechanism, filename=filename,\
            wd=wd)
    # loop dictionary of reactions and save those that contain tag
    tagged_RR_dummies = []
    for key_ in list(RR_dict.keys()):
        # Get reaction string
        rxn_str = RR_dict[key_]
        # collection reactions with tag
        if fam in rxn_str:
            tagged_RR_dummies += [key_]
    return tagged_RR_dummies


# -------------- Extract rxn data from KPP ***input*** file(s)
# ----
# X.XX - get species in KPP *.eqn file
# ----
def KPP_eqn_file_species( folder=None, filename=None, debug=False ):
    """ Get specoes from *.eqn file """
    import pandas as pd
    import numpy as np
    # ----open file and loop by line
    with open( folder+filename, 'rb') as file_:
        specs = []
        num2read_line_from = 999999
        species_is_not_active = False
        inactive = []
        for n_line, line_ in enumerate( file_ ):
            # Are we at the species section?
            if ('#DEFVAR' in line_):
                num2read_line_from = n_line+2
            # Now save the species detail
            if (n_line >= num2read_line_from) and (len(line_)>1):
                specs += [ line_ ]
            # also include inactive species? - Yes
            # (but track that these are inactive)
            if ("#DEFFIX" in line_):
                species_is_not_active = True
            if ('IGNORE' in line_):
                inactive += [species_is_not_active]
            # Stop when got to lines of equations
            if ("#EQUATIONS" in line_):
                break
            if debug: print( num2read_line_from )
    # Process extracted lines to dict of names and descriptions...
    def strip_line(line_):
        try:
            name, descrip = line_.strip().split('= IGNORE;')
            line_ = [name.strip(),descrip.strip()]
        except:
            print( 'ERROR for: {}'.format(line_) )
        return line_
    specs = [ strip_line(i) for i in specs if (len(i) > 12)  ]
    # return as a DataFrame
    maxlen =  400
    df = pd.DataFrame( [i[1] for i in specs], dtype=(np.str, maxlen) )
    df.index = [i[0] for i in specs]
    df.columns = ['Description']
    # add activity to DataFrame
    df['inactive'] = inactive
    return df


# ----
# X.XX - Get a dictionary of KPP equations from *.eqn file
# ----
def get_dicts_of_KPP_eqn_file_reactions( folder=None, filename=None,
        debug=False):
    """ Get reactions from *.eqn file
    (Heterogeneous, Photolysis, Gas-phase)
    """
    import string
    # Local vars
    rxt_funcs = 'HET', 'PHOTOL', 'GCARR' , '  GC'
    # loop lines in file
    with open( folder+filename, 'rb') as file_:
        rxns_dict = {}
        for rxns in ( 'Gas-phase', 'Heterogeneous', 'Photolysis',):
#        for rxns in ('Gas-phase',):
            num2read_line_from = 999999
            eqns =[]
            # tmp variables to catch KPP reactions over more than one line
            tmp_line_ =''
            partial_rxn_str =False
            # Now loop
            for n_line, line_ in enumerate( file_ ):
                # Are we at the species section?
                if ('//' in line_) and (rxns in line_):
                    num2read_line_from = n_line+2
                # Now save the species detail
                if (n_line >= num2read_line_from) and (len(line_)>1):
                    # is there a rxn function in  the line?
                    if not any( [ (i in line_) for i in rxt_funcs] ):
                        # if not then str/line only contains a partial strin
                        partial_rxn_str = True
                        rxn_func_in_str = False
                    else:
                        rxn_func_in_str=True
                    # if only part of rxn str, then save and add to next line
                    if partial_rxn_str:
                        tmp_line_ += line_.strip()
                        if debug: print('added to tmp_line_:', tmp_line_, line_)
                    # if the tmp str is empty, just fill it with the line_
                    if (tmp_line_== ''):
                        tmp_line_ = line_.strip()
                    # (extra) check: is there is rxn func in the tmp_line_ str?
                    if  any( [ (i in tmp_line_) for i in rxt_funcs ] ):
                        rxn_func_in_str=True
                    if rxn_func_in_str:
                        eqns += [ tmp_line_ ]
                        # reset the tmp str
                        tmp_line_ =''
                        partial_rxn_str =False
                # Stop reading lines at end of section
                if ("//" in line_) and len(eqns)>3:
                    break
                print( n_line, line_ )
            # remove spacing errors in KPP eqn entries
            def remove_KPP_spacing_errors(input):
                """ remove differences in spacing ion KPP """
                # Numbers
                for num in [str(i) for i in range(0,10 )]:
                    input = input.replace(' +'+num, ' + '+num)
                # Lower case letters
                for let in string.ascii_lowercase:
                    input = input.replace(' +'+let, ' + '+let)
                # Upper case letters
                for let in string.ascii_uppercase:
                    input = input.replace(' +'+let, ' + '+let)
                return input
            # remove KPP spacing errors
            eqns = [ remove_KPP_spacing_errors(i) for i in eqns ]
            # Check for "eqns" with more than one eqn in
            eqns = split_combined_KPP_eqns( eqns )
            # Save out
            rxns_dict[rxns] = eqns
    return rxns_dict


# -------------- Misc. helper functions for KPP file processing/analysis
# ----
# X.XX -
# ----
def split_KPP_rxn_str_into_chunks( rxn, KPP_line_max=43, debug=False ):
    """ Split a rxn str so that it is not longer than KPP max line length """
    print( rxn )
    # subfunction to cut strings to last " +"
    def return_string_in_parts_ending_with_plus( input ):
        """ return string upto last ' +'  in string """
        # find the last ' + ' in string
        ind = input[::-1].find(' +')
        return input[:-(ind)-1 ]
    # now loop the sub_Strs
    rxn_len = len(rxn)
    remainder = rxn_len
    sub_str_lens = [0]
    sub_strs = []
    # loops to do ()
    times2loop =  rxn_len / float(KPP_line_max)
    times2loop = myround(times2loop, round_up=True, base=1) +1
    for n in range( times2loop ):
        if debug: print( n, remainder, sub_str_lens )
        if (remainder > 0):  #and len(sub_str):
#        while (remainder > 0):
            # cut reaction string from length taken
            new_str = rxn[sum(sub_str_lens):][:int(KPP_line_max)]
            if debug: print( new_str )
            # if the new string is the end of the rxn string
            if len(new_str) < int(KPP_line_max):
                sub_strs += [ new_str ]
                sub_str_lens += [ len(new_str) ]
                remainder= 0
                break
            # If not chop str to las "+"
            else:
                new_str = return_string_in_parts_ending_with_plus( new_str )
                # now save to sub str list
                sub_strs += [ new_str ]
                sub_str_lens += [ len(new_str) ]
                remainder = rxn_len - sum(sub_str_lens)
            if debug: print( new_str )
        else:
            break
    print( sub_strs )
    return sub_strs


# ----
# X.XX -
# ----
def get_KPP_PL_tag( last_tag, tag_prefix='T' ):
    """ Get the next P/L tag in a format T??? """
    assert (len(last_tag) == 4), "Tag must be 4 characers long! (e.g. T???)"
    last_tag_num =  int( last_tag[1:])
    return '{}{:0>3}'.format( tag_prefix, last_tag_num+1 )


# ----
# X.XX -
# ----
def print_out_lines_for_gckpp_file( tags=None, extr_str='' ):
    """ Print lines to gckpp.kpp for added for tags in now in the .eqn file """
    # Create a *.kpp file for lines to be saved to
    a=open('gckpp.kpp_extra_lines_for_tagged_mech_{}'.format(extr_str),'w')
    print( '#FAMILIES', file=a )
    for tag in tags:
        print( '{} : {};'.format( 'P'+tag, tag ), file=a )
    # Now close the file...
    a.close()


# ----
# X.XX -
# ----
def update_KPP_rxn_str(input, rtn_as_list=False):
    """ Update reaction string in KPP reaction string """
    # Remove +hv from phtolysis reactions
    input = input.replace('+hv', '')
    input = input.replace('+ hv', '')
    # Remove {M} from 3 body reactions
    input = input.replace('{+M}', '')
    # Remove any trailing/leading  white space
    input = input.strip()
    # If a self reaction, then  write  Y
    if '+' in input:
        tmp_ = input.split('+')
        if len(tmp_) == 2:
            if tmp_[0].strip() == tmp_[1].strip():
                input = '{} {}'.format(len(tmp_), tmp_[0] )
            elif rtn_as_list:
                input = sorted( tmp_ )
        else:
            print( 'ERROR!', tmp_, input)
    return input.strip()


# ----
# X.XX -
# ----
def process_KPP_rxn_dicts2DataFrames(rxn_dicts=None, debug=False,
        Use_FORTRAN_KPP_numbering=True ):
    """ Process lists of strings of KPP mech into organised DataFrame """
    import pandas as pd
    # Loop dictionary of reaction mechanisms
    for key_ in rxn_dicts.keys():
        rxn_list = rxn_dicts[key_]
        rxn_list_processed =[]
        # Loop reactions and extract and clean meta data
        for rxn in rxn_list:
            rxn_str = rxn.split(':')[0].strip()
            eqn = rxn.split(':')[1].split(';')[0].strip()
            metadata = rxn[rxn.find(';')+1:]
#            if len(metadata) > 0:
#                print( metadata )
#                metadata_start = metadata.find('{')
#                metadata_end = metadata[::-1.find('}')
#                metadata = metadata[metadata_start:metadata_end+1]
            # split off reactants and products...
            react = rxn_str.split('=')[0].strip()
            prod= rxn_str.split('=')[-1].strip()
            rxn_list_processed += [ [rxn_str, react, prod, eqn, metadata ]]
        # Create a dataframe
        df = pd.DataFrame(rxn_list_processed)
        df.columns = ['rxn_str', 'react', 'prod', 'eqn', 'metadata' ]
        # Force use of index numbers from FORTRAN / KPP
        if Use_FORTRAN_KPP_numbering:
            df.index =  df.index +1
            print( 'WARNING - updated DataFrame dictionary to start @1 (not 0)')
        # Overwrite dictionary with dataframe
        rxn_dicts[key_] = df
    return rxn_dicts


# ----
# X.XX -
# ----
def split_combined_KPP_eqns( list_in ):
    """ split combined KPP eqn strings  """
    # Indices of KPP eqn strings with more than one "="
    inds = []
    for n,str in  enumerate( list_in ):
        if str.count('=') > 1:
            inds += [ n ]
    strs = [ list_in[i] for i in inds ]
    print('WARNING: found {} combined strings:'.format( len(inds) ), strs)
    # If there are any combined eqn strings, then split them
    if len(inds) > 0:
        new_eqns  = []
        for ind in inds:
            tmp_str = list_in[ ind ]
            print( tmp_str, inds )
            ind_1st_equals = tmp_str.find( '=' )
            ind_2nd_equals = tmp_str[::-1].find( '=' )
            tmp_str_short = tmp_str[ind_1st_equals:len(tmp_str)-ind_2nd_equals ]
            try:
                last_bracket_of_1st_eqn =  tmp_str_short[::-1].find( '}' )
                # Calculate the split point for the reactions
                ind_2nd_eqn = ind_1st_equals+len(tmp_str_short)
                ind_2nd_eqn = ind_2nd_eqn - last_bracket_of_1st_eqn
                #
                new_eqns += [ [  tmp_str[:ind_2nd_eqn], tmp_str[ind_2nd_eqn:] ]]
            except:
                print('Issue with inputted file (meta data... )' )
                sys.ext()
        # Drop old ones
        [ list_in.pop(i) for i in sorted(inds)[::-1] ]
        # Add news ones and return
#        if len(inds) == 1:
        for n, ind in enumerate( inds ):
            list_in = list_in[:ind] + new_eqns[n] + list_in[ind:]
            print(list_in[:ind][-5:])
            print(list_in[ind+1:][:5])
    return list_in


# --------------
# -------------- Funcs specifically for v11-1g and later ends here
# (funcs still do use funcs from elsewhere)


# ----
# X.XX - Get stoichiometry of each tagged reaction in KPP file
# ----
def get_stioch_for_family_reactions( fam='LOx', filename='gckpp_Monitor.F90',
        Mechanism='Halogens', RR_dict=None, wd=None, debug=False ):
    """
    Get the stiochmetery for each reaction in family from compiled KPP file

    Parameters
    -------
    fam (str): prod/loss family in KPP file (e.g. Ox loss or "LOx" )
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (dict)
    """
    # Get dictionary of reactions in Mechanism
    if isinstance( RR_dict, type(None)):
        RR_dict = get_dict_of_KPP_mech(Mechanism=Mechanism, filename=filename, \
            wd=wd)
    # Assume unity if no coeffeicent
    unity = 1.0
    # Loop dictionary of reactions and save those that contain tag
    tagged_rxns = []
    tagged_rxn_stioch = []
    for key_ in list(RR_dict.keys()):
        # Get reaction string
        rxn_str = RR_dict[key_]
        # collection reactions with tag
        if fam in rxn_str:
            tagged_rxns += [key_]
            # split reaction str by '+' (excluding reactants part)
            rxn_str = rxn_str[18:].split('+')
            if debug: print( rxn_str )
            # get product
            product_str = [i for i in rxn_str if (fam in i) ]
            if debug: print( product_str )
            # Find index of reaction
#            ind_of_rxn = [ n for n,i in product_str if (fam in i) ]
            # split coefficient ("Coe") from reaction
            product_str = product_str[0].strip().split()
            if len(product_str)>1:
                tagged_rxn_stioch += [ float(product_str[0]) ]
            else:
                tagged_rxn_stioch += [ unity ]
    return dict(list(zip(tagged_rxns, tagged_rxn_stioch)))


def get_tags4_family( fam='LOx', filename='gckpp_Monitor.F90',
        Mechanism='Halogens', tag_prefix='PT', RR_dict=None, wd=None,
        get_one_tag_per_fam=True, debug=False ):
    """
    For a P/L family tag (e.g. LOx), if there are induvidual tags then these
    are extracted

    Parameters
    -------
    fam (str): prod/loss family in KPP file (e.g. Ox loss or "LOx" )
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (dict)
    """
    # Get dictionary of reactions in Mechanism
    if isinstance(RR_dict, type(None)):
        RR_dict = get_dict_of_KPP_mech(Mechanism=Mechanism, filename=filename,\
            wd=wd)
    # loop dictionary of reactions and save those that contain tag
    tagged_rxns = []
    tagged_rxn_tags = []
    for key_ in list(RR_dict.keys()):
        # Get reaction string
        rxn_str = RR_dict[key_]
        # collection reactions with tag
        if fam in rxn_str:
#            if debug: print( key_, fam, rxn_str )
            tagged_rxns += [key_]
            # split reaction str by '+' (excluding reactants part)
            rxn_str = rxn_str[18:].split('+')
            # look for tag(s)... - should only be one per reaction!
            tags = [i.strip() for i in rxn_str if (tag_prefix in i) ]
            if debug: print( rxn_str, tags )
            if len(tags)>=1:
                if len(tags) ==1 :
                    tagged_rxn_tags += tags
                else:
                    prt_str = 'WARNING: {} tags for rxn! - {} - {}'
                    if debug: print( prt_str.format( len(tags), tags, rxn_str ))
                    if get_one_tag_per_fam :
                        tagged_rxn_tags += [ tags[0] ]
                    else:
                        tagged_rxn_tags += tags
            else:
                tagged_rxn_tags+=['WARNING: RXN. NOT TAGGED! ({})'.format(key_)]
                if debug: print(( key_, fam, 'ERROR!', tags, rxn_str ))
    assert len(tagged_rxns)==len(tagged_rxn_tags), "# tags doesn't = # rxns!"
    return dict(list(zip(tagged_rxns, tagged_rxn_tags)))


# ----
# X.XX - Get dict of KPP Mech.
# ----
def get_dict_of_KPP_mech(filename='gckpp_Monitor.F90',
        Mechanism='Halogens', GC_version='v11-01', wd=None):
    """
    Get a dictionary of KPP mechansim from compile mechanism

    Parameters
    -------
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file
    GC_version (str): name of GEOS-Chem version

    Returns
    -------
    (dict)
    """
    log_str = 'get_dict_of_KPP_mech called for Mech:{} (ver={}, wd={})'
    logging.info( log_str.format( Mechanism, GC_version, wd) )
    # Get base working code directory
    if isinstance( wd, type(None)):
#        wd = sys.agrv[1]
        # Hardwire for testing
#         wd = '/work/home/ts551/data/all_model_simulations/iodine_runs/'
#         wd += 'iGEOSChem_5.0/code_TMS_new/'
#         wd += '/KPP/{}/'.format(Mechanism)
        print('wd with code must be provided')
    MECH_start_str = 'INTEGER, DIMENSION(1) :: MONITOR'
#    rxn_line_ind = '! index'
    strs_in_non_rxn_lines = 'N_NAMES_', 'CHARACTER', 'DIMENSION', 'PARAMETER'
    RR_dict = {}
    with open( wd+filename, 'r') as file:
        # loop by line in file
        start_extracting_mech_line=1E99
        for n, line in enumerate( file ):
            # check for mechanism identifier
            if (MECH_start_str in line):
                start_extracting_mech_line = n+3
            # Extract reaction mechanism info
            if n >=start_extracting_mech_line:
                # break out of loop after empyty line (len<3)
                if len(line) < 3:
                    break
                # check if the line contains a reaction str
#                if (rxn_line_ind in line) or start_extracting_mech_line:
                # check if line contrains strings not in reaction lines
                if not any([(i in line) for i in strs_in_non_rxn_lines]):
                    rxn_str = line[6:106]
                    # RR??? dummy tags only available on v11-01 patches!
                    if GC_version == 'v11-01':
                        RR_dummy = 'RR{}'.format( line[118:].strip() )
                        # add to dictionary
                        RR_dict[RR_dummy] = rxn_str
                    # Use just reaction number for other versions...
                    else:
                        try:
                            RR_num = int( line[118:].strip() )
                            # add to dictionary
                            RR_dict[RR_num] = rxn_str
                        except ValueError:
                            # add gotcha for lines printed without an index in
                            # KPP
                            # e.g. final line is missing index in KPP output.
                            # CHARACTER(LEN=???), PARAMETER, DIMENSION(??) ::
                            #  EQN_NAMES_?? = (/ &
                            #  ' ... ', & ! index ???
                            #  ' ... ' /)
                            # (no index given for the final output. so assume
                            # n+1)
                            logging.debug('rxn # assumed as {} for {}'.format(\
                                RR_num+1, rxn_str ) )
                            # use the value of the line previous and add to
                            # dictionary
                            RR_dict[RR_num+1] = rxn_str
    return RR_dict


# ----
# X.XX - Print Prod-loss reactions for tagged/passed reactions
# ----
def prt_families4rxns_to_input_to_PROD_LOSS(fam='LOx', rxns=None, wd=None, \
        filename='gckpp_Monitor.F90', Mechanism='Halogens' ):
    """
    Takes a list of reaction numbers or (fam) and prints out prod/loss in
    a form that can be copy/pasted into KPP (gckpp.kpp)

    Parameters
    -------
    rnxs (list): lisst of reactions to use for
    fam (str): prod/loss family in KPP file (e.g. Ox loss or "LOx" )
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (None)
    """
    # get list of tagged reactions for family
    if isinstance(rxns, type(None)):
        rxns = get_KPP_tagged_rxns( fam=fam, filename=filename, \
            Mechanism=Mechanism, wd=wd)
    # --- Print to screen
    header_Str = '#FAMILIES'
    pstr = 'P{} : {};'
    print('>>>> Copy and paste the below text into gckpp.kpp <<<')
    print(header_Str)
    for rxn in rxns:
        print((pstr.format(rxn, rxn )))


# ----
# X.XX - Print Prod-loss reactions for tagged/passed reactions
# ----
def prt_families4rxns_to_input_to_PROD_LOSS_globchem_spec(fam='LOx', \
        rxns=None, wd=None, filename='gckpp_Monitor.F90', \
        Mechanism='Halogens' ):
    """
    Takes a list of reaction numbers or (fam) and prints out prod/loss in
    a form that can be copy/pasted into KPP (globchem.spc)

    Parameters
    -------
    rnxs (list): lisst of reactions to use for
    fam (str): prod/loss family in KPP file (e.g. Ox loss or "LOx" )
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (None)

    Notes
    -------
     - From v11-2d the KPP mechanism is in a single *.eqn file (globchem.spc was
        retired).
    """
    # get list of tagged reactions for family
    if isinstance(rxns, type(None)):
        rxns = get_KPP_tagged_rxns( fam=fam, filename=filename, \
            Mechanism=Mechanism, wd=wd)
    # --- Print to screen
    header_Str = '#DEFVAR'
    pstr = '     {:<10}      =          IGNORE;'
    print('>>>> Copy and paste the below text into globchem.spc <<<')
    print(header_Str)
    for rxn in rxns:
        print((pstr.format(rxn, rxn )))


# ----
# X.XX - Get dictionary of all reactions strings for tagged reactions
# ----
def get_dictionary_of_tagged_reactions(filename='globchem.eqn',
        Mechanism='Halogens', wd=None):
    """
    Construct a dictionary of reaction strings for tagged reactions in
    globchem.eqn

    Notes
    -------
     - From v11-2d the KPP mechanism is in a single *.eqn file (globchem.eqn was
        retired and replaced with <mechanism name>.eqn).
    """
    # Get base working code directory
    if isinstance( wd, type(None)):
#        wd = sys.agrv[1]
        # Hardwire for testing
        wd = '/work/home/ts551/data/all_model_simulations/iodine_runs/iGEOSChem_5.0/code_TMS_new/'
        wd += '/KPP/{}/'.format(Mechanism)
    # Local variable
    tracer_names_like_tag = ['TRO2']
    # Initialise lists to store tags
    tags_l = []
    rxn_l = []
    # Now open file and look for tags
    with open(wd+filename) as file_:
        # loop lines and store reaction strs (1st line) that contain tags
        for line in file_:
            try:
                # What does the reaction string begin?
                start_str_index = line.index('}')+2
                # Select reaction string and just products.
                reaction_str = line[start_str_index:51]
                product_str = reaction_str.split(' =')[-1]
                # Assume Tag is 1st and in form TG??? (where ??? are numerical )
                # update this to use regular expressions?
                part_of_str_that_would_contain_tag = product_str[:6]
                if ' T' in part_of_str_that_would_contain_tag:
                    # strip tag from string.
                    tag = part_of_str_that_would_contain_tag.strip()
                    # Add if actually a tag.
                    if tag not in tracer_names_like_tag:
                        tags_l += [ tag ]
                        # select tag
                        rxn_l += [ reaction_str.strip() ]
            # If the line doesn't contain a reaction # ("{?}"), then pass
            except ValueError:
                pass
    return dict( list(zip(tags_l, rxn_l)) )


# ----
# X.XX - Assign family for tag based on reaction string
# ----
def get_Ox_family_tag_based_on_reactants(filename='gckpp_Monitor.F90', \
        Mechanism='Halogens', wd=None,  fam='LOx', tag_prefix='PT', \
        tags=None, RR_hv_dict=None, RR_dict=None, GC_version='v11-01',
        debug=False  ):
    """
    Get Ox famiy of reaction tag using KPP reaction string.

    Parameters
    -------
    rxns (list): lisst of reactions to use for
    fam (str): prod/loss family in KPP file (e.g. Ox loss or "LOx" )
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (None)
    """
    # --- Local variables
    # Get dictionary of reactions in Mechanism
    if isinstance(RR_dict, type(None)):
        RR_dict = get_dict_of_KPP_mech(Mechanism=Mechanism, \
            filename=filename, wd=wd)
#    if isinstance(RR_hv_dict, type(None)):
#        RR_hv_dict = get_dictionary_of_tagged_reactions(filename='globchem.eqn',
#            Mechanism=Mechanism, wd=wd)
    # Get tags for reaction unless already provided
    if isinstance(tags, type(None)):
        tags = get_tags4_family( wd=wd, fam=fam, filename=filename, \
            Mechanism=Mechanism, tag_prefix=tag_prefix, RR_dict=RR_dict )
    # --- Extra local variables
    HOx = [ 'OH', 'HO2', 'H2O2']
    # temporarily add to definition of HOx
    HOx+=['O1D', 'O','O3','NO3']
    ClOx =['CFC', 'Cl', 'ClO' ]
    NOx = [ 'NO', 'NO2', 'NO3', 'N2O5']
    non_I_specs_with_I_char = [ \
    'INO2', 'ISN1', 'ISNOOA', 'ISNOHOO', 'ISOPNB', 'ISOPND', 'ISOP', 'ISNP',
    # add species in v11-2d
    'IONITA',
    # add species in v11-2d (benchmarks)
    'IMAO3', 'IPMN', 'MONITS', 'MONITU', 'ISNP', 'LIMO', 'ISNOOB', 'PIO2',
    'LIMO2'
    ]
    # Get list of tagged hv reactions
#    all_rxns = sorted(RR_hv_dict.keys())
#    hv_rxns_tags = [ i for i in all_rxns if ( 'hv' in RR_hv_dict[i])]
    all_rxns = sorted(RR_dict.keys())
    hv_rxns_tags = [ i for i in all_rxns if ( 'hv' in RR_dict[i])]
    # Loop tagged reactions and assign family
    tagged_rxns = sorted(tags.keys())
    fam_l = []
    for n_rxn, rxn_ in enumerate( tagged_rxns ):
        _debug=False
        # Initialise booleans
        Br_is_reactant = False
        Cl_is_reactant = False
        I_is_reactant = False
        NOx_is_reactant = False
        HOx_is_reactant = False
        hv_is_reactant = False
        IONITA_is_formed =False
        # --- Get reaction string  and check within
        rxn_str = RR_dict[rxn_]
        reactant_str = rxn_str.split('-->')[0]
        product_str = rxn_str.split('-->')[1]
        # - Check if species are in reactions
        # BrOx reaction?
        if 'Br' in reactant_str:
            Br_is_reactant=True
        # IOx reaction?
        if 'I' in reactant_str :
            # account for non-iodine species with I Character in...
            if not any([(i in reactant_str) for i in non_I_specs_with_I_char]):
                I_is_reactant=True
        # ClOx reaction?
        if any([(i in reactant_str) for i in ClOx]):
            Cl_is_reactant=True
        # Gotcha for heterogenous N2O5 breakdown by Cl-
#        if (tags[rxn_] == 'T172') and (ver='v11-01')::
#        if (tags[rxn_] == 'T164') and (GC_version=='v11-01'):
#            Cl_is_reactant=True
        if ('N2O5' in reactant_str) and ('ClNO2' in reactant_str):
            Cl_is_reactant=True
        # NOx reaction?
        if any([(i in reactant_str) for i in NOx]):
            NOx_is_reactant=True
#        print (tags[rxn_][1:] in hv_rxns_tags), tags[rxn_][1:], hv_rxns_tags
#        print RR_dict[rxn_]
        # hv reaction?
        if (tags[rxn_][1:] in hv_rxns_tags):
            hv_is_reactant=True
        # HOx reaction?
        if any([(i in reactant_str) for i in HOx]):
            HOx_is_reactant=True
        # gotcha for IONITA in v11-01
#         if (GC_version=='v11-01'):
#             IONITA_rxns = ['T040', 'T039', 'T037']
#             if any( [(tags[rxn_] == i) for i in IONITA_rxns] ):
#                 IONITA_is_formed = True
        # IONITA in  reaction?
        # (IONITA = Aer-phase organic nitrate from isoprene precursors)
        if ('IONITA' in product_str):
            IONITA_is_formed = True
        # --- Assign familes
        # 1st check if halogen crossover reaction...
        if Cl_is_reactant and Br_is_reactant:
            fam_l += ['ClOx-BrOx']
        elif Cl_is_reactant and I_is_reactant:
            fam_l += ['ClOx-IOx']
        elif Br_is_reactant and I_is_reactant:
            fam_l += ['BrOx-IOx']
        # Now just check if single halogen family...
        elif Cl_is_reactant:
            fam_l += ['ClOx']
        elif Br_is_reactant:
            fam_l += ['BrOx']
        elif I_is_reactant:
            fam_l += ['IOx']
        # Now check if photolysis reaction...
        elif hv_is_reactant:
            fam_l += ['hv']
        # HOx?
        elif NOx_is_reactant:
            fam_l += ['NOx']
        # HOx?
        elif HOx_is_reactant:
            fam_l += ['HOx']
        # if IONITA reaction
        elif IONITA_is_formed:
            fam_l += ['NOx']
        # Not assigned?!
        else:
            fam_l += ['NOT ASSIGNED!!!']
            _debug=True
        # Special cases?
        # O1D + H2O --> 2 OH
        if ('O1D' in reactant_str) and ('H2O' in reactant_str):
            fam_l[n_rxn] = 'hv'
        # debug print ?
        if _debug:
            specs = 'Br', 'I', 'Cl', 'NOx', 'hv', 'HOx'
            booleans = Br_is_reactant, I_is_reactant, Cl_is_reactant,  \
                NOx_is_reactant, hv_is_reactant, HOx_is_reactant
            print((list(zip(specs, booleans))))
        if debug: print((rxn_str, fam_l[n_rxn]))
    # Nicer family names?
#    if mk_family_names_readable:
    name_dict = {
    'ClOx-BrOx': 'Cl+Br', 'BrOx-IOx': 'Br+I', 'BrOx': 'Bromine',
    'ClOx-IOx': 'Cl+I', 'IOx': 'Iodine', 'ClOx': 'Chlorine', 'HOx': 'HO$_{\\rm x}$',
    'hv':'Photolysis', 'NOx': 'NO$_{\\rm x}$',
    # Allow unassigned reactions to pass (to be caught later)
    'NOT ASSIGNED!!!':'NOT ASSIGNED!!!'
    }
    fam_l = [ name_dict[i] for i in fam_l ]
    tag_l = [ tags[i] for i in tagged_rxns ]
    return dict(list(zip(tag_l, fam_l )))


# ----
# X.XX - Assign family for tag based on reaction string
# ----
def get_tags_in_rxn_numbers( rxn_nums=[], RR_dict=None, \
        filename='gckpp_Monitor.F90', Mechanism='Halogens', wd=None, \
        debug=False):
    """
    Get tags in given list of reactions ()

    Parameters
    -------
    rxns (list): lisst of reactions to use for
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (None)
    """
    # Get dictionary of reactions in Mechanism
    if isinstance( RR_dict, type(None)):
        RR_dict = get_dict_of_KPP_mech(Mechanism=Mechanism, filename=filename, \
            wd=wd)
    # Loop dictionary of reactions and save those that contain tag
    tagged_rxns = []
    tags_for_rxns = []
    # create a sub dictionary for reaction numbers provided
    sub_dict = dict( [ (i, RR_dict[i]) for i in rxn_nums ] )
    print(sub_dict)
    for key_ in list(sub_dict.keys()):
        # Get reaction string
        rxn_str = RR_dict[key_]
        # collection reactions with tag
        tag_strs = [' + T', '> T' ]
        # replace this with reg ex?
        if debug:
            print((key_, rxn_str, any([i in rxn_str for i in tag_strs])))
        if any([i in rxn_str for i in tag_strs]):
            # split reaction str by '+' (excluding reactants part)
            product_str_list = rxn_str[18:].split('+')
            # select tag(s)
            tag_ = [ i for i in product_str_list if (' T' in i) ]
            if len(tag_) > 1:
                print(('WARNING - more than one tag for reaction? :', tag_))
                sys.exit()
            else:
                tags_for_rxns += [ tag_[0].strip() ]
                tagged_rxns += [ key_ ]
    return dict( list(zip(tagged_rxns, tags_for_rxns)) )


# ----
# X.XX - Get reaction numbers that oxidative release halogens
# ----
def get_oxidative_release4specs(filename='gckpp_Monitor.F90',
        Mechanism='Halogens', wd=None):
    """
    Certain species have a fixed concentration in the model, for these speices
    the source value is calculated by the summ of the oxidative release
    ( OH, Br, Cl )

    Parameters
    -------
    wd (str): the working (code) directory to search for files in
    Mechanism (str): name of mechanism (e.g. dir in KPP folder)
    filename (str): name of KPP monitor file

    Returns
    -------
    (list)
    """
    # Species ?
    specs = ['CHBr3', 'CH3Cl', 'CH2Cl2', 'CHCl3' ]
    # Get dictionary of reactions in Mechanism
    RR_dict = get_dict_of_KPP_mech(Mechanism=Mechanism, filename=filename, \
        wd=wd)
    # Loop species
    RR_rxn_dummies = []
    for spec in specs:
        # loop reactions
        for key_ in RR_dict:
            rxn_str = RR_dict[key_]
            # species in reaction?
            if spec in rxn_str:
                print(rxn_str)
                RR_rxn_dummies +=[ key_ ]
    return RR_rxn_dummies


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# -------------- Delete/move to user specific modules


# ----
# X.XX - Get tropospheric Burden -
# ----
def get_trop_burden( ctm=None, spec='O3', wd=None, a_m=None, t_p=None, \
        Iodine=False, all_data=True, total_atmos=False , res='4x5',  \
        trop_limit=True, arr=None, debug=False ):
    """
    Get Trosposheric burden for species ("spec")

    Parameters
    ----------
    a_m (np.array): 4D array of air mass
    all_data (boolean): return complete 4D array
    ctm (file object): PyGChem (v2.0) opened ctm.bpch file  - vestigle
    debug (boolean): legacy debug option, replaced by python logging
    res (str): the resolution if wd not given (e.g. '4x5' )
    t_p (np.array): fractional time a grid box has spent in tropospehre
    trop_limit (boolean): limit 4D arrays to troposphere
    total_atmos (boolean): return whole atmosphere or just troposphere?
    spec (str): species/tracer/variable name
    wd (str): Specify the wd to get the results from a run.
    arr (np.array): array of v/v for species

    Returns
    -------
    (np.array) species burden in Gg
    """
    logging.info('get_trop_burden called for {}'.format(spec) )
    # Get variables online if not provided
    if not isinstance(a_m, np.ndarray):
        a_m = get_air_mass_np( ctm_f=ctm, wd=wd, trop_limit=trop_limit, \
            debug=debug )
    if not isinstance(t_p, np.ndarray):
        # Retain PyGChem 0.2.0 approach for back compatibility
        if pygchem.__version__ == '0.2.0':
            t_p = get_gc_data_np( ctm=ctm, spec='TIMETROP',
                category='TIME-TPS', debug=debug)
        else:
            t_p = get_GC_output( wd, vars=['TIME_TPS__TIMETROP'], \
                trop_limit=trop_limit)
    # Retain PyGChem 0.2.0 approach for back compatibility
    if isinstance(arr, type(None) ):
        if pygchem.__version__ == '0.2.0':
            arr = get_gc_data_np( ctm, spec, debug=debug )[:,:,:38,:]
        else:
            arr = get_GC_output( wd, vars=['IJ_AVG_S__'+ spec], \
                trop_limit=trop_limit)
    logging.debug( 'Shape of arrays: ar={}, t_p={}, a_m={}'.format(
        *[ i.shape for i in (arr, t_p, a_m) ]) )
    # v/v * (mass total of air (kg)/ 1E3 (converted kg to g)) = moles of tracer
    arr = arr* ( a_m*1E3 / constants( 'RMM_air'))
    if Iodine:
        # Convert moles to mass (* RMM) , then to Gg
        arr = arr * float( species_mass('I') ) * spec_stoich(spec) /1E9
    else:
        # Convert moles to mass (* RMM) , then to Gg
        arr = arr * float( species_mass(spec) ) /1E9
    # Cut off at the "chemical troposphere" ( defined by GC integrator as 38th)
    if (not total_atmos):
        arr = arr * t_p
    else:
        logging.info( 'get_trop_burden returning whole atmosphere (not troposphere)' )
    if debug:
        print(('Got burden for {} from {}'.format( spec, ctm )))
    if all_data:
        return arr
    else:
        return arr.mean(axis=3)


# ----
# X.XX - Get O3 Burden
# ----
def get_O3_burden(wd=None, spec='O3', a_m=None, t_p=None, O3_arr=None, \
        ctm_f=False, trop_limit=True, all_data=False, annual_mean=True, \
        debug=False ):
    """ Wrapper of 'get_trop_burden' to get tropospheric ozone burden """
    # ---  Local vars.
    # (	all_data == ( annual_mean == False ) )
    if not annual_mean:
        all_data = True
    # ( total_atmos == trop_limit )
    if trop_limit:
        total_atmos = True
    # --- just call existing function
    return get_trop_burden(wd=wd, total_atmos=False, all_data=all_data,
        trop_limit=trop_limit, spec=spec, a_m=a_m, t_p=t_p, arr=O3_arr,
        ctm=ctm_f, debug=debug )


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# ---------------- Section X -------------------------------------------
# -------------- Redundant Functions
# --------------------------------------------------------------------------
#
# NOTE(s):
# (1) These are retained even though they are redundant for back compatibility
# (2) It is not advised to use these.
# (3) These will be removed when AC_tools is next re-structured.



# ----
# X.XX - Gg Ox yr^-1 from individual PORL-L$ rxns ([molec/cm3/s] )
# ----
def molec_cm3_s_2_Gg_Ox_np(arr, rxn=None, vol=None, ctm_f=None, \
        Iodine=False, I=False, IO=False, months=None, years=None, wd=None, \
        year_eq=True, month_eq=False, spec=None, res='4x5',debug=False ):
    """
    Convert species/tag prod/loss from "molec/cm3/s" to "Gg (Ox) yr^-1".

    !!! This is redundent. use convert_molec_cm3_s_2_g_X_s instead. !!!

    NOTES:
     - This function was originally used to process diagnostic outputs from PORL-L$
     - Alterate Output term apart from Ox are possible ( e.g. I, mass ... )
        Just stipulate input species
     - Output can also be requested on a monthly basis
        ( set  month_eq=True,  and year_eq=False )
    """
    if debug: print(' molec_cm3_s_2_Gg_Ox_np  called')
    if not isinstance(vol, np.ndarray):
        vol = get_volume_np( ctm_f=ctm_f, wd=wd, res=res )
        print('WARNING: extracting volume online - inefficent')
    # --- Process conversion
    if (Iodine):
        if debug: print((rxn , arr.shape, vol.shape))
        #  [molec/cm3/s] => * vol / moles * RAM *I in species / 1E9
        arr = ( arr * vol[:,:,:38,:] ) /  constants( 'AVG')* (127.) /1E9 * \
            spec_stoich( rxn, I=I, IO=IO )
    else: # ELSE return Gg X yr^-s ( ASSUMING UNITY OF TAG! )
        if ( rxn ==  'CH4' ):
            RMM =  species_mass(rxn)
        else:
            RMM =  species_mass('O3')
        # Return mass in terms of species provide ( if given )
        if not isinstance( spec, type(None) ):
            RMM = species_mass( spec  )
        arr = ( arr * vol[:,:,:38,:] ) / constants( 'AVG') * RMM /1E9
    # --- Process time from /s to ????
    if year_eq: # convert /second to / year
        arr = arr * 60*60*24*365
    if month_eq:
        day_adjust = d_adjust( months, years)
        arr = arr * day_adjust
    if debug:
        print(('arr', arr.shape , 'vol', vol.shape))
    return arr


# ----
# X.XX - Get Emission of species in g ( or other requested unit )
# ----
def get_emiss( ctm_f=None, spec=None, wd=None, years=None, \
        molec_cm2_s=False, nmonl_m2_d=False, kg_m2_s=False, \
        monthly=False, months=None, s_area=None, res='4x5', \
        ref_spec='I', debug=False ):
    """
    Extract given species emissions from BIOGSRCE category diagnostic

    Parameters
    -------

    Returns
    -------

    Notes
    -----
     - Back compatibility maintained with PyGChem 0.2.0
     - Asumption on iodine emissions
     ( set ref_spec to mass unit equivelnces wanted ( e.g. Br )  )
    """
    logging.info( 'get_emiss called for >{}<'.format(spec) )
    # Extract optional variables, if not provided as arguments
    if not isinstance(years, list):
        years = get_gc_years( ctm_f=ctm_f, set_=False, wd=wd )
    if not isinstance(months, list):
        months = get_gc_months( ctm_f=ctm_f, wd=wd)
    if not isinstance(s_area, np.ndarray):
        s_area = get_surface_area(res)  # m2 land map
    # Make array to adjust to "Gg (X) / month" from "Kg/m2/s"
    m_adjust = d_adjust(months, years)
    # Get emissions in  Kg/m2/ s
    # retain compatibility with version 0.2.0
    if pygchem.__version__ == '0.2.0':
        arr = get_gc_data_np( ctm_f, spec, category="BIOGSRCE")[:,:,0,:]
    else:
        arr = get_GC_output( wd=wd, species=spec, category="BIOGSRCE")
    # Get units as kg/m2/s or convert to kg/s
    if kg_m2_s:
        arr_ = arr
    else:
        # Kg/m2/ s => Kg/ s
        arr_ = arr*s_area
        # Kg/ s => "kg / month"
        arr_ = arr_ * m_adjust
        # g ( e.g. I  ) / month
        arr_ = arr_*1E3/ species_mass(spec)*species_mass(ref_spec) * \
            spec_stoich(spec)
    # Convert to units requested
    if nmonl_m2_d:
        # Convert to (g) / m2
        arr_  =  arr_ / s_area
        # Convert to (g) / m2 / day
        arr_  =  arr_ / (365./12.)
        # Convert to nmol ( /m2/day ) ( reverse normalisation to X mass equiv. )
        arr_ = arr_ / species_mass(ref_spec)  /  spec_stoich(spec)
        arr_ = arr_*1E9
        if debug: print(('get_emiss - 2', arr_.shape))
    if molec_cm2_s:
        # From  "I Gg/month" to "I Gg/month/cm/2" #convert to /m2 => cm/2
        arr_  =  arr_ / (s_area *10000.)
        # Convert to / day => hour => hour => minute => sec
        arr_  =  arr_ / (365./12.) / 24. / 60. / 60.
        # Convert to molecules ( reverse normalisation to X mass equiv. )
        arr_ = ( arr_ / species_mass(ref_spec)  ) / spec_stoich(spec) *\
                        constants('AVG')
        if debug: print(('get_emiss - 3', arr_.shape))
    return arr_


