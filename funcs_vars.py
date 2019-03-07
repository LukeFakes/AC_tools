#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Variable store/dictionarys for use in AC_Tools.

Use help(<name of function>) to get details on a particular function.


NOTE(S):
 - This code will be updated to use a user configuration apoach (*.rc file) shortly.
 - This module is underdevelopment vestigial/inefficient code is being removed/updated.
 - Where external code is used credit is given.
"""

# - Required modules:
# I/O / Low level
import re
import os
#import platform
import pandas as pd
from netCDF4 import Dataset
#import Scientific.IO.NetCDF as S
import sys
import glob
# Math/Analysis
import numpy as np

# the below import needs to be updated,
# imports should be specific and in individual functions
# import tms modules with shared functions
from  funcs4core import *


def pf_var(input, ver='3.0', ntracers=85, fill_var_with_zeroes=False):
    """
    Dictionary store for planeflight ("pf") names/tracers

    Parameters
    ----------
    input (string): tracer name to convert from GEOS-Chem to pf nomenclature
    ver (string): version number of halogen code (atop of GEOS-Chem)
    ntracers (integer): number of tracers in a given version of GEOSchem
    fill_var_with_zeroes (boolean): fill tracer name with zeroes (e.g.'1'=='001')

    Returns
    -------
    (string) of tracer/output variable in pf normenclature

    Notes
    -----
     - UPDATED NEEDED: MORE DETAILED DESCRIPT.
     - Why is this function not in funcs4pf?

    """
    # planeflight variable lists
    metvars = [
        'GMAO_TEMP', 'GMAO_ABSH', 'GMAO_SURF', 'GMAO_PSFC', 'GMAO_UWND', 'GMAO_VWND'
    ]
#    species  = [
#    'O3', 'NO2', 'NO', 'NO3', 'N2O5', 'HNO4', 'HNO3', 'HNO2', 'PAN', 'PPN',
#    'PMN', 'R4N2', 'H2O2', 'MP', 'CH2O', 'HO2', 'OH', 'RO2', 'MO2', 'ETO2',
#    'CO', 'C2H6', 'C3H8', 'PRPE', 'ALK4', 'ACET', 'ALD2', 'MEK', 'RCHO', 'MVK',
#    'SO2', 'DMS', 'MSA', 'SO4', 'ISOP'
#    ]
    species = [
        'A3O2', 'ATO2', 'B3O2', 'EOH', 'ETO2', 'ETP', 'GLYX', 'HO2', 'IAP', 'INO2', 'INPN', 'ISN1', 'ISNOOA', 'ISNOOB', 'ISNOHOO', 'ISNP', 'KO2', 'MAN2', 'MAO3', 'MAOP', 'MAOPO2', 'MCO3', 'MGLY', 'MO2', 'MRO2', 'MRP', 'OH', 'PO2', 'PP', 'PRN1', 'PRPN', 'R4N1', 'R4O2', 'R4P', 'RA3P', 'RB3P', 'RCO3', 'RIO2', 'ROH', 'RP', 'VRO2', 'VRP', 'LISOPOH', 'ISOPND', 'ISOPNB', 'HC5', 'DIBOO', 'HC5OO', 'DHMOB', 'MOBAOO', 'ISOPNBO2', 'ISOPNDO2', 'ETHLN', 'MACRN', 'MVKN', 'PYAC', 'IEPOXOO', 'ATOOH', 'PMNN', 'MACRNO2', 'PMNO2'
    ]
    OH_reactivity = [
        'NO', 'ISOP', 'GMAO_TEMP', 'GMAO_PSFC', 'CO', 'ACET', 'ALD2', 'MEK', 'MVK', 'MACR', 'C3H8', 'CH2O', 'C2H6', 'SO2', 'NO2', 'ISOPNB', 'ISOPND', 'NO3', 'HNO2', 'HNO3', 'OH', 'HO2', 'H2O2', 'MP', 'ATOOH', 'HNO4', 'ALK4', 'ISN1', 'R4N2', 'RCHO', 'ROH', 'PRPE', 'PMN', 'GLYC', 'GLYX', 'MGLY', 'HAC', 'INPN', 'PRPN', 'ETP', 'RA3P', 'RB3P', 'R4P', 'RP', 'PP', 'RIP', 'IEPOX', 'IAP', 'VRP', 'MRP', 'MAOP', 'MAP', 'DMS', 'HBr', 'Br2', 'BrO', 'CHBr3', 'CH2Br2', 'CH3Br', 'HC5', 'ISOPND', 'ISOPNB', 'ISNP', 'MVKN', 'MACRN', 'DHMOB', 'MOBA', 'ETHLN', 'PROPNN'
    ]
    OH_Extras4nic = [
        'OH', 'MCO3', 'A3O2', 'PO2', 'R4O2', 'R4O2', 'R4N1', 'ATO2', 'KO2', 'RIO2', 'VRO2', 'MRO2', 'MAN2', 'B3O2', 'INO2', 'ISNOOA', 'ISNOOB', 'ISNOHOO', 'PRN1', 'RCO3', 'MAO3', 'IEPOXOO', 'MAOPO2', 'MAOPO2', 'HC5OO', 'HC5OO', 'ISOPNDO2', 'ISOPNDO2', 'ISOPNBO2', 'ISOPNBO2', 'DIBOO', 'DIBOO', 'MOBAOO', 'MOBAOO', 'H2', 'CH4', 'HCOOH', 'MOH', 'ACTA', 'EOH', 'VRP'
    ]
    OH_rxns_17_EOH = [21,
                      328, 2, 387, 6, 7, 136, 9, 10, 407, 14, 15, 16, 408, 402, 403, 406, 23, 152, 25, 27, 28, 30, 415, 33, 35, 164, 167, 40, 169, 43, 172, 173, 48, 49, 178, 179, 52, 201, 58, 60, 394, 62, 319, 320, 66, 323, 196, 197, 198, 199, 200, 177, 202, 203, 204, 333, 206, 210, 211, 212, 334, 214, 215, 176, 345, 346, 347, 94, 357, 226, 101, 102, 103, 365, 113, 114, 153, 378, 379, 380, 364
                      ]
    OH_rxns_17_EOH = ['REA_{}'.format(i) for i in OH_rxns_17_EOH]

    # OH reaction species and tracers
    OH_rxn_tras = ['HBr', 'HOI', 'I2', 'CH2O', 'NO2', 'HNO3', 'CH3IT', 'NO', 'HNO3', 'HNO2', 'PRPE', 'PMN', 'HNO4', 'GLYC', 'NO3', 'C3H8', 'DMS', 'ALK4', 'SO2', 'MVK', 'ISOP',
                   'CHBr3', 'BrO', 'ISOP', 'CH2Br2', 'CH3Br', 'ACET', 'MEK', 'H2O2', 'CO', 'PROPNN', 'MP', 'MACR', 'HAC', 'ALD2', 'MOBA', 'RIP', 'Br2', 'IEPOX', 'MAP', 'R4N2', 'RCHO', 'HI']
    OH_rxn_tras = [num2spec(i, ver=ver, invert=True) for i in OH_rxn_tras]
    OH_rxn_tras = ['TRA_{:0>2}'.format(i) for i in OH_rxn_tras]
    OH_rxn_specs = ['GLYX', 'MGLY', 'HCOOH', 'MOH', 'O2', 'DHMOB', 'HO2', 'OH', 'H2', 'CH4', 'ETHLN', 'EOH', 'ATOOH', 'R4P', 'INPN', 'RA3P',
                    'RB3P', 'RP', 'PP', 'IAP', 'VRP', 'MRP', 'MAOP', 'ISN1', 'HC5', 'ACTA', 'ISOPNB', 'ROH', 'ISNP', 'MVKN', 'MACRN', 'ISOPND', 'ETP', 'PRPN']

    # remove inactive species
    inactive_spec = ['ACTA', 'CH4', 'H2', 'HCOOH', 'MOH', 'O2']  # 'EOH',

    # Setup list of tracers
    if any([(ver == i) for i in ('1.6', '1.6.1', '1.6.2')]):
        ntracers = 96
    elif any([(ver == i) for i in ('1.6.3', '1.6.4')]):
        ntracers = 98
    elif ver == '1.7':
        ntracers = 85
    elif any([(ver == i) for i in ('2.0', '3.0')]):
        ntracers = 103
    if ver == 'johan_br.v92':
        ntracers = 87
    # fill with zeros?
    TRAs = ['TRA_' + str(i) for i in range(1, ntracers+1)]
    if fill_var_with_zeroes:
        #    TRAs = ['TRA_{:0>2}'.format(i) for i in range(1, ntracers+1) ]
        TRAs = ['TRA_{:0>3}'.format(i) for i in range(1, ntracers+1)]

    # Setup list of reactions ( photolysis and general )
    if ver == '1.5':
        PHOT_1st, PHOT_last = 455, 533
    elif ver == '1.6':
        PHOT_1st, PHOT_last = 453, 531
    elif ver == '1.6.1':
        PHOT_1st, PHOT_last = 453, 530
    elif ver == '1.6.2':
        PHOT_1st, PHOT_last = 452, 529
    elif ver == '1.6.3':
        PHOT_1st, PHOT_last = 461, 538
    elif ver == '1.7':
        PHOT_1st, PHOT_last = 453, 529
    elif ver == '2.0':
        #        PHOT_1st, PHOT_last = 413, 614 # dev
        PHOT_1st, PHOT_last = 519, 607
    elif ver == '3.0':
        #        PHOT_1st, PHOT_last = 537, 627 # coupled sim.
        #        PHOT_1st, PHOT_last = 554, 644 # With IX split rxns
        PHOT_1st, PHOT_last = 548, 638  # With 0.25 IBr split rxns
    else:
        print(('pf_var not setup for ver: ', ver))

    JREAs = ['REA_' + str(i) for i in range(PHOT_1st, PHOT_last)]
    REAs_all = ['REA_' + str(i) for i in range(0, 533)]

    # reduced list for high time and spatial resolution
    if any([input == i for i in ('slist_v9_2_NREA_red',
                                 'slist_v9_2_NREA_red_NOy')]):
        TRAs = GC_var('active_I') + ['AERI']
        TRAs = [num2spec(i, ver=ver, invert=True) for i in TRAs]
        TRAs = ['TRA_{:0>2}'.format(i) for i in TRAs]

        metvars = [i for i in metvars if not any([(i == ii)
                                                  for ii in ('GMAO_ABSH', 'GMAO_SURF', 'GMAO_PSFC')])]
        species = [i for i in species if not any([(i == ii) for ii in
                                                  ('R4N2', 'MP', 'CH2O', 'MO2', 'ETO2', 'CO', 'C2H6', 'C3H8', 'PRPE',
                                                   'ALK4', 'ACET', 'ALD2', 'MEK', 'RCHO', 'MVK', 'DMS', 'MSA', 'ISOP')
                                                  ])]

    if input == 'slist_ClearFlo':
        TRAs = 'CO', 'ACET', 'ALD2', 'ISOP', 'C2H6', 'C3H8', 'CH2O', \
            'MACR', 'HNO2', 'HNO3', 'MVK', 'NO', 'NO2', 'PAN', 'O3',
        TRAs = [num2spec(i, ver=ver, invert=True) for i in TRAs]
        TRAs = ['TRA_{:0>2}'.format(i) for i in TRAs]
        # mannually add ethanol
        TRAs += ['TRA_86']
        species = ['OH', 'MO2', 'HO2']

    if input == 'slist_PEN_WEY_LEI':
        TRAs = 'NO', 'NO2', 'PAN', 'HNO2', 'HNO3', 'O3',\
            'CO', 'ISOP', 'R4N2', 'PRPE', 'CH2O', \
            'NO3', 'N2O5', \
            'MP', 'DMS', 'SO2', \
            'BrCl', 'Cl2', 'Cl', 'ClO', 'HOCl', 'HCl', 'ClNO2', 'ICl', \
            'SO4', 'SO4s', 'MSA', 'NH3', 'NH4', 'NIT', 'NITs', \
            'SALA', 'SALC',\
            #             'ACET', 'ALD2', 'C2H6', 'C3H8', 'MACR', 'MVK',
        TRAs = [num2spec(i, ver=ver, invert=True) for i in TRAs]
        TRAs = ['TRA_{:0>2}'.format(i) for i in TRAs]
        # Species? ( aka ones that are not transported )
        species = ['OH', 'HO2']

    if input == 'slist_v9_2_NREA_red_NOy':
        # THIS IS NOT A GOOD APPROACH, use actual names an tranlate based on verison.
        #        missing = [  'TRA_17', 'TRA_60', 'TRA_30', 'TRA_31', 'TRA_50', \
        #            'TRA_54', 'TRA_55', 'TRA_57' ]

        #            use tracer  TRA_60, TRA_30, TRA_31, for: 'MMN' , 'NH3' , 'NH4',  'R4N2', 'BrNO2', 'BrNO3','MPN', 'PROPNN',
        missing = 'MMN', 'NH3', 'NH4',  'R4N2', 'BrNO2', 'BrNO3', 'MPN', 'PROPNN'
        missing = [num2spec(i, ver=ver, invert=True) for i in missing]
        missing = ['TRA_{:0>2}'.format(i) for i in missing]
        species = species + missing

    # use TRA_?? instead of species if species is a tracer
    species_ = []
    for s in species:
        try:
            species_ += ['TRA_{}'.format(num2spec(s, ver=ver,
                                                  invert=True))]
        except:
            species_ = [s]
    species = species_

    # Construct dictionary
    d = {
        'species': species,
        'metvars': metvars,
        'REAs_all': REAs_all,
        'JREAs': JREAs,
        'TRAs': TRAs,
        'slist':  species + TRAs + JREAs + metvars,
        'slist_v9_2_NH':   species + TRAs[:66] + metvars,
        'slist_v9_2_NREA':   species + TRAs + metvars,
        'slist_v9_2_NREA_red': species + TRAs + metvars,
        'slist_REAs_all':   species + TRAs + REAs_all + metvars,
        'slist_REAs_all_OH':   species + TRAs + metvars+OH_reactivity,
        'slist_REAs_all_OH_extras':   species + TRAs + metvars,
        'slist_v9_2_NREA_red_NOy': species + TRAs + metvars,
        'slist_v10_1.7_allspecs': species + TRAs + JREAs + metvars,
        'slist_ClearFlo': species + TRAs + metvars,
        'slist_ClearFlo_OH_rxn': species + TRAs + metvars + OH_rxns_17_EOH + OH_rxn_tras + OH_rxn_specs,
        'slist_PEN_WEY_LEI': species + TRAs + metvars
    }

    # retrieve variable list from dictionary
    vars = d[input]

    # return unique list
    vars = sorted(list(set(vars)))

    # remove inactive tracers/species
    inactive_spec = [n for n, i in enumerate(vars) if (i in inactive_spec)]
    print(inactive_spec)
    [vars.pop(i) for i in sorted(inactive_spec)[::-1]]
    print(vars)

    return vars


def what_species_am_i(input=None, V_9_2=True, V_9_2_C=False, ver='1.7',
                      special_case=None, invert=False, rtn_dict=False, debug=False):
    """
    Converts a GEOS-Chem (GC) species/tracer into a PF tracer (TRA_##).
            takes TRA_## & returns GC ID or other wayround

    Parameters
    ----------
    wd (string): the wd to get the results from a run
    res (string): the resolution if wd not given ( e.g. '4x5')
    invert (boolean): invert dictionary keys and values
    debug = False (legacy debug, replaced by logging)
    V_9_2, V_9_2_C = redundent oiption swicthes for previous GEOS-Chem versions
    special_case = overide seclected species dictionary

    Returns
    -------
    (string) species name in GEOS-Chem tracer naming nomenclature (or entire directory
    if rtn_dict=True)

    Notes
    -----
     - Species have the same names in PF, but units are in molec/cm3, not
       mixing ratio (v/v)
     -  Generic v10 and v11 need adding to this list

    """
    # select correct naming dictionary
    var = {
        '1.6': 'GCFP_d2TRA_all_1.6',
        '1.6.2': 'GCFP_d2TRA_all_1.6',  # same as 1.6
        '1.6.3': 'GCFP_d2TRA_all_1.6.3',  # 1.6 + 2
        '1.7': 'GCFP_d2TRA_all_1.7',
        '2.0': 'GCFP_d2TRA_all_2.0',
        '3.0':  'GCFP_d2TRA_all_2.0',  # Same as 2.0
        '4.0':  'GCFP_d2TRA_all_2.0',  # Same as 2.0
        '5.0':  'GCFP_d2TRA_all_2.0',  # Same as 2.0? - Kludge for now
    }[ver]

#    special_case = 'EOH'
#    special_case = 'EOH + actual names'
#    if all_TRA:
#            var ={  \
#            '1.7': 'all_TRA_spec_met_1.7_EOH'
#            '1.6': 'GCFP_d2TRA_1.6'
#            }[ver]

    if not isinstance(special_case, type(None)):
        var = {
            #         'EOH':'GCFP_d2TRA_all_1.7_EOH',
            #        'EOH + actual names':'GCFP_d2TRA_all_1.7_EOH_actual_names'
            'all_TRA_spec_met_1.7_EOH.zeros': 'TRA_spec_met_all_1.7_EOH',  # '
            'all_TRA_spec_met_1.7_EOH': 'TRA_spec_met_all_1.7_EOH_no_trailing_zeroes'
            #        TRA_spec_met_all_1'
        }[special_case]

    # Get dictionary from variable store
    d = GC_var(var)

    if debug:
        print((d, special_case))

    if invert:
        d = {v: k for k, v in list(d.items())}

    # return dictionary
    if rtn_dict:
        return d
    else:
        return d[input]


def num2spec(num=69, rtn_dict=False, invert=False, ver='1.7'):
    """
    Parameters
    ----------
    ver (str): Specify the wd to get the results from a run.
    num (int): the resolution if wd not given (e.g. '4x5' )
    rtn_dict (boolean): legacy debug option, replaced by python logging
    invert (boolean): uses spec as the keys in the dictionary

    Returns
    -------
    (int) number of tracer in GEOS-Chem or dictionary of tracer names and indicies (dict)

    Notes
    -----
     - Also works in reverse or returns whole dictionary to remove need to remake
    dictionary for each call.
     - Version number needed ( e.g. "Cl+Br+I" = 3.0, "1.7" = "Br+I",
     - UPDATE NEEDED: basecase v9-2/v10 not currently included
    """

    # --- Get dictionary of tracer numbers
    d = what_species_am_i(ver=ver, rtn_dict=True, special_case=None)

    # --- Slice off just numbers
    # special case for dev version?
    if any([(ver == i) for i in ('1.6', '1.6.2',)]):
        d = GC_var('GCFP_d2TRA_justTRA_1.6')
    if any([(ver == i) for i in('1.6.3', '1.6.4')]):
        d = GC_var('GCFP_d2TRA_justTRA_1.6.3')
    # Then slice
    nums = [int(i[4:]) for i in list(d.keys())]

    # --- Re-make dictionary
    d = dict(list(zip(nums, list(d.values()))))

    # --- Invert to give spec for num
    if invert:
        d = {v: k for k, v in list(d.items())}

    if rtn_dict:
        return d
    else:
        return d[num]


def species_mass(spec):
    """
    Function to get species relative molecular mass (RMM) in g/mol

    Parameters
    ----------
    spec (str): species/tracer/variable name

    Returns
    -------
    (float)

    Notes
    -----
     - C3H5I == C2H5I (this is a vestigle typo, left in to allow for
    use of older model run data  )
    """
    d = {
        'HIO3': 176.0, 'Br2': 160.0,  'O3': 48.0,
        'PAN': 121.0, 'RIP': 118.0, 'BrNO3': 142.0, 'Br': 80.0,
        'HBr': 81.0, 'HAC': 74.0,  'HNO3': 63.0, 'HNO2': 47.0,
        'C2H5I': 168.0, 'HNO4': 79.0, 'OIO': 159.0, 'MAP': 76.0,
        'CH2I2': 268.0, 'IONO2': 189.0, 'NIT': 62.0, 'CH3Br': 95.0,
        'C3H7I': 170.0, 'DMS': 62.0, 'CH2O': 30.0, 'CH3IT': 142.0,
        'NO2': 46.0, 'NO3': 62.0, 'N2O5': 105.0, 'H2O2': 34.0, 'DST4': 29.0,
        'DST3': 29.0, 'DST2': 29.0, 'DST1': 29.0, 'MMN': 149.0, 'HOCl': 52.0,
        'NITs': 62.0, 'RCHO': 58.0,  'MPN': 93.0, 'INO': 157.0,
        'MP': 48.0, 'CH2Br2': 174.0, 'SALC': 31.4, 'NH3': 17.0, 'CH2ICl': 167.0,
        'IEPOX': 118.0, 'ClO': 51.0, 'NO': 30.0, 'SALA': 31.4, 'MOBA': 114.0,
        'R4N2': 119.0, 'BrCl': 115.0, 'OClO': 67.0, 'PMN': 147.0, 'CO': 28.0,
        'MVK': 70.0, 'BrNO2': 126.0,
        'IONO': 173.0, 'Cl2': 71.0, 'HOBr': 97.0, 'PROPNN': 109.0, 'Cl': 35.0,
        'I2O2': 286.0, 'I2O3': 302.0, 'I2O4': 318.0, 'I2O5': 334.0,
        'HI': 128.0, 'ISOPN': 147.0, 'SO4s': 96.0, 'I2O': 270.0,
        'MSA': 96.0, 'I2': 254.0, 'PPN': 135.0, 'IBr': 207.0, 'MACR': 70.0,
        'I': 127.0, 'AERI': 127.0, 'HOI': 144.0, 'BrO': 96.0, 'NH4': 18.0,
        'SO2': 64.0, 'SO4': 96.0, 'IO': 143.0, 'CHBr3': 253.0, 'CH2IBr': 221.0,
        'ICl': 162.0, 'GLYC': 60.0, \
        # Carbon/VOC species - WARNING these are considered in units cf C equiv.
        # (following GEOS-Chem approach)
        'ALD2': 12.0, 'ACET': 12.0, 'PRPE': 12.0, 'OCPO': 12.0,  'OCPI': 12.0, \
        'C3H8': 12.0, 'C2H6': 12.0, 'BCPI': 12.0, 'ISOP': 12.0, 'BCPO': 12.0,\
        'ALK4': 12.0, 'MEK': 12.0, \
        # species, not in GEOS-Chem tracer list
        'HO2': 33.0, 'OH': 17.0, 'CH4': 16.0, 'N': 14.0, 'CH3I': 142.0, \
        'CH2OO': 46.0, 'S': 32.0, \
        # Carbon species not in GEOS-Chem
        'C2H4': 12.0,
        # Additional 2.0 species
        'HCl': 36.5, 'HOCl': 52.5, 'ClNO2': 81.5, 'ClNO3': 97.5, 'ClOO': 67.5, \
        'Cl2O2': 103.0,  'CH3Cl':  50.5, 'CH2Cl2': 85.0, 'CHCl3': 119.5, \
        'BrSALA': 80., 'BrSALC': 80., 'ISALA': 127.,  'ISALC': 127., \
        # Additional "species" to allow for ease of  processing
        'AERI_AVG': ((286.0+302.0+318.0)/3)/2, 'SO4S': 96.0,
        'IO3': 127.+(3.*16.), 'SSBr2': 160.0, 'C': 12.0,
        # Add families for ease of processing
        'Iodine': 127.0, 'Iy': 127., 'Bromine': 80.0, 'Bry': 80.0, 'Chlorine': 35.0,
        'Cly': 35.0, 'NOy': 14.0, 'NOx': 14.0, 'SOx': 32.0,\
        'Sulfate': 32.0, 'sulfur': 32.0, 'VOCs': 12.0,
        # v11-01 standard extra tracers...
        'ASOA1': 150.0, 'ASOA3': 150.0, 'ASOA2': 150.0, 'ASOG3': 150.0, \
        'ASOG2': 150.0, 'ASOG1': 150.0, 'TSOA0': 150.0, 'TSOA1': 150.0, \
        'TSOA2': 150.0, 'TSOA3': 150.0, 'TSOG2': 150.0, 'TSOG3': 150.0, \
        'TSOG0': 150.0, 'TSOG1': 150.0, 'MVKN': 149.0, 'MACRN': 149.0, \
        'MTPO': 136.0, 'ISOPND': 147.0, 'LIMO': 136.0, 'ISOPNB': 147.0, \
        'MTPA': 136.0, 'NITS': 31.0, 'ISOG3': 150.0, 'ISOG2': 150.0, \
        'ISOG1': 150.0, 'ISOA1': 150.0, 'ISOA3': 150.0, 'ISOA2': 150.0, \
        'ASOAN': 150.0,
        # more v11-01 advected tracers...
        'H2O': 18.0, 'N2O': 44.0, 'CFC11': 137.0, 'CFC12': 121.0, \
        'H1211': 165.0, 'BENZ': 78.11, 'H1301': 149.0, 'CFC114': 187.0, \
        'TOLU': 92.14, 'CH3CCl3': 133.0, 'CCl4': 152.0, 'HCFC22': 86.0, \
        'CFC113': 187.0, 'HCFC141b': 117.0, 'CFC115': 187.0, 'OCS': 60.0, \
        'XYLE': 106.16, 'H2402': 260.0, 'HCFC142b': 117.0, 'HCFC123': 117.0, \
        # Extra species in v12.x
        'GLYX': 58.0, 'MGLY': 72.0, 'SOAP': 150.0, 'SOAS': 150.0, 'NPMN': 147.0, \
        u'RIPB': 118.0, u'LVOCOA': 154.0, u'IEPOXD': 118.0, u'IEPOXB': 118.0, \
        u'IEPOXA': 118.0, u'RIPD': 118.0, u'LVOC': 154.0, u'INDIOL': 102.0, \
        u'RIPA': 118.0, u'IPMN': 147.0, u'DHDN': 226.0, u'HPALD': 116.0, \
        u'SOAGX': 58.0, u'MGLY': 72.0, u'IONITA': 14.0, u'NPMN': 147.0, \
        u'MONITS': 215.0, u'MONITU': 215.0, u'MONITA': 14.0, u'HC187': 187.0, \
        u'ISN1OG': 226.0, u'ISN1OA': 226.0, u'IMAE': 102.0, u'ETHLN': 105.0, \
        u'SOAIE': 118.0, u'HONIT': 215.0, u'GLYX': 58.0, u'SOAME': 102.0, \
        u'SOAMG': 72.0, u'HCOOH': 46.0, u'ISN1': 147.0, u'ACTA': 60.0, \
        u'SOAP': 150.0, u'SOAS': 150.0,
        # Temporary species or values where numbers not known for certain.
        'pFe': 55.85, 'EOH': 46.07
    }

    return d[spec]


def spec_stoich(spec, IO=False, I=False, NO=False, OH=False, N=False,
                C=False, Br=False, Cl=False, S=False, ref_spec=None, debug=False):
    """
    Returns unit equivalent of X ( e.g. I ) for a given species. This can be automatically
    set by providing a reference species or by setting boolean input parametiers.

    Parameters
    ----------
    spec (str): species/tracer/variable name
    ref_spec (str): species which number of spec equiv. in is being sought
    wd (str): Specify the wd to get the results from a run.
    res (str): the resolution if wd not given (e.g. '4x5' )
    debug (boolean): legacy debug option, replaced by python logging
    IO, I, NO, OH, N, C, Br, Cl, S (boolean): reference species to use (defualt = I)

    Returns
    -------
    (float) number equivlent units of ref_spec in spec.

    Notes
    -----
     - Update Needed: re-write to take stioch species (e.g. OH, I instead of booleans )
     - asssume I == True as default
     - C3H5I == C2H5I
        (this is a vestigle typo, left in to allow for use of older model runs )
     - aerosol cycling specs
    # 'LO3_36' : (2.0/3.0) , 'LO3_37' : (2.0/4.0),  # aersol loss rxns... 'LO3_37' isn't true loss, as I2O4 is regen. temp
     - Aerosol loss rxns ( corrected stoichio for Ox, adjsutment need for I )
    """
    # If reference species provided automatically select family
    if not isinstance(ref_spec, type(None)):
        if any([(ref_spec == i) for i in ('I', 'Iy', 'Iodine')]):
            I = True
        if any([(ref_spec == i) for i in ('Br', 'Bry', 'Bromine')]):
            Br = True
        if any([(ref_spec == i) for i in ('Cl', 'Cly', 'Chlorine')]):
            Cl = True
        if any([(ref_spec == i) for i in ('C', 'VOC')]):
            C = True
        if any([(ref_spec == i) for i in ('N', 'NOy', 'NOx')]):
            N = True
        if any([(ref_spec == i) for i in ('OH', 'HO2')]):
            OH = True
        if ref_spec == 'IO':
            IO = True
        if ref_spec == 'NO':
            NO = True
        if any([(ref_spec == i) for i in ('S', 'SOx', 'Sulfate')]):
            S = True

    if debug:
        vars = ref_spec, IO, I, NO, OH, N, C, Br, Cl
        varsn = 'ref_spec', 'IO', 'I', 'N', 'OH', 'N', 'C', 'Br', 'Cl'
        print(("'spec_stoich'  called for: ", list(zip(varsn, vars))))

    # Select dictionary ( I=True is the default... )
    if IO:
        d = {
            'RD11': 2.0, 'RD10': 1.0, 'RD12': 2.0, 'LO3_36': 1./3., 'RD09': 1.0,
            'RD66': 1.0, 'RD23': 1.0, 'RD37': 1.0, 'LO3_24': 1.0/2.0, 'RD56': 1.0,
            'RD01': 1.0, 'RD08': 1.0, 'RD46': 2.0, 'RD30': 1.0, 'RD25': 1.0,
            'RD27': 1.0, 'RD97': 1.0
        }
    elif NO:
        d = {
            'NO2': 1.0, 'NO3': 1.0, 'N2O5': 2.0, 'NO': 1.0, 'PPN': 1.0, 'R4N2': 1.0,
            'BrNO3': 1.0, 'INO': 1.0, 'PAN': 1.0, 'PMN': 1.0, 'HNO3': 1.0,
            'HNO2': 1.0, 'NH3': 1.0, 'HNO4': 1.0, 'BrNO2': 1.0,
            'IONO': 1.0, 'PROPNN': 1.0, 'NH4': 1.0, 'MPN': 1.0, 'MMN': 1.0,
            'ISOPN': 1.0, 'IONO2': 1.0
        }
    elif OH:
        d = {
            'LO3_18': 2.0, 'LO3_03': 1.0,  'PO3_14': 1.0, 'RD65': 1.0, 'LR25': 1.0,
            'LOH': 1.0, 'POH': 1.0, 'LO3_86': 1.0, 'RD98': 1.0, \
            # Redundent: 'RD95': 1.0,
            # also include HO2 and OH for HOx calculations
            'OH': 1.0, 'HO2': 1.0
        }
    elif S:
        d = {
            'S': 1.0, 'SO4': 1.0, 'SO4s': 1.0, 'SO4S': 1.0, 'SO2': 1.0
        }
    elif N:
        d = {
            'RD10': 1.0, 'LR26': 1.0, 'LR27': 1.0, 'LR20': 1.0, 'RD17': 1.0,
            'RD16': 1.0, 'RD19': 1.0, 'RD18': 2.0, 'LR28': 1.0, 'LO3_30': 1.0,
            'RD75': 1.0, 'LR7': 1.0, 'LR8': 1.0, 'RD56': 1.0, 'RD24': 1.0,
            'LO3_39': 1.0, 'RD25': 1.0, 'RD81': 1.0, 'LR35': 1.0, 'LR18': 1.0,
            'LR17': 1.0, 'LR11': 1.0, 'LR39': 1.0, 'RD20': 1.0, 'RD21': 2.0,
            'RD22': 1.0, 'RD23': 1.0, 'RD68': 1.0, 'RD69': 1.0, \
            # NOy ( N in 'NOy')
            'NO2': 1.0, 'NO3': 1.0, 'N2O5': 2.0, 'NO': 1.0, 'PPN': 1.0, \
            'R4N2': 2.0, 'BrNO3': 1.0, 'INO': 1.0, 'PAN': 1.0, 'PMN': 1.0, \
            'HNO3': 1.0, 'HNO2': 1.0, 'NH3': 1.0, 'HNO4': 1.0, 'BrNO2': 1.0, \
            'IONO': 1.0, 'PROPNN': 1.0, 'NH4': 1.0, 'MPN': 1.0, 'MMN': 1.0, \
            'ISOPN': 1.0, 'IONO2': 1.0, 'ClNO2': 1.0, 'ClNO3': 1.0,
            'NIT': 1.0, 'NITs': 1.0, 'NITS': 1.0, \
        }
    elif C:
        d = {
            'ACET': 3.0, 'ALD2': 2.0, 'C2H6': 2.0, 'C3H8': 3.0, 'ISOP': 5.0,
            'PRPE': 3.0, 'ALK4': 4.0, 'MEK': 4.0,
            'APINE': 10.0, 'BPINE': 10.0, 'LIMON': 10.0, 'SABIN': 10.0, 'MYRCN': 10.0,
            'CAREN': 10.0, 'OCIMN': 10.0,
        }
    elif Br:
        d = {
            'CH3Br': 1.0, 'HOBr': 1.0, 'BrO': 1.0, 'CHBr3': 3.0, 'Br2': 2.0,
            'BrSALC': 1.0, 'CH2IBr': 1.0, 'BrCl': 1.0, 'Br': 1.0, 'CH2Br2': 2.0,
            'IBr': 1.0, 'BrSALA': 1.0, 'BrNO2': 1.0, 'BrNO3': 1.0, 'HBr': 1.0, \
            # for ease of processing also include Seasalt Br2
            'SSBr2': 2.0,
            # Also have reaction tracers
            'LR73': 1.0,
            # Note: stoichometry is for **GAS** phase Br (aka not SSA )
            # ( Aka JT03s == Br2 ( ==2 ), but one is BrSALA/BrSALC therefore =1)
            'JT03s': 1.0, 'JT04s': 1.0, 'JT05s': 1.0,
            # BrCl from HOBr or hv
            'JT02s': 1.0, 'JT08': 1.0,
            # v11 KPP Tags
            'T149': 3.0, 'T127': 0.680+1.360, 'T126': 0.440+0.560, 'T071': 3.0,
            'T198': 0.150, 'T199': 0.150, 'T200': 0.150, 'T082': 1.0
        }
    elif Cl:
        d = {
            'ClO': 1.0, 'Cl': 1.0, 'ClOO': 1.0, 'ClNO3': 1.0, 'ClNO2': 1.0,
            'Cl2': 2.0, 'OClO': 1.0, 'HOCl': 1.0, 'HCl': 1.0, 'Cl2O2': 2.0,
            'BrCl': 1.0, 'ICl': 1.0, 'CH2Cl2': 2.0, 'CHCl3': 3.0, 'CH2ICl': 1.0,
            'CH3Cl': 1.0,
            # Also have reaction tracers
            'LR62': 3.0, 'LR107': 3.0,
            'LR74': 1.0, 'LR106': 1.0, 'LR103': 1.0,
            'LR75': 2.0, 'LR105': 2.0, 'LR104': 2.0,
            # BrCl from HOBr or hv
            'JT02s': 1.0, 'JT08': 1.0,
            # ICl  (assuming 0.85:0.15 )
            'RD59': 0.15, 'RD92': 0.15, 'RD63': 0.15,
            # N2O5+SSA=>ClNO2
            'LR114': 1.0,
            # v11 KPP Tags
            'T174': 3.0, 'T203': 3.0,
            'T173': 2.0, 'T201': 2.0, 'T202': 2.0,
            'T172': 1.0, 'T171': 1.0, 'T143': 1.0,
            'T155': 1.0, 'T135': 1.0, 'T212': 1.0,
            'T198': 0.850, 'T199': 0.850, 'T200': 0.850,
            'PT213': 1.0, 'PT214': 1.0,
        }
    else:  # ( I=True is the default... )
        d = {
            'RD11': 1.0, 'RD10': 1.0, 'HIO3': 1.0, 'RD15': 1.0, 'RD62': 2.0,
            'RD17': 1.0, 'RD16': 1.0, 'RD19': 1.0, 'LO3_37': 0.5, 'CH2I2': 2.0,
            'AERII': 1.0, 'CH2ICl': 1.0, 'PIOx': 1.0, 'C3H7I': 1.0, 'RD73': 1.0,
            'RD72': 2.0, 'RD71': 1.0, 'RD70': 1.0, 'C3H5I': 1.0, 'RD57': 1.0,
            'CH3IT': 1.0, 'IO': 1.0, 'LO3_38': 1.0, 'RD61': 1.0, 'RD68': 1.0,
            'I2': 2.0, 'IONO': 1.0, 'LO3_36': 0.6666666666666666, 'INO': 1.0,
            'RD88': 1.0, 'RD89': 1.0, 'LOx': 1.0, 'RD06': 1.0, 'RD07': 1.0,
            'RD02': 1.0, 'RD01': 1.0, 'I': 1.0,  'LO3_24': 0.5, 'AERI': 1.0,
            'HOI': 1.0, 'RD64': 2.0, 'RD65': 1.0, 'RD66': 1.0, 'RD67': 1.0,
            'RD60': 1.0, 'RD47': 1.0, 'C2H5I': 1.0, 'RD63': 1.0, 'RD20': 1.0,
            'RD22': 1.0, 'RD24': 1.0, 'RD69': 1.0, 'RD27': 1.0, 'OIO': 1.0,
            'CH2IBr': 1.0, 'LIOx': 1.0, 'L_Iy': 1.0, 'ICl': 1.0, 'IBr': 1.0,
            'RD95': 2.0, 'I2O2': 2.0, 'I2O3': 2.0, 'I2O4': 2.0, 'I2O5': 2.0,
            'HI': 1.0, 'I2O': 2.0, 'RD59': 1.0, 'RD93': 2.0, 'RD92': 1.0,
            'IONO2': 1.0, 'RD58': 1.0, 'ISALA': 1.0, 'ISALC': 1.0, 'CH3I': 1.0, \
            # p/l for: IO, I
            'RD15': 1.0, 'RD17': 1.0, 'RD75': 1.0, 'RD72': 2.0, 'RD71': 1.0, \
            'RD70': 1.0, 'RD56': 1.0, 'RD69': 1.0, 'RD88': 1.0, 'RD89': 1.0, \
            'RD06': 1.0, 'RD07': 1.0, 'RD08': 1.0, 'RD64': 2.0, 'RD65': 1.0, \
            'RD67': 1.0, 'RD46': 2.0, 'RD47': 1.0, 'RD20': 1.0, 'RD22': 1.0, \
            'RD68': 1.0, 'RD25': 1.0, 'RD96': 1.0, 'RD11': 1.0, 'RD12': 2.0, \
            'RD02': 1.0, 'RD16': 1.0, 'RD19': 1.0, 'RD24': 1.0, 'RD09': 1.0, \
            'RD23': 1.0, 'RD37': 1.0, 'RD97': 1.0, \
            # kludge for test analysis (HEMCO emissions )
            'ACET': 1.0, 'ISOP': 1.0, 'CH2Br2': 1.0, 'CHBr3': 1.0, 'CH3Br': 1.0, \
            # Iodine in het loss/cycling reactions
            # loss to SSA/other aerosols
            # HOI
            'LR44': 1.0, 'LR45': 1.0, 'LR32': 1.0,   \
            # HI other
            'LR34': 1.0, \
            # IONO2
            'LR42': 1.0, 'LR43': 1.0, 'LR35': 1.0, \
            # IONO
            'LR46': 1.0, 'LR47': 1.0, 'LR39': 1.0,
            # --- KPP tags
            # Iy cycling sinks...
            'T217': 1.0, 'T216': 1.0, 'T198': 1.0, 'T199': 1.0, 'T196': 1.0,
            'T183': 1.0, 'T195': 1.0, 'T184': 1.0,  'T215': 1.0, 'T197': 1.0,
            # I2Oy
            'T190': 2.0, 'T193': 2.0, 'T187': 2.0,
            'T186': 2.0, 'T189': 2.0, 'T192': 2.0,
            'T185': 2.0, 'T188': 2.0, 'T191': 2.0,
        }

    # Kludge for testing. Allow values to equal 1.0 if not defined.
    try:
        if debug:
            print(('{} (ref_spec: {}) stoichiometry : {}'.format(spec,
                                                                 ref_spec,  d[spec])))
        return d[spec]

    except:
        print(('!'*20, 'WARNING - Kludge assumming stoichiometry = 1.0, for' +
               ' {} (ref_spec given as: {})'.format(spec, ref_spec)))
        return 1.0


def tra_unit(x, scale=False, adjustment=False, adjust=True, global_unit=False,
             ClearFlo_unit=False, IUPAC_unit=False, use_pf_species_units=False,
             debug=False):
    """
    Get appropirate unit for Tracer (and scaling if requested)

    Parameters
    ----------
    x (str): species/tracer/variable name
    adjustment (float): adjustment to give unit (+,- value etc )
    scale (float): scaling factor for unit
    adjust (boolean): set==True to adjust input.geos unit values to adjusted values
    global_unit (boolean): set units to globally relevent ones
    IUPAC_unit (boolean): set units to IUPAC uints
    ClearFlo_unit (boolean): set units to those used in the ClearFlo campaign
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    units (str), adjustment to give units (float), and scaling for units (float)

    Notes
    -----
     - Is this redundent now with the species class?
     - "Appropirate" unit is taken from GEOS-Chem input.geos
     - Option to use IUPAC unit. ( set IUPAC_unit==True )
    """
    tra_unit = {
        'OCPI': 'ppbv', 'OCPO': 'ppbv', 'PPN': 'ppbv', 'HIO3': 'pptv',
        'O3': 'ppbv', 'PAN': 'ppbv', 'ACET': 'ppbC', 'RIP': 'ppbv',
        'BrNO3': 'pptv', 'Br': 'pptv', 'HBr': 'pptv', 'HAC': 'ppbv',
        'ALD2': 'ppbC', 'HNO3': 'ppbv', 'HNO2': 'ppbv', 'C2H5I': 'pptv',
        'HNO4': 'ppbv', 'OIO': 'pptv', 'MAP': 'ppbv', 'PRPE': 'ppbC',
        'HI': 'pptv', 'CH2I2': 'pptv', 'IONO2': 'pptv', 'NIT': 'ppbv',
        'CH3Br': 'pptv', 'C3H7I': 'pptv', 'C3H8': 'ppbC', 'DMS': 'ppbv',
        'CH2O': 'ppbv', 'CH3IT': 'pptv', 'NO2': 'ppbv', 'NO3': 'ppbv',
        'N2O5': 'ppbv', 'CHBr3': 'pptv', 'DST4': 'ppbv', 'DST3': 'ppbv',
        'DST2': 'ppbv', 'DST1': 'ppbv', 'HOCl': 'ppbv', 'NITs': 'ppbv',
        'RCHO': 'ppbv', 'C2H6': 'ppbC', 'MPN': 'ppbv', 'INO': 'pptv',
        'MP': 'ppbv', 'CH2Br2': 'pptv', 'SALC': 'ppbv', 'NH3': 'ppbv',
        'CH2ICl': 'pptv', 'IEPOX': 'ppbv', 'ClO': 'ppbv', 'NO': 'pptv',
        'SALA': 'ppbv', 'MOBA': 'ppbv', 'R4N2': 'ppbv', 'BrCl': 'pptv',
        'OClO': 'ppbv', 'PMN': 'ppbv', 'CO': 'ppbv', 'CH2IBr': 'pptv',
        'ISOP': 'ppbC', 'BCPO': 'ppbv', 'MVK': 'ppbv', 'BrNO2': 'pptv',
        'IONO': 'pptv', 'Cl2': 'ppbv', 'HOBr': 'pptv', 'PROPNN': 'ppbv',
        'Cl': 'ppbv', 'I2O2': 'pptv', 'I2O3': 'pptv', 'I2O4': 'pptv',
        'I2O5': 'pptv', 'MEK': 'ppbC', 'MMN': 'ppbv', 'ISOPN': 'ppbv',
        'SO4s': 'ppbv', 'I2O': 'pptv', 'ALK4': 'ppbC', 'MSA': 'ppbv',
        'I2': 'pptv', 'Br2': 'pptv', 'IBr': 'pptv', 'MACR': 'ppbv', 'I': 'pptv',
        'AERI': 'pptv', 'HOI': 'pptv', 'BrO': 'pptv', 'NH4': 'ppbv',
        'SO2': 'ppbv', 'SO4': 'ppbv', 'IO': 'pptv', 'H2O2': 'ppbv',
        'BCPI': 'ppbv', 'ICl': 'pptv', 'GLYC': 'ppbv', 'ISALA': 'pptv',
        'ISALC': 'pptv',
        # Extra diagnostics to allow for simplified processing
        'CH3I': 'pptv', 'Iy': 'pptv', 'PSURF': 'hPa', 'OH': 'pptv', 'HO2': 'pptv', \
        'MO2': 'pptv', 'NOy': 'ppbv', 'EOH': 'ppbv', 'CO': 'ppbv', 'CH4': 'ppbv', \
        'TSKIN': 'K', 'GMAO_TEMP': 'K', 'GMAO_VWND': 'm/s',\
        'GMAO_UWND': 'm/s', 'RO2': 'pptv', 'U10M': 'm/s', 'V10M': 'm/s',\
        'PRESS': 'hPa', 'CH2OO': 'pptv', 'Bry': 'ppbv', 'NOx': 'ppbv', 'HOx': 'HOx',
        'VOC': 'ppbC', 'TNO3': 'ppbv', 'GLYX': 'pptv',
        'GMAO_SURF': 'surface area',  # cm2/cm3?
        'GMAO_ABSH': 'frac.',
        'GMAO_PSFC': 'hPa',
        # Extra ClearFlo compounds
        'acetylene': 'pptv', 'propene': 'pptv', 'Napthalene': 'pptv', \
        'Styrene': 'pptv', '1,3-butadiene': 'pptv', '1,2-butadiene': 'pptv', \
        'iso-butene': 'pptv', 'm+p-xylene': 'pptv', '1-butene': 'pptv', \
        't-2 pentene': 'pptv', 'cis-2-butene': 'pptv', '1  pentene': 'pptv', \
        'Trans-2-butene': 'pptv', 'o-xylene': 'pptv',\
        'iso-pentane': 'pptv', 'n-hexane': 'pptv',  \
        'iso-butane': 'pptv', 'Nonane, 2-methyl-': 'pptv', \
        'Butane, 2,2,3-trimethyl-': 'pptv', 'Dodecane': 'pptv', \
        'Pentane, 2,2,4-trimethyl-': 'pptv', '2,3methylpentane': 'pptv', \
        'Nonane': 'pptv', 'cyclopentane': 'pptv', 'n- heptane': 'pptv', \
        'n-butane': 'pptv', 'n-pentane': 'pptv', 'Undecane': 'pptv', \
        'Decane': 'pptv', 'Octane': 'pptv', 'n-octane': 'pptv',\
        # Extra Cly species
        'ClNO2': 'pptv', 'ClNO3': 'pptv', 'HCl': 'pptv', 'ClOO': 'pptv', \
        'Cl2O2': 'pptv', 'CH2Cl2': 'pptv', 'CHCl3': 'pptv', 'CH3Cl': 'pptv', \
        'BrSALA': 'pptv', 'BrSALC': 'pptv', 'Cly': 'pptv', \
        # extra tag "species" for easy of processing
        'PD421': 'molec cm$^{-3}$ s$^{-1}$',
        # add planeflight variabels for ease of processing
        'LON': '$^{\circ}$E', 'LAT': '$^{\circ}$N', 'PRESS': 'hPa',
        # add combined species for easy of processing
        'HOCl+Cl2': 'pptv', 'HOBr+Br2': 'pptv',
        # add derivative species for easy of processing
        'HNO3/NOx': 'pptv', 'HNO3+NIT': 'pptv', 'HNO3+NO3': 'pptv',
        'NIT/NOx': 'pptv', 'HNO3/NIT': 'pptv',
        #
        'Cl-': 'pptv',
    }
    try:
        units = tra_unit[x]
    except KeyError:
        logging.info(
            'provided species/tracer ({}) not in unit dictionary'.format(x))
        sys.exit()

    # Adjust to appropriate scale for pf analysis
    if adjust:
        spec_2_pptv = GC_var('spec_2_pptv')
        spec_2_pptC = GC_var('spec_2_pptC')
        if (x in spec_2_pptv):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'pptv')))
            units = 'pptv'
        if (x in spec_2_pptC):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'pptC')))
            units = 'pptC'

    # Over ride adjustments for globally appro. units
    if global_unit:
        spec_2_ppbv = GC_var('spec_2_ppbv')
        spec_2_ppbC = GC_var('spec_2_ppbC')
        if (x in spec_2_ppbv):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'ppbv')))
            units = 'ppbv'
        if (x in spec_2_ppbC):
            if debug:
                print(('adjusting {} ({}) to {}'.format(x, units, 'ppbC')))
            units = 'ppbC'

    if ClearFlo_unit:
        units2ppbv = ['NO', 'MACR', 'MVK', 'PRPE', 'ALK4', 'ALD2']
        if any([x == i for i in units2ppbv]):
            units = 'ppbv'
        if any([x == i for i in ['PAN', ]]):
            units = 'pptv'
        if any([x == i for i in ['ISOP']]):
            units = 'ppbC'

    if use_pf_species_units:
        TRA_v10_species = [
            'A3O2', 'ATO2', 'B3O2', 'EOH', 'ETO2', 'ETP', 'GLYX', 'HO2', 'IAP', 'INO2', 'INPN', 'ISN1', 'ISNOOA', 'ISNOOB', 'ISNOHOO', 'ISNP', 'KO2', 'MAN2', 'MAO3', 'MAOP', 'MAOPO2', 'MCO3', 'MGLY', 'MO2', 'MRO2', 'MRP', 'OH', 'PO2', 'PP', 'PRN1', 'PRPN', 'R4N1', 'R4O2', 'R4P', 'RA3P', 'RB3P', 'RCO3', 'RIO2', 'ROH', 'RP', 'VRO2', 'VRP', 'LISOPOH', 'ISOPND', 'ISOPNB', 'HC5', 'DIBOO', 'HC5OO', 'DHMOB', 'MOBAOO', 'ISOPNBO2', 'ISOPNDO2', 'ETHLN', 'MACRN', 'MVKN', 'PYAC', 'IEPOXOO', 'ATOOH', 'PMNN', 'MACRNO2', 'PMNO2'
        ]
        if (x in TRA_v10_species):
            units = 'molec/cm3'

    if scale:
        scaleby = get_unit_scaling(units)

    if adjustment:
        if units == 'K':
            units = 'Deg. Celcuis'
            adjustby = -273.15
        else:
            adjustby = 0

    if IUPAC_unit:
        if units == 'ppbv':
            units = 'nmol mol$^{-1}$'
        if units == 'ppbC':
            units = 'nmol (C) mol$^{-1}$'
        if units == 'pptv':
            units = 'pmol mol$^{-1}$'
        if units == 'pptC':
            units = 'pmol (C) mol$^{-1}$'

    if scale and (not adjustment):
        return units, scaleby
    elif (scale and adjustment):
        return units, scaleby, adjustby
    else:
        return units


def diagnosticname_gamap2iris(x):
    """
    Convert ctm.bpch name into NetCDF nomenclature
    """
    d = {
        "IJ-AVG-$": 'IJ_AVG_S',
        "BXHGHT-$": 'BXHEIGHT',
        "PORL-L=$": 'PORL_L_S__',
        'DAO-3D-$': 'DAO_3D_S__',
        'DAO-FLDS': 'DAO_FLDS__',
        'DRYD-FLX': 'DRYD_FLX__',
        'DRYD-VEL': 'DRYD_VEL__',
        'CHEM-L=$': 'CHEM_L_S__',
        'WETDCV-$': 'WETDCV_S__',
        'WETDLS-$': 'WETDLS_S__',
        'WD-LSW-$': 'WD_LSW_S__',
        'WD-LSR-$': 'WD_LSR_S__',
        'UP-FLX-$': 'UP_FLX_S__',
        'NS-FLX-$': 'NS_FLX_S__',
        'EW-FLX-$': 'EW_FLX_S__',
        'TURBMC-$': 'TURBMC_S__',
        'OD-MAP-$': 'OD_MAP_S__',
        #    'WD-FRC-$'
        'MC-FRC-$': 'MC_FRC_S__',
    }
    return d[x]


def get_unit_scaling(units, scaleby=1):
    """
    Get scaling for a given unit string

    Parameters
    ----------
    units (str): units
    scaleby (float): scaling factor for unit
    """
    logging.debug("Getting unit scaling for {units}".format(units=units))
    misc = (
        'K', 'm/s', 'unitless', 'kg', 'm', 'm2', 'kg/m2/s', 'molec/cm2/s',
        'mol/cm3/s',  'kg/s', 'hPa', 'atoms C/cm2/s', 'kg S', 'mb', 'atoms C/cm2/s',
        'molec/cm3', 'v/v', 'cm/s', 's-1', 'molec/m3', 'W/m2', 'unitless',
    )
    # parts per trillion
    if any([(units == i) for i in ('pptv', 'pptC', 'ppt')]):
        scaleby = 1E12
    # parts per billion
    elif any([(units == i) for i in ('ppbv', 'ppbC', 'ppb')]):
        scaleby = 1E9
    elif any([units == i for i in misc]):
        scaleby = 1
        logging.debug('WARNING: {} is not in unit lists: '.format(units))
    return scaleby


class species:
    """
    Class for holding infomation about chemical speices.

    NOTES:
     -  the class is build from a csv file (species.csv) in the git Repository.
    """

    def __init__(self, name):
        self.name = name
        self.help = ("""This is a class to get information on species from a local CSV folder
   It might contain the following information:
   self.RMM    = The Mean Mass of the species.
   self.latex      = The latex name of the species.
   self.smiles   = The smiles string of the species.
   self.InChI    = The InChI string of the species.
   """)
        species_filename = os.path.dirname(__file__) + "/Species.csv"

        try:
            species_file = open(species_filename, 'r')
        except IOError:
            print("Error: Species.csv does not appear to exist.")
        species_csv = csv.reader(species_file)

        if (name == 'OH'):
            self.group = 'CHEM-L=$'
        else:
            self.group = 'IJ-AVG-$'

        for row in species_csv:
            try:
                if (str(self.name) == row[0].strip()):
                    self.formula = row[1]
                    self.InChI = row[2]
                    self.smiles = row[3]
                    self.RMM = float(row[4])
                    self.Latex = row[5]
            except NameError:
                print("Species not found in CSV file")

        # TODO - Add in function to return stiochmetery using smile str
        # (e.g. how many carbons in species )


def get_ctm_nc_var(variable):
    """
    Get number variable for diagnostic family where NetCDF import
    from *.dat file has failed. This function returns a category name + a
    number value to refer to diagnostic ording in NetCDF.

    Parameters
    ----------
    variable (str): NetCDF variable within number suffix

    Returns
    -------
    variable (str): NetCDF variable in GEOS-Chem output

    Notes
    -----
     - This is only called as a back up, and should only be used for test
    ouput and not for production runs

    """
    d = {
        'DAO_3D_S__CMFMC': 'DAO_3D_S___4',
        'DAO_3D_S__DTRAIN': 'DAO_3D_S___3',
        'DAO_3D_S__SPHU': 'DAO_3D_S___2',
        'DAO_3D_S__TMPU': 'DAO_3D_S___1',
        'DAO_3D_S__UWND': 'DAO_3D_S__',
        'DAO_3D_S__VWND': 'DAO_3D_S___0'
    }
    return d[variable]


def constants(input_x, rtn_dict=False):
    """
    Dictionary storing commonly used constants

    Parameters
    ----------
    input_x (str): name of contant of interest
    rtn_dict (boolean): retrun complete dictionary instead of single value

    Returns
    -------
    value of constant (float) or dictionary on constants and values (dict)

    Notes
    -----
    """
    con_dict = {
        # Relative atomic mass of air (Just considering N2+O2)
        'RMM_air': (.78*(2.*14.)+.22*(2.*16.)),
        # Avogadro constant (Mol^-1)
        'AVG': 6.0221413E23,
        # Dobson unit - (molecules per meter squared)
        'mol2DU': 2.69E20,
        # Specific gas constant for dry air (J/(kg·K))
        'Rdry': 287.058,
    }
    if rtn_dict:
        return con_dict
    else:
        return con_dict[input_x]


# -------------- Dynamic processing of p/l
#
# NOTE - below functions for automated processing/parsing of smvgear
# mechanisms for tagging. It is redundant and far more coherent version
# for processing KPP mechanisms and tags is included in funcs4GEOS.py


def rxn_dict_from_smvlog(wd, PHOTOPROCESS=None, ver='1.7',
                         LaTeX=False, debug=False):
    """
    Build a dictionary reaction of reaction details from smv.log.
    This can be used as an external call to analyse other prod/loss
    reactions through smvgear

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    debug (boolean): legacy debug option, replaced by python logging
    PHOTOPROCESS (int): smvgear index of 1st photochemical reaction
    LaTeX (boolean): convert species to LaTeX style formatting
    ver (str): The GEOS-Chem halogen version that is being used

    Returns
    -------
    (dict) dictionary of active reactions in smvgear output

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """

    if isinstance(PHOTOPROCESS, type(None)):
        PHOTOPROCESS = {
            '1.6': 457, '1.6.2': 452, '1.6.3': 461, '1.7': 467, '2.0': 555,
            '3.0': 547,
            # placeholder for v4.0
            '4.0': 547
        }[ver]

    fn = 'smv2.log'
    if debug:
        print((wd+'/'+fn))
    file_ = open(wd+'/'+fn, 'r')
    readrxn = False
    for row in file_:
        row = row.split()
        if 'NMBR' in row:
            readrxn = True
        if len(row) < 1:
            readrxn = False
        if readrxn:
            try:
                rxns.append(row)
            except:
                rxns = [row]

    # -- remove 'NMBR'
    rxns = [i for i in rxns if ('NMBR' not in i)]
    n = [int(rxn[0]) for rxn in rxns]
    rxns = [rxn[1:] for rxn in rxns]
    rdict = dict(list(zip(n, rxns)))

    # --- Process to Latex
    if LaTeX:
        for rxn in sorted(rdict.keys()):

            # -- Use Latex formatting?
            if rxn > PHOTOPROCESS-1:
                #                xarstr = r' $\xrightarrow{hv}$ '
                xarstr = r' + hv $\rightarrow$ '
            else:
                xarstr = r' + M $\rightarrow$ '
            # --- get all print on a per tag basis the coe, rxn str
            try:
                rxn_str = ''.join(rdict[rxn][4:])
                if LaTeX:
                    rxn_str = rxn_str.replace('++=', xarstr)
                    rxn_str = rxn_str.replace('+', ' + ')
                    rxn_str = rxn_str.replace('+ =', r' $\rightarrow$ ')
                else:
                    pass
                if debug:
                    print(rxn_str)
                try:
                    rxn_strs += [rxn_str]
                    rxns += [rxn]
                except:
                    rxn_strs = [rxn_str]
                    rxns = [rxn]
            except:
                print(('!'*100, 'ERROR HERE: >{}<  >{}<'.format(rxn, rxn_str)))
        rdict = dict(list(zip(rxns, rxn_strs)))
    return rdict


def rxns_in_pl(wd, spec='LOX', debug=False):
    """
    Extract reactions tracked by p/l family in smvgear

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    debug (boolean): legacy debug option, replaced by python logging
    spec (str): prod-loss variable name (from input.geos)

    Returns
    -------
    (list) reaction in production/loss family

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """

    fn = 'smv2.log'
    file_ = open(wd+'/'+fn, 'r')
    if debug:
        print(file_)
    readrxn = False
    # required strings in file line
    conditions = 'Family', 'coefficient', 'rxns', spec
    for row in file_:
        row = row.split()
        if debug:
            print((row, spec, all([i in row for i in conditions])))
        if all([i in row for i in conditions]):
            readrxn = True
        if (len(row) < 1) or ('REACTANTS:' in row):
            readrxn = False
        if readrxn:
            try:
                rxns.append(row)
            except:
                rxns = [row]

    # -- Check that rxns ahave been found?
    if len(rxns) < 1:
        print(('ERROR: No rxns. found for >{}<, correct family?'.format(spec)))
        sys.exit(0)

    # -- remove 'Family'
    rxns = [i for i in rxns if ('Family' not in i)]
    if debug:
        print(('number (len of list) of reacitons: ', len(rxns)))
    n = [int(rxn[1]) for rxn in rxns]
    rxns = [rxn[2:] for rxn in rxns]

    rdict = dict(list(zip(n, rxns)))
    return rdict


def rxn4pl(pls, wd='example/example', rdict=None, reduce_size=True,
           ver='1.7', debug=False):
    """
    Get information on reaction in smvgear from a provide reaction tag

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    ver (str): The GEOS-Chem halogen version that is being used
    debug (boolean): legacy debug option, replaced by python logging
    spec (str): prod-loss variable name (from input.geos)
    rdict (dict): dictionary of prod-loss reaction (made by rxn_dict_from_smvlog)

    Returns
    -------
    (list) reaction in production/loss family

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """

    # ---  Get Dict of reaction detail
    if debug:
        print('rxn4pl called')
    if isinstance(rdict, type(None)):
        #   Get Dict of all reactions, Keys = #s
        rdict = rxn_dict_from_smvlog(wd, ver=ver)

    if debug:
        for i in list(rdict.keys()):
            if any([(s_ in ''.join(rdict[i])) for s_ in pls]):
                print((i, 'yes'))

    # --- Indices for
    # reduce dict size
    if reduce_size:
        keys = [i for i in list(rdict.keys()) if
                any([(s_ in ''.join(rdict[i])) for s_ in pls])]

        # re-make dictionary
        rdict = dict(list(zip(keys, [rdict[i] for i in keys])))

    # loop via pl
    keys = np.array([[pl, [i for i in list(rdict.keys())
                           if any([(pl in ''.join(rdict[i]))])][0]] for pl in pls])

    # --- Return as reactions referenced by tag
    return dict(list(zip(keys[:, 0],  [rdict[int(i)] for i in keys[:, 1]])))


def get_indicies_4_fam(tags, fam=False, IO_BrOx2=False, rtnspecs=False,
                       NOy_as_HOx=True, Include_Chlorine=False, debug=False):
    """
    Return indicies (in list form) for in a given family

    Parameters
    ----------
    tags (list): list of tags(str) from globchem.dat
    fam (boolean): also return which family the tag belongs to
    IO_BrOx2 (boolean): include an addtion tracer for XO+XO reactions?
    Include_Chlorine (boolean): include an extra tracer for ClO+XO
    NOy_as_HOx (Boolean): include NOy losses in HOx family.
    debug (boolean): legacy debug option, replaced by python logging
    rtnspecs(boolean): return tags as part of function output

    Returns
    -------
    (list) or indices for globche.dat/prod and loss tags

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """
    # assign family
#    famsn = [ 'Photolysis','HOx','NOy' ,'Bromine', 'Iodine' ]
    if Include_Chlorine:
        famsn = ['Photolysis', 'HOx', 'Chlorine', 'Bromine', 'Iodine']
    else:
        famsn = ['Photolysis', 'HOx', 'Bromine', 'Iodine']
    fams = []
    for tag in tags:
        fams.append(get_tag_fam(tag))
    # if rm NOy family (treat as NOx)
    if NOy_as_HOx:
        fams = [x if (x != 'NOy') else 'HOx' for x in fams]

    # Create dictionary from tags and fam assignment
    fd = dict(list(zip(tags, fams)))

    # Select tags with assigned family in list ("famsn")
    ll = []
    [ll.append([]) for i in famsn]
    for n, tag in enumerate(tags):
        for fn in range(len(famsn)):
            if fd[tag] == famsn[fn]:
                ll[fn].append(n)

    # Consider Ox loss for
    if fam:
        #    if False: # Kludge for test.
        # Kludge - to allow for counting Ox loss via XO +XO 50/50 between fams,
        # ( add extra loss tag. )
        if IO_BrOx2:
            #        if False:
            # Add extra tag for reaction ( IO + BrO )
            ll[famsn.index('Bromine')].append(max([max(i) for i in ll])+1)
            fams = fams + ['Bromine']
            tags = tags + ['LO3_24']
        if Include_Chlorine:
            #        if False:
            # Add extra tag for reaction ( ClO + BrO )
            ll[famsn.index('Chlorine')].append(max([max(i) for i in ll])+1)
            fams = fams + ['Chlorine']
            tags = tags + ['LO3_82']
            # Add extra tag for reaction  ( ClO + IO )
            ll[famsn.index('Chlorine')].append(max([max(i) for i in ll])+1)
            fams = fams + ['Chlorine']
            tags = tags + ['LO3_87']

        if rtnspecs:
            return ll, fams, tags
        else:
            return ll, fams
    else:
        return ll


def get_p_l_tags(rxns, debug=False):
    """
    Get p/l tags for a given smvgear reaction

    Parameters
    ----------
    rxns (list): list of rxn numbers(int) from smvgear
    debug (boolean): legacy debug option, replaced by python logging

    Returns
    -------
    (list) of tags for globchem.dat/prod and loss tags

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.

    """

    # (PD??, RD??, LO3_??, PO3_??, LR??)
    prefixs = 'PD', 'RD', 'PO3', 'LO3', 'LR'

    for rxn in rxns:
        if debug:
            print([i for i in rxn if any([(x in i) for x in prefixs])])
        tags = [i for i in rxn if any([(x in i) for x in prefixs])]

        try:
            tagsl.append(tags)
        except:
            tagsl = [tags]

    return tagsl


def p_l_species_input_geos(wd, ver='1.7', rm_multiple_tagged_rxs=False, debug=False):
    """
    Extract prod/loss species (input.geos) and reaction tags (globchem.dat)

    Parameters
    ----------
    wd (str): Specify the wd to get the results from a run.
    debug (boolean): legacy debug option, replaced by python logging
    ver (str): The GEOS-Chem halogen version that is being used
    rm_multiple_tagged_rxs(boolean): only return one tag per rxn.

    Returns
    -------
    (list) globchem.dat tags and prod/loss ("PD") vars from input.geos

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """
    # find and open input.geos file
    fn = glob.glob(wd+'/*input.geos*')[0]
    if any([(i in fn) for i in ('~', '#')]):
        print(('Trying next "input.geos" file - as FAIL for :', fn))
        fn = glob.glob(wd+'/*input.geos*')[1]

    if debug:
        print(('p_l_species_input_geos called using : ', wd, fn))
    file_ = open(fn, 'r')

    # Read in just the prod loss section
    strs_in_1st_line = 'Number', 'of', 'P/L', 'families'
    section_line_divider = '------------------------+----------' + \
        '--------------------------------------------'
    readrxn = False
    for row in file_:
        row = row.split()

        # once at prod/loss section, start added to list
        if all([i in row for i in strs_in_1st_line]):
            readrxn = True

        # if not at end of prod/loss section, add to list
        if section_line_divider in row:
            readrxn = False
        if readrxn:
            try:
                rxns.append(row)
            except:
                rxns = [row]

    # -- Only consider 'Family' ( no headers e.g. 'families' )
    rxns = [i for i in rxns if ('families' not in i)]
    rxns = [[i.replace(':', '') for i in r] for r in rxns]

    # Kludge, adjust for extra space 12-99
    # ( This is no longer required for 1.7 + )
    if ver == '1.6':
        [i.pop(0) for i in rxns if ('th' not in i[0])]

    # Extract just PD (input.geos) and vars (globchem.dat vars )
    PD = [rxn[4] for rxn in rxns]
    vars = [rxn[5:] for rxn in rxns]
    if debug:
        print((rxns, PD, vars, ver))

    # remove p/l with muliple values ( start from 12th input) - Kludge?
    if rm_multiple_tagged_rxs:
        PD, vars = [i[11:] for i in (PD, vars)]
        vars = [i[0] for i in vars]

    return PD, vars


def tags_from_smvlog(wd):  # , spec='LOX' ):
    """
    Get all active p/l tags in smvgear ( from smv2.log )

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """
    fn = 'smv2.log'
    file_ = open(wd+'/'+fn, 'r')
    readrxn = False
    for row in file_:
        row = row.split()
        if all([(i in row) for i in ['NBR', 'NAME', 'MW', 'BKGAS(VMRAT)']]):
            readrxn = True
        if len(row) < 1:
            readrxn = False
        if readrxn:
            try:
                rxns.append(row)
            except:
                rxns = [row]

    # -- remove 'NMBR'
    rxns = [i for i in rxns if ('NBR' not in i)]
    rxns = [rxn[1] for rxn in rxns]

    # --- only consider tags
    return [i for i in rxns if any([x in i
                                    for x in ('PD', 'RD', 'PO3', 'LO3', 'LR')])]


def PDs_from_smvlog(wd, spec='LOX'):
    """
    Get all active PDs tags in smvgear ( from smv2.log )

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """
    fn = 'smv2.log'
    file_ = open(wd+'/'+fn, 'r')
    readrxn = False
    leniency = 0
    entries_in_title = ['Families', 'for', 'prod', 'or', 'loss', 'output:']
    for row in file_:
        row = row.split()
        if all([(i in row) for i in entries_in_title]):
            readrxn = True
            leniency = 1
        if len(row) < 1:
            if leniency < 0:
                readrxn = False
            leniency -= 1
        if readrxn:
            try:
                rxns.append(row)
            except:
                rxns = [row]

    # -- remove 'NMBR'
    exceptions = [
        'SPECIES', '===============================================================================', 'Families']
    rxns = [i for i in rxns if all([(ii not in i) for ii in exceptions])]
    rxns = [j for k in rxns for j in k]
    return rxns


def rxns4tag(tag, rdict=None, ver='1.7', wd=None):
    """
    Get a list of all reactions with a given p/l tag

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """
    # --- get reaction dictionary
    if isinstance(rdict, type(None)):
        rdict = rxn_dict_from_smvlog(wd, ver=ver)

    # --- Caveats -
    # to adapt for long line errors in fortran written output
    errs = ['LO3_36']  # + ['LO3_87']
    cerrs = ['RD95']  # + ['LR48']
    # To account for reaction where not all channels result in Ox loss
    errs += ['RD48']
    cerrs += ['LO3_87']
    if any([(tag == i) for i in errs]):
        tag = cerrs[errs.index(tag)]

    # -- loop reactions, if tag in reaction return reaction
    rxns = []
    for n, rxn in enumerate(rdict.values()):

        expanded_rxn_str = [i.split('+') for i in rxn]
        expanded_rxn_str = [
            item for sublist in expanded_rxn_str for item in sublist]

        # ( Issue) Why endswith? Restore to use if contains any tag
#        if any( [ (i.endswith(tag) ) for i in rxn]):
        # This is because otherwise 'LR10' would be read as 'LR100'
#        if any( [tag in i for i in rxn]): # <= This will lead to false +ve
        # However, fortran print statment err for (  LO3_87 )
        if any([i.endswith(tag) for i in expanded_rxn_str]):
            rxns.append([list(rdict.keys())[n]] + rxn)

    return rxns


def get_tag_details(wd, tag=None, PDs=None,  rdict=None, PHOTOPROCESS=None, ver='1.7',
                    LaTeX=False, print_details=False, debug=False):
    """
    Retriveve prod/loss tag details from smv.log
        ( rxn number + reaction description)

    Notes
    -----
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """

    # what is the number of the first photolysis reaction?
    if isinstance(PHOTOPROCESS, type(None)):
        PHOTOPROCESS = {
            '1.6': 457,  '1.6.2': 452, '1.7': 467, '2.0': 555, '3.0': 547, '4.0': 547
        }[ver]

    # ---  get all reactions tags are active in smv.log
    if isinstance(rdict, type(None)):
        rdict = rxn_dict_from_smvlog(wd, ver=ver)
    trxns = rxns4tag(tag, wd=wd, rdict=rdict)

    # --- get all print on a per tag basis the coe, rxn str
    try:
        rxn_str = ''.join(trxns[0][5:9])

        # -- Use Latex formatting?
#        if LaTeX:
#
        # setup latex arrows and replace existing arrows
#            if trxns[0][0] > PHOTOPROCESS-1:
#                xarstr = r' $\xrightarrow{hv}$ '
#            else:
#                xarstr = r' $\xrightarrow{M}$ '
#            rxn_str = rxn_str.replace('++=', xarstr).replace('+', ' + ')
#            rxn_str = rxn_str.replace('+ =', r' $\rightarrow$ ' )

#        else:
#            pass
        if debug:
            print(rxn_str)
        dets = [tag, trxns[0][0], rxn_str]
    except:
        print(('!'*100, 'ERROR HERE: >{}< >{}<'.format(tag, trxns)))
    if print_details:
        print(dets)
    # --- return a dictionary of all active tagged reactions details by tag : PD, number, rxn str, coeeffiecn
    else:
        return dets


def get_rxn_Coe(wd, num, tag, nums=None, rxns=None, tags=None, Coe=None, spec='LOX',
                ver='1.6', debug=False):
    """
    Retrieve given reaction coefficient for smvgear (from smv2.log)

    Notes
    -----
     - This is no longer the case. However, previously if using dev.
    Iy scheme, then the listed values from fuction Ox_in_species() will be used.
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """

    # --- get dictionaries for reactions within
    if all([(i == None) for i in (nums, rxns, tags, Coe)]):
        nums, rxns, tags, Coe = prod_loss_4_spec(wd,  spec, all_clean=True,
                                                 ver=ver)
    if debug:
        print((nums, Coe))

    # Pull reaction coefficient  from dictionary
    Coe_dict = dict(list(zip(nums, Coe)))
    Coe = float(Coe_dict[num])
    # Consider all change positive - Kludge
    # ( This is due to the assignment approach, where P=prod, L=loss )
    if ('P' not in tag):
        Coe = Coe*-1.0

    # --- over write Ox in species with prod_mod_tms values
    # ( This is only used for the Ox tracers from dev. Iy simulation )
    # This has been removed to avoid possibility of double up.
#    try:
#        Coe = Ox_in_species(tag, rxns=True)
#        if debug:
#            print 'using values from Ox_in_species'
#    except:
#        if debug:
#            print 'using values from smv.log @: {}'.format(wd), 'for ', tag, Coe
    return Coe


def get_pldict_reactants(pl_dict=None, only_rtn_tracers=True, rm_OH=True, rm_Cl=True,
                         tags=None, debug=False):
    """
    Get reactant from smv2.log dictionary

    Notes
    -----
     - some reactants are not tracers ( see list: non_TRAs )
    ( to remove these set only_rtn_tracers=True )
     - to remove OH from reactant list set rm_OH=True
     - This function is useful, but update to GEOS-Chem flexchem ( in >v11)
    will make it redundent and therefore this is not being maintained.
    """
#    non_TRAs = ['CH4', '', 'ETHLN', 'ISOPND', 'E', 'M', 'HCO', 'MVKN', 'ACTA']

    # Get reaction strings
    if isinstance(tags, type(None)):
        tags = list(pl_dict.keys())
    strs = [pl_dict[i][1] for i in tags]
    if debug:
        print(('rxn strs: ',  strs, len(strs)))
    # remove arrows from reactions
    strs = [i.replace('+M=', '+=').replace('+O2=', '+=').replace('+N2=', '+=')
            for i in strs]
    if debug:
        print((strs, len(strs)))
    # select reactants
    strs = [i.split('+=')[0] for i in strs]
    if debug:
        print((strs, len(strs)))
    if rm_OH:     # remove OH from reaction strings
        strs = [i.replace('+OH', '+') for i in strs]
        for n, str in enumerate(strs):
            if str.startswith('OH+'):
                strs[n] = str.replace('OH', '+')
    if rm_Cl:     # remove Cl from reaction strings
        strs = [i.replace('+Cl', '+') for i in strs]
        for n, str in enumerate(strs):
            if str.startswith('Cl+'):
                strs[n] = str.replace('Cl+', '+')

    # remove "+" punctuation
    strs = [i.replace('+', '').strip() for i in strs]
    if debug:
        print((strs, len(strs)))

    return strs


def PLO3_to_PD(PL, fp=True, wd=None, ver='1.6', res='4x5', verbose=False, debug=False):
    """
    Converts globchem.dat tracer to PD/LD from prod/loss diag in input.geos

    Notes
    -----
     - 'fp' option is now obselete.
     - UPDATED NEEDED: MORE DETAILED DESCRIPT.
    """

    if verbose:
        print(('PLO3_to_PD called for wd = ', wd))

    versions = [
        '1.3', '1.4', '1.5', '1.6', '1.6.1', '1.6.2', '1.6.3', '1.7', '2.0', '3.0', '4.0']
    if any([(ver == i) for i in versions]):

        if isinstance(wd, type(None)):
            print('WARNING: Using MUTD wd')
            wd = MUTD_runs(ver=ver, res=res, debug=debug)[0]

        # Get list of assigned PDs for vars
        PDs, vars = p_l_species_input_geos(wd, ver=ver,
                                           rm_multiple_tagged_rxs=True, debug=debug)

        # Add other (non 'PD') vars for ease of processing
        non_PDs = [
            'PIOx', 'iLOX', 'LIOx', 'iPOX', 'POX', 'LOX', 'LOx', 'L_Iy', 'LOH',
            'LCl', 'POH', 'PCl', 'P_Iy', 'L_Bry', 'P_Bry', 'L_Cly', 'P_Cly',
            'LSBrA', 'LSBrC', 'PSBrA', 'PSBrC'
        ]
        vars += non_PDs
        PDs += non_PDs

        if debug:
            print((vars, PDs))

        return dict(list(zip(vars, PDs)))[PL]
    else:
        print('update programme - manual PLdict now obsolete. ')


def get_pl_dict(wd, spec='LOX', rmx2=False, ver='1.7', rm_redundent_ClBrI_tags=False,
                debug=False):
    """
    Get reaction IDs for each rxn. in spec (p/l, e.g. LOX). This is the driver for
    the prod/loss programmes

    Notes
    -----
     - UPDATED NEEDED: MORE DETAILED DESCRIPT.
    """
    if debug:
        print(('get_pl_dict called for ', ver, spec, wd))

    # Extract details on reactio in p/l family
    nums, rxns, tags, Coe = prod_loss_4_spec(wd,  spec, all_clean=True,
                                             ver=ver, debug=debug)

    # Make a dictionary of coeffiecnts of reaction
    Coe_dict = dict(list(zip(nums, Coe)))

    # unpack for mulutple tags of same reactions, then get details
    unpacked_tags = [j for k in tags for j in k]

    # Kludge - remove 'PO3_10' temporarily from dictionary as these contain
    # partial tag names (  Fortran print statment cut off )
    unpacked_tags = [i for i in unpacked_tags if ('PO3_10' not in i)]

    if debug:
        print(unpacked_tags)

    details = [get_tag_details(wd, tag, ver=ver) for tag in unpacked_tags]

    # Kludge - 1 rxn missing from POx tracking? - 999  + "'ISOPND+OH', '+', '=1.0ISOPND'"
    [details.pop(n) for n, i in enumerate(details) if i[1] == 364]
    ind = [n for n, i in enumerate(nums) if i == 354]

    # Get coefficients for change in reaction family
    # NOTE: This does not exclude adjustment for non unity globchem.dat tags
    Coes = [get_rxn_Coe(wd, d[1], unpacked_tags[n], nums=nums,
                        rxns=rxns, tags=tags, Coe=Coe, spec=spec, debug=debug)
            for n, d in enumerate(details)]

    # Remove double ups, which are present due to Loss (LO3_??) and
    # rate tagging (RD??) originally performed separately
    if rmx2:
        d = [
            # I2O2 => AERI (LOSS) ( either RD62 or LO3_38 fine. )
            ['RD62', 'LO3_38'],
            # IONO2 ( use LO3_30 or RD59, LR42, and LR43 )
            ['RD59', 'LO3_30'],  \
            # HOI +hv =>  ( either RD65 or LO3_34 fine. )
            ['RD65', 'LO3_34'],  \
            # I2O4 => AERI (LOSS) ( either RD93 or LO3_55 fine. )
            ['RD93', 'LO3_55'],
            # IONO => IX/AERI (LOSS) ( use LO3_39 ( RD92 is not equiv) )
            ['RD92', 'LO3_39'], \
            # I2O3 => AERI (LOSS) ( either RD95 or LO3_36 fine. )
            ['RD95', 'LO3_36'],   \
            # OIO +hv =>  => AERI (LOSS) ( either RD67 or LO3_35 fine. )
            ['RD67', 'LO3_35'],
            # HOBr + hv=>  ( either LR25 or LO3_84 fine. )
            ['LR25', 'LO3_84']
        ]
        # Use Justin's 'LR??'/Johan's JTO1 tags in preference to 'LO3??' tags
        # This is an Kludge that only is necessary for "NOHAL" runs
        if rm_redundent_ClBrI_tags:
            d += [
                ['LR6', 'LO3_73'], ['LR5',  'LO3_73'], ['LR10', 'LO3_74'],
                ['LR25', 'LO3_84'], ['LO3_82', 'LO3_82'], ['LO3_76', 'LO3_76'],
                ['LO3_75', 'LO3_75']
            ]
            # make sure 'LO3_73' is dropped regardless of index selection
            d += [['LO3_73', 'LO3_73'],  ['LO3_73', 'LO3_73'],
                  ['LO3_74', 'LO3_74'], ['LO3_84', 'LO3_84']
                  ]

        # Either one can be removed as currently two will be present and both #
        # are  equally weighted by use of the Ox_in_species diagnostic ...
        # ( However, this  only if all are equiv. )
        if rm_redundent_ClBrI_tags:
            # Drop the 2nd element in "d" list #
            d = [i[1] for i in d]
        else:
            # Drop the 1st element in "d" list # <= MUST USE for Halogen sims.
            d = [i[0] for i in d]

        ind = [n for n, i in enumerate(details) if any([i[0] == ii
                                                        for ii in d])]
        # make sure indices ('ind') are only removed once
        ind = list(sorted(set(ind)))

        if debug:
            print((d, ind, [len(i) for i in (details, Coes)],
                   [[i[0] for i in details][ii] for ii in ind][::-1]))
        # If cases have been found, remove these
        if len(ind) > 0:
            [l.pop(i) for i in ind[::-1] for l in (details, Coes)]
        if debug:
            print([len(i) for i in (details, Coes)])

    # return a dictionary indexed by p/l tracer, with rxn #,
    # reaction str and Coe of rxn.
    return dict(list(zip([i[0] for i in details], [i[1:] + [Coes[n]]
                                                   for n, i in enumerate(details)])))


def prod_loss_4_spec(wd, fam, all_clean=True, ver='1.7', debug=False):
    """
    Retrieve reaction numbers for family of tags

    Notes
    -----
     - coefficecents ("Coe") returned are for the family (e.g LOX)
    within a reaciton. ( aka not for the tag )
     -  UPDATED NEEDED: MORE DETAILED DESCRIPT.
    """

    # ---  Get Dict of all reactions, Keys = #s
    rdict = rxn_dict_from_smvlog(wd, ver=ver)

    # ---  Get reaction # tracked by p/l diag for spec and coefficient.
    rxns = rxns_in_pl(wd, fam)
    nums = list(rxns.keys())
    Coe = [rxn[-1] for rxn in list(rxns.values())]

    # --- get all details from full reaction dictionary
    rxns = [rdict[i] for i in nums]

    # --- get tags for tracked reactions, state where reactions are un tracked
    tags = get_p_l_tags(rxns)

    # --- cleaned tags
    if all_clean:
        tags = [[re.sub('\+\d.\d', '',  i) for i in u] for u in tags]
        tags = [[re.sub('\=\d.\d', '',  i) for i in u] for u in tags]

        # -- remove erroneous read/  Kludge on val
        # ---  Fortran write error leads to combination of species at the
        #  end of long line of a chemical reaction in globchem.dat
        if debug:
            print([i[:3] for i in (nums, rxns, tags, Coe)])
            print([len(i) for i in (nums, rxns, tags, Coe)])

        # LO3_36RD95 is present twice as this reaction is present 2 times in the code
        # update 16 01 11: LO3_36RD95 is now present x3 in version 3.0
        # ( due split uptake in iodine to aerosol )
        errs = [
            'LO3_36RD95', 'LO3_36RD95', 'LO3_36RD95',
            'ISOPNDPO3_50',
            'ISOPNDLR40',
            'LO3_30LR42',
            'LO3_30LR43',
            'LO3_39LR46',
            'LO3_39LR47',
            'LO3_87LR48', 'LO3_87LR48',
            'LISOPOLR86',
            'LO3_50LR113',
            'LO3_50LR114',
            # final v3.0 runs
            'LO3_65LR126'
        ]
        cerrs = [
            ['LO3_36', 'RD95'], ['LO3_36', 'RD95'], ['LO3_36', 'RD95'],
            ['PO3_50'],
            ['LR40'],
            ['LO3_30', 'LR42'],
            ['LO3_30', 'LR43'],
            ['LO3_39', 'LR46'],
            ['LO3_39', 'LR47'],
            ['LO3_87'], ['LO3_87'],
            ['LR86'], \
            #        ['LO3_50', 'LR113' ], \
            #        ['LO3_50', 'LR114' ]
            # revserse LR tags also ( LO3_50 now redundant? ) - NO
            ['LR113', 'LO3_50'], \
            ['LR114', 'LO3_50'],
            #        ['LR113'],
            #        ['LR114'],
            # final v3.0 runs
            ['LR126', 'LO3_65'],

        ]
#        errs = ['LO3_36RD95' , 'ISOPNDPO3_50', 'ISOPNDLR40']
#        cerrs = [ ['RD95'], ['PO3_50'], ['LR40'] ]
        for n, e in enumerate(errs):
            try:
                # Get index of erroneous rxn tag
                ind = [nn for nn, i in enumerate(tags) if
                       any([(e in ii) for ii in i])][0]
                # Extract vars for a given index
                vars = [i[ind] for i in (nums, rxns, tags, Coe)]
                if debug:
                    print((3, [i[-1] for i in (nums, rxns, tags, Coe)], vars,
                           [len(i) for i in (nums, rxns, tags, Coe)]))
                # remove index ( "ind" ) value from nums, rxns, tags, and Coe
                [i.pop(ind) for i in (nums, rxns, tags, Coe)]

                # Add the cerrs values on the end
                if debug:
                    print((4, [i[-1] for i in (nums, rxns, tags, Coe)],
                           [len(i) for i in (nums, rxns, tags, Coe)]))
                nums += [vars[0]]
                rxns += [vars[1]]
                tags += [cerrs[n]]
                Coe += [vars[-1]]

                if debug:
                    print((6, [i[-1] for i in (nums, rxns, tags, Coe)],
                           [len(i) for i in (nums, rxns, tags, Coe)]))
                    print(('->'*30,  'SUCCESS >{}<  >{}<'.format(n, e)))
            except:
                print(('>'*50, 'FAIL (NOT REPLACED) >{}< >{}<'.format(n, e)))

    # KLUDGE! - rm empty list values of ones that contain errs
#    ind = [ n for n,i in enumerate(tags) if ( (len(i)==0) or (i[0] in errs) ) ]
#    [ [ l.pop(i) for i in sorted(ind)[::-1] ] for  l in nums, rxns, tags, Coe ]
    if debug:
        print(tags)

#    print '1'*300, tags

    return nums, rxns, tags, Coe


def latex_spec_name(input_x, debug=False):
    """
    Formatted (Latex) strings for species and analysis names

    Notes
    -----
    REDUNDENT: now using class structure ( see species instance )
    """
    spec_dict = {
        'OIO': 'OIO', 'C3H7I': 'C$_{3}$H$_{7}$I', 'IO': 'IO', 'I': 'I',
        'I2': 'I$_{2}$', 'CH2ICl': 'CH$_{2}$ICl', 'HOI': 'HOI',
        'CH2IBr': 'CH$_{2}$IBr', 'C2H5I': 'C$_{2}$H$_{5}$I',
        'CH2I2': 'CH$_{2}$I$_{2}$', 'CH3IT': 'CH$_{3}$I',
        'IONO': 'INO$_{2}$', 'HIO3': 'HIO$_{3}$', 'ICl': 'ICl',
        'I2O3': 'I$_{2}$O$_{3}$', 'I2O4': 'I$_{2}$O$_{4}$',
        'I2O5': 'I$_{2}$O$_{5}$', 'INO': 'INO', 'I2O': 'I$_{2}$O',
        'IBr': 'IBr', 'I2O2': 'I$_{2}$O$_{2}$', 'IONO2': 'INO$_{3}$', 'HI': 'HI',
        'BrO': 'BrO', 'Br': 'Br', 'HOBr': 'HOBr', 'Br2': 'Br$_{2}$',
        'CH3Br': 'CH$_{3}$Br', 'CH2Br2': 'CH$_{2}$Br$_{2}$',
        'CHBr3': 'CHBr$_{3}$', 'O3': 'O$_{3}$', 'CO': 'CO', 'DMS': 'DMS',
        'NO': 'NO', 'NO2': 'NO$_{2}$',
        'NO3': 'NO$_{3}$', 'HNO3': 'HNO$_{3}$', 'HNO4': 'HNO$_{4}$',
        'PAN': 'PAN', 'HNO2': 'HONO', 'N2O5': 'N$_{2}$O$_{5}$',
        'ALK4': '$\geq$C4 alkanes', 'ISOP': 'Isoprene', 'H2O2': 'H$_{2}$O$_{2}$',
        'ACET': 'CH$_{3}$C(O)CH$_{3}$', 'MEK': '>C3 ketones',
        'RCHO': 'CH$_{3}$CH$_{2}$CHO',
        'MVK': 'CH$_{2}$=CHC(O)CH$_{3}$', 'MACR': 'Methacrolein',
        'PMN': 'PMN', 'PPN': 'PPN',
        'R4N2': '$\geq$C4 alkylnitrates', 'PRPE': '$\geq$C3 alkenes',
        'C3H8': 'C$_{3}$H$_{8}$', 'CH2O': 'CH$_{2}$O',
        'C2H6': 'C$_{2}$H$_{6}$', 'MP': 'CH$_{3}$OOH', 'SO2': 'SO$_{2}$',
        'SO4': 'SO${_4}{^{2-}}$', 'SO4s': 'SO${_4}{^{2-}}$ on SSA',
        'MSA': 'CH$_{4}$SO$_{3}$', 'NH3': 'NH$_{3}$', 'NH4': 'NH${_4}{^+}$',
        'NIT': 'NO${_3}{^-}$', 'NITs': 'NO${_3}{^-}$ on SSA', 'BCPI': 'BCPI',
        'OCPI': 'OCPI', 'BCPO': 'BCPO', 'OCPO': 'OCPO', 'DST1': 'DST1',
        'DST2': 'DST2', 'DST3': 'DST3', 'DST4': 'DST4', 'SALA': 'SALA',
        'SALC': 'SALC',  'HBr': 'HBr', 'BrNO2': 'BrNO$_{2}$',
        'BrNO3': 'BrNO$_{3}$', 'MPN': 'CH$_{3}$O$_{2}$NO$_{2}$',
        'ISOPN': 'ISOPN', 'MOBA': 'MOBA', 'PROPNN': 'PROPNN',
        'HAC': 'HAC', 'GLYC': 'GLYC', 'MMN': 'MMN', 'RIP': 'RIP',
        'IEPOX': 'IEPOX', 'MAP': 'MAP', 'AERI': 'Aerosol Iodine', 'Cl2': 'Cl$_{2}$',
        'Cl': 'Cl', 'HOCl': 'HOCl', 'ClO': 'ClO', 'OClO': 'OClO', 'BrCl': 'BrCl',
        'HI+OIO+IONO+INO': 'HI+OIO+INO$_{2}$+INO',
        'CH2IX': 'CH$_{2}$IX (X=Cl, Br, I)',
        'IxOy': 'I$_{2}$O$_{X}$ ($_{X}$=2,3,4)',
        'CH3I': 'CH$_{3}$I', 'OH': 'OH', 'HO2': 'HO$_{2}$', 'MO2': 'MO$_{2}$',
        'RO2': 'RO$_{2}$', 'ISALA': 'Iodine on SALA',
        'ISALC': 'Iodine on SALC', 'CH4': 'CH$_{4}$', 'MOH': 'Methanol',
        'RD01': r'I + O$_{3}$ $\rightarrow$ IO + O$_{2}$',
        # Adjusted names
        'ALD2': 'Acetaldehyde',
        # Analysis names
        'iodine_all': 'All Iodine', 'Iy': 'I$_{\\rm y}$',\
        'IOy': 'IO$_{\\rm y}$', \
        'IyOx': 'I$_{y}$O$_{x}$',
        'IOx': 'IO$_{\\rm x}$', \
        'iodine_all_A': 'All Iodine (Inc. AERI)',  \
        'I2Ox': 'I$_{2}$O$_{\\rm X}$', 'AERI/SO4': 'AERI/SO4', \
        'EOH': 'Ethanol', 'OH reactivity / s-1': 'OH reactivity / s$^{-1}$', \
        'PSURF': 'Pressure at the bottom of level', \
        'GMAO_TEMP': 'Temperature', 'TSKIN': 'Temperature at 2m', \
        'GMAO_UWND': 'Zonal Wind', 'GMAO_VWND': 'Meridional Wind', \
        'U10M': '10m Meridional Wind', 'V10M': '10m Zonal Wind', \
        'CH2OO': 'CH$_{2}$OO', 'Sulfate': 'Sulfate', 'VOCs': 'VOCs', \
        'GMAO_ABSH': 'Absolute humidity', 'GMAO_SURF': 'Aerosol surface area', \
        'GMAO_PSFC': 'Surface pressure',
        # Family/group species/tracer Names
        'N_specs': 'NO$_{\\rm y}$', 'NOy': 'NO$_{\\rm y}$',
        'Bry': 'Br$_{\\rm y}$', 'Cly': 'Cl$_{\\rm y}$', 'NIT+NITs': 'NIT+NITs',  \
        'N_specs_no_I': 'NO$_{\\rm y}$ exc. iodine', 'TSO4': 'TSO$_4$',
        'NOx': 'NO$_{\\rm x}$', 'HOx': 'HO$_{\\rm x}$', 'TNO3': 'TNO$_3$', \
        'SOx': 'SO$_{\\rm x}$', 'PM2.5': 'PM$_{2.5}$', 'VOC': 'VOC', \
        'NIT+NH4+SO4': 'NO${_3}{^-}$+NH${_4}{^+}$+SO${_4}{^{2-}}$',
        'NIT_ALL': 'NIT (all)', 'PM10': 'PM$_{10}$', 'BC': 'BC',
        # typos
        'CH2BR2': 'CH$_{2}$Br$_{2}$',\
        # Cly names
        'ClOO': 'ClOO', 'Cl2': 'Cl$_{2}$', \
        'BrCl': 'BrCl', 'ICl': 'ICl', 'HOCl': 'HOCl', 'ClO': 'ClO', 'ClOO': 'ClOO', \
        'OClO': 'OClO', 'Cl2O2': 'Cl$_{2}$O$_{2}$', 'HCl': 'HCl', \
        'ClNO2': 'ClNO$_{2}$', 'ClNO3': 'ClNO$_{3}$', 'Cl': 'Cl',\
        'CH3Cl': 'CH$_{3}$Cl',  'CH2Cl2': 'CH$_{2}$Cl$_{2}$', \
        'CHCl3': 'CHCl$_{3}$',
        # Bry names
        'BrSALC': 'Br- on SALC', 'BrSALA': 'Br- on SALA',
        # add planeflight variabels  for ease of processing
        'LON': 'Lon.', 'LAT': 'Lat.', 'PRESS': 'Press.',
        # add combined species for easy of processing
        'HOCl+Cl2': 'HOCl+Cl$_2$', 'HOBr+Br2': 'HOBr+Br$_2$',
        'HNO3/NOx': 'HNO$_3$/NO$_{\\rm x}$',
        'HNO3+NIT': 'HNO$_3$+NIT', 'HNO3+NO3': 'HNO$_3$+NO$_3$',
        'NIT/NOx': 'NIT/NO$_{\\rm x}$', 'HNO3/NIT': 'HNO$_3$/NIT',
        # Add pseudo species
        'Cl-': 'Cl$^{-}$',
    }
    return spec_dict[input_x]

# -------------- Non-generic Functions
#
# NOTE(s):
# (1) These are retained, but will be migrated to a seperate non-generic module
# (2) It is not advised to use these.


def gaw_2_name():
    """
    Returns dictionary GAW of sites
    """
    wdf = get_dir('dwd') + 'ozonesurface/' + 'gaw_site_list.h5'
    df = pd.read_hdf(wdf,  'wp', mode='r')
    names = df.values[:, 1]

    # alter long name for CVO
    ind = [n for n, i in enumerate(names) if
           (i == 'Cape Verde Atmospheric Observatory')]
    names[ind[0]] = 'Cape Verde'

    return dict(list(zip(df.index, names)))


def get_global_GAW_sites(f='gaw_site_list_global.h5'):
    """
    Get list of (just) GAW global sites

    Notes
    -----
     - This data is from Sofen et al 2016 and freely availible.
     (BADC doi:10.5285/08fbe63d-fa6d-4a7a-b952-5932e3ab0452 )
    """
    wd = get_dir('dwd') + 'ozonesurface/'
    df = pd.read_hdf(wd+f,  'wp', mode='r')
    vars = sorted(list(df.index))
    # Kludge: remove those not in "grouped" analysis
    # ( Q: why are these sites not present?  - A: data control for lomb-scragle)
    [vars.pop(vars.index(i)) for i in ['ZUG', 'ZSF', 'ZEP', 'WLG', 'USH', 'SDK',
                                       'PYR', 'PUY', 'PAL', 'MKN', 'IZO', 'HPB', 'DMV', 'BKT', 'AMS', 'ALT', 'ABP']]
# [ 'AMS', 'MKN', 'IZO' , 'WLG', 'PYR', 'USH', 'ABP', 'ALT'] ]
    return vars


def get_loc(loc=None, rtn_dict=False, debug=False):
    """
    Dictionary to store locations for automated analysis

    Data arranged: LON, LAT, ALT
    ( LON in deg E, LAT in deg N, ALT in metres a.s.l. )

    Notes
    -----
     - double up? ( with 5.02 ?? )
     - Now use Class of GEO_site in preference to this func?
     - UPDATE NEEDED: move this to func_vars4obs
    """

    loc_dict = {
        # --- CAST/CONTRAST
        'GUAM':  (144.800, 13.500, 0),
        'CHUUK': (151.7833, 7.4167, 0),
        'PILAU': (134.4667, 7.3500, 0),
        'London': (-0.1275, 51.5072, 0),
        'Weybourne': (1.1380, 52.9420,  0),
        'WEY': (1.1380, 52.9420,  0),  # Weyboure ID
        'Cape Verde': (-24.871, 16.848, 0),
        'CVO': (-24.871, 16.848,  0),  # Cape Verde ID
        'CVO1': (-24.871, 16.848,  0),  # Cape Verde ID
        'CVO (N)': (-24.871, 16.848+4,  0),  # Cape Verde (N)
        'CVO2': (-24.871, 16.848+4,  0),  # Cape Verde (N)
        'CVO (NNW)': (-24.871, 16.848+8.,  0),  # Cape Verde (NNW)
        'CVO3': (-24.871, 16.848+8.,  0),  # Cape Verde (NNW)
        'CVO (NW)': (-24.871-4, 16.848+4.,  0),  # Cape Verde (NW)
        'CVO4': (-24.871-4, 16.848+4.,  0),  # Cape Verde (NW)
        'CVO (W)': (-24.871-4, 16.848,  0),  # Cape Verde (W)
        'CVO5': (-24.871-4, 16.848,  0),  # Cape Verde (W)
        'CVO (S)': (-24.871, 16.848-4,  0),  # Cape Verde (S)
        'CVO6': (-24.871, 16.848-4,  0),  # Cape Verde (S)
        'CVO (SW)': (-24.871-4, 16.848-4,  0),  # Cape Verde (SW)
        'CVO7': (-24.871-4, 16.848-4,  0),  # Cape Verde (SW)
        # --- ClearFlo
        'North Ken':  (-0.214174, 51.520718, 0),
        'KEN':  (-0.214174, 51.520718, 0),
        'BT tower': (-0.139055, 51.521556, 190),
        'BTT': (-0.139055, 51.521556, 190),
        # --- ClNO2 sites
        'HOU': (-95.22, 29.45, 0),
        'BOL': (-105.27, 40.0, 1655 + 150),
        'LAC': (-118.23, 34.05, 	0),
        'HES': (8.45, 50.22, 	825),
        'SCH': (114.25, 22.22, 60),
        'TEX': (-95.425000, 30.350278,  60),
        'CAL': (-114.12950, 51.07933,  1100),
        'PAS':  (-118.20, 34.23, 246),
        # --- ClNO2 (UK) sites
        'PEN':  (-4.1858, 50.3214, 0.),
        'LEI_AUG':  (-1.127311, 52.619823, 0.),
        'LEI_MAR':  (-1.127311, 52.619823, 0.),
        'LEI':  (-1.127311, 52.619823, 0.),
        'Leicester':  (-1.127311, 52.619823, 0.),
        'Mace_head_M3': (-10.846408, 53.209003, 0.),
        'Penlee':  (-4.1858, 50.3214, 0.),
        'Penlee_M2': (-2.0229414, 49.7795272, 0.),
        'Penlee_M3': (-5.3652425, 49.8370764, 0.),
        'Penlee_M4': (-4.15,  50.25, 0.),
        'Penlee_M5': (-0.85, 50.25, 0.),
        'Penlee_M6': (-7.05, 50.25, 0.),
        'Penlee_M7': (-4.1858, 50.1, 0.),
        # --- Europe sites
        'DZK':  (4.5000, 52.299999237, 4),
        # --- O3 preindustrial
        'MON':  (2.338333, 48.822222,  75+5),
        #    'MON' : (2.3, 48.8, 80), # Monsoursis
        # Pavelin  et al. (1999) / Mickely  et al. (2001)
        # 0 m. a. l. assumed following ( "<500m") in Mickely  et al. (2001)
        'ADE': (138.0, -35.0, 0),  # Adelaide
        'COI': (-8.0, 40.0, 0),  # Coimbra
        'HIR': (132.0, 34.0, 0),  # Hiroshima
        'HOB': (147.0, -43.0, 0),  # Hobart
        'HOK': (114.0, 22.0, 0),  # Hong Kong
        'LUA': (14.0, -9.0, 0),  # Luanda
        'MAU': (57.0, -20.0, 0),  # Mauritius
        'MOV': (-56.0, -35.0, 0),  # Montevideo
        'MVT': (4.0, 44.0, 1900),  # Mont-Ventoux
        'NEM': (145.0, 43.0, 0),  # Nemuro
        'TOK': (139.0, 35.0, 0),  # Tokyo
        'VIE': (16.0, 48.0, 0),  # Vienna
        'PDM': (0.0, 43.0, 1000),  # Pic du midi
        # ---  Misc
        #    'MAC' : ( -10.846408, 53.209003, 0 ) # Mace Head.
        'MAC': (-9.9039169999999999, 53.326443999999995, 0),  # Mace Head.
        'Mace Head': (-9.9039169999999999, 53.326443999999995, 0),  # .
        'Brittany': (-4.0, 48.7, 0),  # Brittany, France
        'Ria de Arousa': (-8.87, 42.50, 0),  # Ria de Arousa, Spain
        'Mweenish Bay': (-9.83, 53.31, 0),  # Ireland
        'Harestua': (10.7098608, 60.2008617, 0),  # Norway
        'Cartagena': (-1.0060599, 37.6174104, 0),  # Spain
        'Malasapina - final day': (-8.338, 35.179, 0),  # final day of cruise
        'Dagebull': (8.69, 54.73, 0),
        'Lilia': (-4.55, 48.62, 0),
        'Heraklion': (25.1, 35.3, 0),  # Heraklion, Crete
        'Sylt': (8.1033406, 54.8988164, 0),
        'Sicily': (14.2371407,  38.5519809, 0),  # Sicily
        #    'Frankfurt' : ( 8.45,50.22, )
        # --- Global GAW sites (from gawsis
        'Barrow': (-156.6114654541, 71.3230133057,  11),
        'Ascension Island': (-14.3999996185, -7.9699997902, 91),
        'Neumayer': (-8.265999794, -70.6660003662, 42),
        'Hilo': (-155.0700073242, 19.5799999237,  11),
        'Samoa': (-170.5645141602, -14.2474746704, 77),
        'Assekrem': (5.6333332062, 23.2666664124,  2710),
        # --- Misc
        'UoM_Chem': (-2.2302418, 53.4659844, 38),
        'CDD': (6.83333333, 45.8333333, 4250),
        'NEEM': (-51.12, 77.75, 2484),
        'Welgegund': (26.939311,  -26.570146, 1480),
        'WEL': (26.939311,  -26.570146, 1480),  # abrev. Welgegund
        'Botsalano': (25.75, -25.54, 1420),
        'BOT': (25.75, -25.54, 1420),  # abrev. Botsalano
        'Marikana': (27.48, -25.70, 1170),
        'MAR': (27.48, -25.70, 1170),  # abrev. Marikana
        'Elandsfontein': (29.42, -26.25, 1750),
        'ELA': (29.42, -26.25, 1750),  # abrev. Elandsfontein
    }
    if rtn_dict:
        return loc_dict
    else:
        return loc_dict[loc]


def GC_var(input_x=None, rtn_dict=False, debug=False):
    """
    General Dictionary to manage common variables used by GC
    analysis programmes.

    Parameters
    ----------
    input_x (str): species/tracer/variable/etc name

    Returns
    -------
    values (e.g. list) from dictionary store

    Notes
    -----
     - A lot of this dictionary is vestigial. consider removing entirely?
        or moving to redundent section
     - Variables includes:
    f_var = GC flux (EW, NS , UP) variables
    Ox = 'Ox', 'POX', 'LOX' + list of drydep species
    ( # not inc. 'NO3df', 'HNO4df', 'BrOdf' , 'BrNO2', 'IO', 'IONO', 'OIO', )
    Ox_p = Ox prod list
    Ox-l = Ox loss list
    d_dep  = dry dep (category, name = species)
    w_dep  = wet dep ( 3x categories
    ( WETDCV = rain out loss in convective updrafts (kg/s),
    WETDLS = rainout in large scale precip (kg/s),
    CV-FLX = Mass change due to cloud convection (kg/s); name = species)
    BL_m = UPWARD MASS FLUX FROM BOUNDARY-LAYER MIXING,
    (category, name = species)
    f_strat  = strat flux (to tropsosphere) (category, name = species)
    """
    if debug:
        print('GC_var called for {}'.format(input_x))
    GC_var_dict = {
        # --- Ox budget analysis
        'f_var': ['EW-FLX-$', 'NS-FLX-$', 'UP-FLX-$'],
        'r_t': ['Photolysis', 'HOx', 'Bromine', 'Iodine'],
        'r_tn': ['Photolysis', 'HOx', 'Bromine', 'Iodine'],
        'r_tn_lc': ['photolysis', 'HOx', 'bromine', 'iodine'],
        # Ox loss families inc. Cly
        'r_tn_Cly': ['Photolysis', 'HOx', 'Chlorine', 'Bromine', 'Iodine'],
        'r_tn_lc_Cly': ['photolysis', 'HOx', 'chlorine', 'bromine', 'iodine'],
        'fams': ['I2', 'HOI', 'IO', 'I', 'HI+OIO+IONO+INO', 'IONO2', 'IxOy', \
                 'CH3I', 'CH2IX'],
        # Iy families + AERI
        'fams_A':  ['I2', 'HOI', 'IO', 'I', 'HI+OIO+IONO+INO', 'IONO2', \
                    'IxOy', 'CH3I', 'CH2IX', 'AERI'],
        # List slices
        'fam_slice': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 8), (8, 9), (9, 12), \
                      (12, 13), (13, None)],
        'fam_slice_A': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 8), (8, 9), (9, 12), \
                        (12, 13), (13, 16), (16, None)],
        # POx lists - redundant?
        #   'POx_l_fp' : ['PO3_01', 'PO3_03', 'PO3_02', 'PO3_05','PO3_14',\
        #     'PO3_15', 'PO3_18', 'PO3_19', 'PO3_20', 'PO3_21', 'PO3_22', \
        #     'PO3_24', 'PO3_25', 'PO3_26', 'PO3_27', 'PO3_30', 'PO3_31', \
        #     'PO3_32', 'PO3_33', 'PO3_34', 'PO3_35', 'PO3_37', 'PO3_38', 'PO3_39', \
        #     'PO3_40', 'PO3_41', 'PO3_43'],
        'Ox_key': ['POX', 'PO3_14', 'PO3_15',   'LOX'],
        # , 'LO3_18', 'LO3_03', 'LO3_02','LR25', 'LR21', 'LR5','LR6','LO3_34', 'LO3_33','LO3_24', 'LO3_35'  ],
        'POxLOx': ['POX', 'LOX'],
        'iPOxiLOx': ['POX', 'LOX', 'iPOX', 'iLOX'],
        # --- Iy/ Iodine budget analysis
        'BL_FT_UT': [(0, 6), (6, 26), (26, 38)],
        'n_order': ['CH2IX', 'CH3I', 'I2', 'HOI', 'IO', 'I', 'IONO2', \
                    'HI+OIO+IONO+INO', 'IxOy'],
        'n_order_A': ['CH2IX', 'CH3I', 'I2', 'HOI', 'IO', 'I', 'IONO2', \
                      'HI+OIO+IONO+INO', 'IxOy', 'AERI'],
        'I_l': ['RD01', 'RD02', 'RD16', 'RD19', 'RD24', 'RD27'],
        # LO37 swaped for RD97 as LO37 assigned to loss point of I2O3 uptake
        'IO_l': ['RD09', 'RD10', 'RD11', 'RD12', 'RD23', 'LO3_24', 'RD37', \
                 'RD97', 'RD66'],
        'I_p': [ \
            'RD06', 'RD07', 'RD10', 'RD11', 'RD47', 'RD15', 'RD17', 'RD20', 'RD22',\
            'LO3_24', 'RD64', 'RD65', 'RD66', 'RD67', 'RD68', 'RD69', 'RD70', \
            'RD71', 'RD72', 'RD73', 'RD88', 'RD89'],
        'IO_p': ['RD01', 'RD08', 'RD46', 'RD25', 'RD27', 'RD56'],
        'sOH': ['LO3_18'],
        'd_dep': ['DRYD-FLX'],
        'w_dep': ['WETDCV-$', 'WETDLS-$'],
        'BL_m': ['TURBMC-$'],
        'f_strat': ['STRT-FL'],
        'p_l': ['PORL-L=$'],
        'Cld_flx': ['CV-FLX-$'],
        'I_Br_O3': [ \
            'IO', 'OIO', 'HOI', 'I2', 'I', 'CH3IT', 'CH2I2', 'CH2ICl', \
            'CH2IBr', 'C3H7I', 'C2H5I', 'BrO', 'Br', 'HOBr', 'Br2',\
            'CH3Br', 'CH2Br2', 'CHBr3', 'O3', 'CO', ],
        'IOrg_RIS': [ \
            'CH3IT', 'CH2ICl', 'CH2I2', 'CH2IBr', 'I2', 'HOI', 'I', 'IO', \
            'OIO', 'HI', 'IONO', 'IONO2'],
        'I_specs': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', \
            'I2O3', 'I2O4''CH3IT', 'CH2I2', 'I', 'INO'],
        'Iy': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'INO', 'IONO', 'IONO2', 'I2O2', \
            'I2O3', 'I2O4', 'I', ]+['ICl', 'IBr'],
        'IxOy': ['IO', 'OIO',  'I2O2', 'I2O3', 'I2O4'],
        'Iy+AERO': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'INO', 'IONO', 'IONO2', 'I2O2', \
            'I2O3', 'I2O4', 'I', ]+['ICl', 'IBr']+['AERI'+'ISALA'+'ISALC'],
        'Iy1.1': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', \
            'I2O4', 'I', 'INO'],
        'IOy': [ \
            'HOI', 'IO', 'OIO', 'IONO', 'IONO2', 'INO', 'I2O2', \
            'I2O4', 'I2O3'],
        'IOy1.1': [\
            'HOI', 'IO', 'OIO', 'IONO', 'IONO2', 'INO', 'I2O2', 'I2O4'],
        'I2Ox': ['I2O2', 'I2O4', 'I2O3'],
        'IyOx1.1': ['I2O2', 'I2O4'],
        'Iy_no_i2o4': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', 'I', 'INO', \
            'I2O3'],
        'Iy_no_i2o41.1': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', 'I', 'INO'],
        'Phot_s_Iy': ['CH3IT', 'CH2ICl', 'CH2I2', 'CH2IBr'],
        #['RD89', 'RD88', 'RD71', 'RD72'],
        'HOI': ['HOI'],
        'IOx': ['IO', 'I', ],
        'IO': ['IO'],
        'I': ['I', ],
        'OIO': ['OIO'],
        # LOx is p/l tracer name, for Loss of IOx
        'LIOx': ['LIOx'],
        # LOx is p/l tracer name, for Loss of IOx
        'PIOx': ['PIOx'],
        'iodine_all': ['I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO', \
                       'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3', 'I2O5', 'CH3IT',\
                       'CH2I2', 'CH2ICl', 'CH2IBr', 'C3H7I', 'C2H5I', 'ICl', 'I2O', \
                       'IBr', 'HIO3', ],
        'iodine_all_A': ['I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO', \
                         'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3', 'I2O5', 'CH3IT', \
                         'CH2I2', 'CH2ICl', 'CH2IBr', 'C3H7I', 'C2H5I', 'ICl', 'I2O', \
                         'IBr', 'HIO3', 'AERI'],
        'iodine_all_A_v2': [
            'I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO',  'IONO', \
            'IONO2', 'I2O2', 'I2O4', 'I2O3', 'CH3IT', 'CH2I2', \
            'CH2ICl', 'CH2IBr', 'ICl', 'IBr', 'AERI', 'ISALA', 'ISALC'],
        # Misc analysis
        'LHOI': ['RD65', 'RD63', 'RD08'],
        'LHOBr': ['LR25', 'LR30', 'LR21'],
        'LI2': ['RD64', 'RD06', 'RD22'],
        'LCH2I2': ['RD72'],
        'LCH2Cl': ['RD88'],
        'LCH2Br': ['RD89'],
        'LCH3IT': ['RD15', 'RD71'],
        'sHOX': ['HOI', 'HOBr'],
        'HO2_loss': [\
            'PO3_14', 'RD09', 'RD02', 'LR2', 'LR3', 'PO3_46', 'PO3_02', 'PO3_03', \
            'PO3_05'],
        'CAST_int': [ \
            'IO', 'OIO', 'HOI', 'I2', 'I', 'HOI', 'CH3I', 'CH2I2', 'CH2ICl', 'CH2IBr',\
            'C3H7I', 'C3H5I', 'BrO', 'Br', 'HOBr', 'Br2', 'CH3Br', 'CH2Br2', \
            'CHBr3', 'O3', 'CO', 'OH', 'HO2', 'NO', 'NO2'],
        'CAST_intn': [\
            'IO', 'OIO', 'HOI', ' I2', 'I', 'HOI', 'CH3IT', 'CH2I2', 'CH2ICl', \
            'CH2IBr', 'C3H7I', 'C2H5I', 'BrO', 'Br', 'HOBr', 'Br2', 'CH3Br', \
            'CH2Br2', 'CHBr3', 'O3', 'CO', 'DMS', 'NO', 'HNO3', 'HNO4', \
            'NO2', 'NO3', 'PAN', 'HNO2', 'N2O5'],
        'CAST_int_n': [\
            'IO', 'OIO', 'HOI', 'I2', 'I', 'HOI', 'CH3I', 'CH2I2', 'CH2ICl', 'CH2IBr',\
            'C3H7I', 'C2H5I', 'BrO', 'Br', 'HOBr', 'Br2', 'CH3Br', 'CH2Br2', \
            'CHBr3', 'O3', 'CO', 'OH', 'HO2', 'NO', 'NO2'],
        'diurnal_sp': ['IO', 'I2', 'CH2I2', 'BrO'],
        'obs_comp': [\
            'CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr', 'C2H5I', 'C3H7I', 'I2', 'IO'],
        'emiss_specs': ['CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr', 'I2', 'HOI'],
        'w_dep_specs': [\
            'I2', 'HI', 'HOI', 'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3',\
            'AERI'],  # , 'IBr', 'ICl']
        'd_dep_specsl1.1': [\
            'I2', 'HI', 'HOI', 'IONO', 'IONO2',  'I2O2', 'I2O4', 'AERI'],  # , 'IO', 'OIO'] ,
        'd_dep_specs': [ \
            'I2df', 'HIdf', 'HOIdf', 'IONOdf', 'IONO2df',  'I2O2df', 'I2O4df', \
            'I2O3df', 'AERIdf', ],  # , 'IOdf', 'OIOdf'], #
        'd_dep_specs_3.0': [
            'I2df', 'HIdf', 'HOIdf', 'IONOdf', 'IONO2df',  'I2O2df', 'I2O4df', \
            'I2O3df', 'ICldf', 'IBrdf', 'AERIdf', ],  # , 'IOdf', 'OIOdf'], #
        'Bry_d_dep_specs': [ \
            'HBr', 'HOBr',  'BrCl', 'Br2', 'IBr', 'BrNO3', ], \
        'Bry_w_dep_specs': [ \
            'HBr', 'HOBr',  'BrCl', 'Br2', 'IBr'], \
        'Cly_d_dep_specs': [ \
            'HCl', 'HOCl', 'ClNO3', 'BrCl', 'ICl'], \
        'I2_het_cyc': ['RD59', 'RD92', 'RD63'],
        # HI, I2O2, I2O4, I2O3 uptake (prev: 2OIO excuded as I2Ox formaed, IO+OIO included as I2O3 not treated )
        'I_het_loss': ['RD58', 'RD62', 'RD93', 'RD95'],
        # ['RD60','RD61','RD62','RD52','RD53','RD54','RD55','RD13'],  # RD13 = OIO + OH => HIO3  86 => AERI loss
        # -- Het ( v3.0+)
        'I2_het_cyc_v3': ['RD59', 'RD92', 'RD63'],
        'I_het_loss_v3': [  \
            # I2O2 all ( RD62), HI ssa (RD58),
            'RD58', 'RD62', 'RD93', 'RD95', \
            # loss to SSA/other aerosols
            'LR44', 'LR45', 'LR32',   # HOI
            'LR34',  # HI other
            'LR42', 'LR43', 'LR35',  # IONO2
            'LR46', 'LR47', 'LR39'],  # IONO
        'NOx': ['NO', 'NO2'],
        'HOx': ['OH', 'HO2'],
        'SOx': ['SO2', 'SO4', 'SO4s'],
        'N_specs': [
            'NO', 'NO2', 'PAN', 'HNO3', 'PMN', 'PPN', 'R4N2', 'N2O5', 'HNO4',\
            'NH3', 'NH4', 'BrNO2', 'BrNO3', 'MPN', 'ISOPN', 'PROPNN', 'MMN',\
            'NO3', 'HNO2', 'IONO', 'IONO2', 'INO'],
        'NOy': [
            'NO', 'NO2', 'PAN', 'HNO3', 'PMN', 'PPN', 'R4N2', 'N2O5', 'HNO4',\
            #    'NH3', 'NH4',
            'BrNO2', 'BrNO3', 'MPN', 'ISOPN', 'PROPNN', 'MMN',\
            'NO3', 'HNO2', 'IONO', 'IONO2', 'INO', 'ClNO2', 'ClNO3'],
        'N_specs_no_I':  [
            'NO', 'NO2', 'PAN', 'HNO3', 'PMN', 'PPN', 'R4N2', 'N2O5', 'HNO4', \
            'NH3', 'NH4', 'BrNO2', 'BrNO3', 'MPN', 'ISOPN', 'PROPNN', 'MMN',\
            'NO3', 'HNO2'],
        'Bry': [\
            'Br2', 'BrCl', 'IBr', 'HOBr', 'BrO', 'HBr', 'BrNO2', 'BrNO3', 'Br'],\
        'Cly': [ \
            'ClOO', 'OClO', 'ClO', 'Cl2O2', 'ICl', 'Cl2', 'Cl', 'BrCl', 'ClNO3',
            'ClNO2', 'HOCl', 'HCl'],
        'Cl_specs': [ \
            'Cl2', 'BrCl', 'ICl', 'HOCl', 'ClO', 'ClOO', 'OClO', 'Cl2O2', 'HCl',  \
            'ClNO2', 'ClNO3', 'Cl', 'CH2Cl2', 'CHCl3', 'CH2ICl', 'CH3Cl'],
        'Br_specs': ['Br2', 'BrNO3', 'Br', 'HBr', 'CH2IBr', \
                     'CH3Br', 'CH2Br2', 'BrCl', 'BrNO2', 'BrSALC', 'BrSALA', \
                     'HOBr', 'IBr', 'BrO', 'CHBr3'],
        'Br_emiss': ['CH2Br2', 'CHBr3', 'SSBr2'],  # 'CH3Br'
        'johan_GRL_TRAs': [ \
            'BrCl', 'Cl2', 'Cl', 'ClO', 'HCl', 'HOCl', 'ClNO2', 'ClNO3', \
            'ClOO', 'OClO', 'Cl2O2', 'CH3Cl', 'CH2Cl2', 'CHCl3', 'BrSALA', \
            'BrSALC'],
        'I_N_tags': ['RD10', 'RD23', 'RD19', 'RD16', 'RD22', \
                     'RD56', 'RD24', 'LO3_30', 'RD69', 'RD68', 'RD20', 'RD21', 'RD25', \
                     'LO3_39', 'RD17', 'RD18', 'RD75'],
        'Br_N_tags': ['LR7', 'LR18', 'LR17', 'LR11', 'LR8', \
                      'LR20', 'LR26', 'LR28', 'LR27'],
        'inactive_I': [ \
            'BrCl', 'OClO', 'ClO', 'HOCl', 'Cl', 'Cl2', 'I2O5', 'I2O', 'HIO3', \
            'IBr', 'ICl', 'C2H5I', 'C3H7I'],  # I2O3 now active.
        'active_I': [ \
            'I2', 'HOI', 'IO', 'I', 'HI', 'OIO', 'INO', 'IONO', 'IONO2', 'I2O2',
            'I2O4', 'I2O3', 'CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr'],
        'surface_specs': [\
            'O3', 'NO', 'NO2', 'NO3', 'N2O5', 'IO', 'IONO2'],
        # --- Model run title dictionaries
        'run_name_dict': {
            'run': 'Br-I', \
            'Br_2ppt': 'Halogens (I+,Br+) + fixed 2 pptv BrO', \
            'just_I': 'IODINE', 'no_hal': 'NOHAL', 'just_Br': \
            'BROMINE', \
            'Br_1ppt': 'Halogens (I+,Br+) + fixed 1 pptv BrO', \
            'obs': 'Observations'},
        'latex_run_names': {
            'I2Ox_half': 'I$_{2}$O$_{X}$ loss ($\\gamma$) /2',
            'run': 'Br-I',
            'MacDonald_iodide': 'Ocean iodide',
            'Sulfate_up': 'Sulfate uptake',
            'I2Ox_phot_exp': 'I$_{2}$O$_{X}$ exp. X-sections',
            'het_double': 'het. cycle ($\\gamma$) x2',
            'I2Ox_phot_x2': 'I$_{2}$O$_{X}$ X-sections x2',
            'no_het': 'no het. cycle ',
            'I2Ox_double': 'I$_{2}$O$_{X}$ loss ($\\gamma$) x2',
            'just_I': 'IODINE',
            'BrO1pptv': 'MBL BrO 1 pmol mol$^{-1}$',
            'het_half': 'het. cycle ($\\gamma$) /2',
            'Just_I_org': 'Just org. I',
            'no_I2Ox': 'No I$_{2}$O$_{X}$ Photolysis',
            'BrO1pptv_ALL': 'BrO 1 pptv in Trop.',
            'BrO2pptv': 'MBL BrO 2 pmol mol$^{-1}$',
            # adjust from GBC to ACP names
            #        'no_hal': '(I-,Br-)', 'Just_Br': '(I-,Br+)',
            'no_hal': 'NOHAL', 'Just_Br': 'BROMINE',
            # Add for v10 ( 2.0 Cl/Br/I code )
            'run.Cl.Br.I.aerosol':  'GEOS-Chem (v10 Cl.Br.I)', \
            # kludge for diurnal plot
            'Iodine simulation.': 'Br-I.', '(I+,Br+)': 'Br-I.', '(I+,Br-)': 'IODINE',\
            '(I-,Br+)': 'BROMINE', '(I-,Br-)': 'NOHAL'},
        # --- Tracer unit handling
        'spec_2_pptv': [ \
            'I2', 'HOI', 'IO', 'OIO', 'HI', 'IONO', 'IONO2', 'I2O2', 'CH3IT', \
            'CH2I2', 'IBr', 'ICl', 'I', 'HIO3', 'I2O', 'INO', 'I2O3', 'I2O4', \
            'I2O5', 'AERI', 'Cl2', 'Cl', 'HOCl', 'ClO', 'OClO', 'BrCl', 'CH2ICl', \
            'CH2IBr', 'C3H7I', 'C2H5I', 'Br2', 'Br', 'BrO', 'HOBr', 'HBr', 'BrNO2',\
            'BrNO3', 'CHBr3', 'CH2Br2', 'CH3Br', 'RCHO', 'MVK', 'MACR', \
            'PMN', 'PPN', 'R4N2', 'DMS', 'SO4s', 'MSA', 'NITs', 'BCPO', 'DST4', \
            'ISOPN', 'MOBA', 'PROPNN', 'HAC', 'GLYC', 'MMN', 'RIP', 'IEPOX', \
            'MAP', 'N2O5', 'NO3'],  # 'HNO4',  'HNO2'],
        'spec_2_pptC': ['PRPE', 'ISOP'],
        # global
        'spec_2_ppbv': [ \
            'NO', 'DMS',  'RIP', 'IEPOX', 'BCPO', 'DST4', 'HAC', 'GLYC', \
            'MACR', 'ISOP'],
        'spec_2_ppbC': ['ALK4'],
        # --- PF dictionaries
        # WARNING - remove non forwards combatible dicts:
        # (GCFP_TRA_d ... GCFP_d2TRA  ... GCFP_d2TRA_justTRA . etc)
        # GCFP_TRA_d is in use by CVO plotters -  use what_species_am_i instead!
        'GCFP_TRA_d': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_96': 'C2H5I', 'TRA_95': 'C3H7I', 'TRA_94': 'CH2IBr', 'TRA_93': 'CH2ICl', 'TRA_92': 'BrCl', 'TRA_91': 'OClO', 'TRA_90': 'ClO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'I2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'HOI', 'TRA_69': 'IO', 'TRA_71': 'HI', 'TRA_70': 'OIO', 'TRA_73': 'IONO2', 'TRA_72': 'IONO', 'TRA_75': 'CH3IT', 'TRA_74': 'I2O2', 'TRA_77': 'IBr', 'TRA_76': 'CH2I2', 'TRA_79': 'I', 'TRA_78': 'ICl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'TRA_01': 'NO', 'TRA_02': 'O3', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'HIO3', 'TRA_81': 'I2O', 'TRA_82': 'INO', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'I2O5', 'TRA_86': 'AERI', 'TRA_87': 'Cl2', 'TRA_88': 'Cl', 'TRA_89': 'HOCl', 'O3': 'O3', 'CO': 'CO'},
        # GCFP_d2TRA is in use by IO plotters -  use what_species_am_i instead!
        'GCFP_d2TRA': {'HIO3': 'TRA_80', 'OCPO': 'TRA_37', 'PPN': 'TRA_16', 'OCPI': 'TRA_35', 'O3': 'TRA_2', 'PAN': 'TRA_3', 'ACET': 'TRA_9', 'IEPOX': 'TRA_62', 'BrNO3': 'TRA_50', 'Br': 'TRA_45', 'HBr': 'TRA_48', 'HAC': 'TRA_58', 'ALD2': 'TRA_11', 'HNO3': 'TRA_7', 'HNO2': 'TRA_66', 'C2H5I': 'TRA_96', 'HNO4': 'TRA_23', 'OIO': 'TRA_70', 'MAP': 'TRA_63', 'PRPE': 'TRA_18', 'HI': 'TRA_71', 'CH2I2': 'TRA_76', 'IONO2': 'TRA_73', 'NIT': 'TRA_32', 'CH3Br': 'TRA_53', 'C3H7I': 'TRA_95', 'C3H8': 'TRA_19', 'DMS': 'TRA_25', 'CH2O': 'TRA_20', 'CH3IT': 'TRA_75', 'CH3I': 'TRA_75', 'NO2': 'TRA_64', 'NO3': 'TRA_65', 'N2O5': 'TRA_22', 'CHBr3': 'TRA_51', 'DST4': 'TRA_41', 'DST3': 'TRA_40', 'DST2': 'TRA_39', 'DST1': 'TRA_38', 'HOCl': 'TRA_89', 'NITs': 'TRA_33', 'RCHO': 'TRA_12', 'C2H6': 'TRA_21', 'MPN': 'TRA_54', 'INO': 'TRA_82', 'MP': 'TRA_24', 'CH2Br2': 'TRA_52', 'SALC': 'TRA_43', 'NH3': 'TRA_30', 'CH2ICl': 'TRA_93', 'RIP': 'TRA_61', 'ClO': 'TRA_90', 'NO': 'TRA_1', 'SALA': 'TRA_42', 'MOBA': 'TRA_56', 'R4N2': 'TRA_17', 'BrCl': 'TRA_92', 'OClO': 'TRA_91', 'PMN': 'TRA_15', 'CO': 'TRA_4', 'CH2IBr': 'TRA_94', 'ISOP': 'TRA_6', 'BCPO': 'TRA_36', 'MVK': 'TRA_13', 'BrNO2': 'TRA_49', 'IONO': 'TRA_72', 'Cl2': 'TRA_87', 'HOBr': 'TRA_47', 'PROPNN': 'TRA_57', 'Cl': 'TRA_88', 'I2O2': 'TRA_74', 'I2O3': 'TRA_83', 'I2O4': 'TRA_84', 'I2O5': 'TRA_85', 'MEK': 'TRA_10', 'MMN': 'TRA_60', 'ISOPN': 'TRA_55', 'SO4s': 'TRA_28', 'I2O': 'TRA_81', 'ALK4': 'TRA_5', 'MSA': 'TRA_29', 'I2': 'TRA_67', 'Br2': 'TRA_44', 'IBr': 'TRA_77', 'MACR': 'TRA_14', 'I': 'TRA_79', 'AERI': 'TRA_86', 'HOI': 'TRA_68', 'BrO': 'TRA_46', 'NH4': 'TRA_31', 'SO2': 'TRA_26', 'SO4': 'TRA_27', 'IO': 'TRA_69', 'H2O2': 'TRA_8', 'BCPI': 'TRA_34', 'ICl': 'TRA_78', 'GLYC': 'TRA_59', 'ALK4': 'ALK4', 'MSA': 'MSA', 'MO2': 'MO2', 'C3H8': 'C3H8', 'ISOP': 'ISOP', 'DMS': 'DMS', 'CH2O': 'CH2O', 'O3': 'O3', 'PAN': 'PAN', 'NO3': 'NO3', 'N2O5': 'N2O5', 'H2O2': 'H2O2', 'NO': 'NO', 'PPN': 'PPN', 'R4N2': 'R4N2', 'HO2': 'HO2', 'NO2': 'NO2', 'PMN': 'PMN', 'ACET': 'ACET', 'CO': 'CO', 'ALD2': 'ALD2', 'RCHO': 'RCHO', 'HNO3': 'HNO3', 'HNO2': 'HNO2', 'SO2': 'SO2', 'SO4': 'SO4', 'HNO4': 'HNO4', 'C2H6': 'C2H6', 'RO2': 'RO2', 'MVK': 'MVK', 'PRPE': 'PRPE', 'OH': 'OH', 'ETO2': 'ETO2', 'MEK': 'MEK', 'MP': 'MP', 'GMAO_TEMP': 'GMAO_TEMP'},
        'GCFP_d2TRA_all_1.6': {'HIO3': 'TRA_80', 'TRA_17': 'TRA_17', 'TRA_16': 'TRA_16', 'TRA_15': 'TRA_15', 'TRA_14': 'TRA_14', 'TRA_13': 'TRA_13', 'TRA_12': 'TRA_12', 'TRA_11': 'TRA_11', 'TRA_19': 'TRA_19', 'ACET': 'ACET', 'RIP': 'TRA_61', 'BrNO3': 'TRA_50', 'HAC': 'TRA_58', 'ALD2': 'ALD2', 'HNO3': 'HNO3', 'HNO2': 'HNO2', 'HNO4': 'HNO4', 'OIO': 'TRA_70', 'MAP': 'TRA_63', 'PRPE': 'PRPE', 'TRA_29': 'TRA_29', 'CH2I2': 'TRA_76', 'I2O2': 'TRA_74', 'NIT': 'TRA_32', 'CH3Br': 'TRA_53', 'C3H7I': 'TRA_95', 'MO2': 'MO2', 'C3H8': 'C3H8', 'I2O5': 'TRA_85', 'TRA_71': 'TRA_71', 'TRA_70': 'TRA_70', 'TRA_73': 'TRA_73', 'DMS': 'DMS', 'TRA_75': 'TRA_75', 'TRA_74': 'TRA_74', 'TRA_77': 'TRA_77', 'TRA_76': 'TRA_76', 'CH2O': 'CH2O', 'TRA_78': 'TRA_78', 'CH3IT': 'TRA_75', 'NO2': 'NO2', 'NO3': 'NO3', 'N2O5': 'N2O5', 'H2O2': 'H2O2', 'PAN': 'PAN', 'HOCl': 'TRA_89', 'TRA_18': 'TRA_18', 'GMAO_TEMP': 'GMAO_TEMP', 'RCHO': 'RCHO', 'C2H6': 'C2H6', 'INO': 'TRA_82', 'MP': 'MP', 'CH2Br2': 'TRA_52', 'CH2ICl': 'TRA_93', 'TRA_59': 'TRA_59', 'TRA_58': 'TRA_58', 'IEPOX': 'TRA_62', 'TRA_53': 'TRA_53', 'TRA_52': 'TRA_52', 'TRA_51': 'TRA_51', 'TRA_50': 'TRA_50', 'TRA_57': 'TRA_57', 'TRA_56': 'TRA_56', 'TRA_55': 'TRA_55', 'TRA_54': 'TRA_54', 'MOBA': 'TRA_56', 'CH3I': 'TRA_75', 'BrCl': 'TRA_92', 'OClO': 'TRA_91', 'CO': 'CO', 'BCPI': 'TRA_34', 'ISOP': 'ISOP', 'BCPO': 'TRA_36', 'MVK': 'MVK', 'TRA_28': 'TRA_28', 'Cl': 'TRA_88', 'TRA_26': 'TRA_26', 'TRA_27': 'TRA_27', 'TRA_24': 'TRA_24', 'I2O3': 'TRA_83', 'I2O4': 'TRA_84', 'TRA_23': 'TRA_23', 'TRA_20': 'TRA_20', 'TRA_21': 'TRA_21', 'MMN': 'TRA_60', 'I2O': 'TRA_81', 'HBr': 'TRA_48', 'ALK4': 'ALK4', 'I2': 'TRA_67', 'PPN': 'PPN', 'IBr': 'TRA_77', 'I': 'TRA_79', 'AERI': 'TRA_86', 'NH4': 'TRA_31', 'SO2': 'SO2', 'SO4': 'SO4', 'NH3': 'TRA_30', 'TRA_08': 'TRA_08', 'TRA_09': 'TRA_09', 'TRA_01': 'TRA_01', 'TRA_02': 'TRA_02', 'TRA_03': 'TRA_03', 'TRA_04': 'TRA_04', 'TRA_05': 'TRA_05', 'TRA_06': 'TRA_06', 'TRA_07': 'TRA_07', 'OCPI': 'TRA_35', 'OCPO': 'TRA_37', 'Br2': 'TRA_44', 'O3': 'O3', 'Br': 'TRA_45', 'TRA_96': 'TRA_96', 'TRA_95': 'TRA_95', 'TRA_94': 'TRA_94', 'TRA_93': 'TRA_93', 'TRA_92': 'TRA_92', 'TRA_91': 'TRA_91', 'TRA_90': 'TRA_90', 'TRA_62': 'TRA_62', 'TRA_63': 'TRA_63', 'TRA_60': 'TRA_60', 'TRA_61': 'TRA_61', 'TRA_66': 'TRA_66', 'TRA_67': 'TRA_67', 'C2H5I': 'TRA_96', 'TRA_65': 'TRA_65', 'TRA_68': 'TRA_68', 'TRA_69': 'TRA_69', 'OH': 'OH', 'IONO2': 'TRA_73', 'HI': 'TRA_71', 'CHBr3': 'TRA_51', 'TRA_46': 'TRA_46', 'DST4': 'TRA_41', 'DST3': 'TRA_40', 'DST2': 'TRA_39', 'DST1': 'TRA_38', 'NITs': 'TRA_33', 'TRA_48': 'TRA_48', 'TRA_49': 'TRA_49', 'TRA_44': 'TRA_44', 'TRA_45': 'TRA_45', 'RO2': 'RO2', 'TRA_47': 'TRA_47', 'TRA_40': 'TRA_40', 'TRA_41': 'TRA_41', 'TRA_42': 'TRA_42', 'TRA_43': 'TRA_43', 'MPN': 'TRA_54', 'ETO2': 'ETO2', 'IO': 'TRA_69', 'TRA_64': 'TRA_64', 'ClO': 'TRA_90', 'NO': 'NO', 'SALA': 'TRA_42', 'SALC': 'TRA_43', 'R4N2': 'R4N2', 'PMN': 'PMN', 'TRA_25': 'TRA_25', 'CH2IBr': 'TRA_94', 'TRA_22': 'TRA_22', 'BrNO2': 'TRA_49', 'IONO': 'TRA_72', 'Cl2': 'TRA_87', 'HOBr': 'TRA_47', 'PROPNN': 'TRA_57', 'MEK': 'MEK', 'TRA_72': 'TRA_72', 'ISOPN': 'TRA_55', 'SO4s': 'TRA_28', 'TRA_79': 'TRA_79', 'MSA': 'MSA', 'TRA_39': 'TRA_39', 'TRA_38': 'TRA_38', 'GLYC': 'TRA_59', 'TRA_35': 'TRA_35', 'TRA_34': 'TRA_34', 'TRA_37': 'TRA_37', 'TRA_36': 'TRA_36', 'TRA_31': 'TRA_31', 'TRA_30': 'TRA_30', 'TRA_33': 'TRA_33', 'TRA_32': 'TRA_32', 'HO2': 'HO2', 'MACR': 'TRA_14', 'HOI': 'TRA_68', 'BrO': 'TRA_46', 'ICl': 'TRA_78', 'TRA_80': 'TRA_80', 'TRA_81': 'TRA_81', 'TRA_82': 'TRA_82', 'TRA_83': 'TRA_83', 'TRA_84': 'TRA_84', 'TRA_85': 'TRA_85', 'TRA_86': 'TRA_86', 'TRA_87': 'TRA_87', 'TRA_88': 'TRA_88', 'TRA_89': 'TRA_89', 'GMAO_TEMP': 'GMAO_TEMP', 'GMAO_UWND': 'GMAO_UWND', 'GMAO_VWND': 'GMAO_VWND'},
        'GCFP_d2TRA_all_1.6.3': {'HIO3': 'TRA_80', 'OCPO': 'TRA_37', 'TRA_65': 'TRA_65', 'PPN': 'PPN', 'TRA_17': 'TRA_17', 'TRA_16': 'TRA_16', 'TRA_15': 'TRA_15', 'OCPI': 'TRA_35', 'TRA_13': 'TRA_13', 'TRA_12': 'TRA_12', 'TRA_11': 'TRA_11', 'O3': 'O3', 'PAN': 'PAN', 'ACET': 'ACET', 'IEPOX': 'TRA_62', 'BrNO3': 'TRA_50', 'Br': 'TRA_45', 'TRA_98': 'TRA_98', 'GMAO_UWND': 'GMAO_UWND', 'TRA_96': 'TRA_96', 'TRA_95': 'TRA_95', 'TRA_94': 'TRA_94', 'TRA_93': 'TRA_93', 'TRA_92': 'TRA_92', 'TRA_91': 'TRA_91', 'HBr': 'TRA_48', 'TRA_72': 'TRA_72', 'HAC': 'TRA_58', 'ALD2': 'ALD2', 'HNO3': 'HNO3', 'HNO2': 'HNO2', 'TRA_60': 'TRA_60', 'TRA_61': 'TRA_61', 'TRA_66': 'TRA_66', 'TRA_67': 'TRA_67', 'C2H5I': 'TRA_96', 'HNO4': 'HNO4', 'TRA_62': 'TRA_62', 'TRA_68': 'TRA_68', 'TRA_69': 'TRA_69', 'OIO': 'TRA_70', 'MAP': 'TRA_63', 'PRPE': 'PRPE', 'OH': 'OH', 'TRA_29': 'TRA_29', 'TRA_14': 'TRA_14', 'HI': 'TRA_71', 'TRA_63': 'TRA_63', 'CH2I2': 'TRA_76', 'IONO2': 'TRA_73', 'TRA_24': 'TRA_24', 'NIT': 'TRA_32', 'CH3Br': 'TRA_53', 'C3H7I': 'TRA_95', 'MO2': 'MO2', 'C3H8': 'C3H8', 'TRA_23': 'TRA_23', 'TRA_71': 'TRA_71', 'TRA_70': 'TRA_70', 'TRA_73': 'TRA_73', 'DMS': 'DMS', 'TRA_75': 'TRA_75', 'TRA_20': 'TRA_20', 'TRA_77': 'TRA_77', 'TRA_76': 'TRA_76', 'CH2O': 'CH2O', 'TRA_78': 'TRA_78', 'CH3IT': 'TRA_75', 'NO2': 'NO2', 'NO3': 'NO3', 'N2O5': 'N2O5', 'CHBr3': 'TRA_51', 'TRA_46': 'TRA_46', 'DST4': 'TRA_41', 'DST3': 'TRA_40', 'DST2': 'TRA_39', 'DST1': 'TRA_38', 'TRA_56': 'TRA_56', 'TRA_19': 'TRA_19', 'HOCl': 'TRA_89', 'TRA_18': 'TRA_18', 'NITs': 'TRA_33', 'GMAO_TEMP': 'GMAO_TEMP', 'TRA_36': 'TRA_36', 'RCHO': 'RCHO', 'TRA_48': 'TRA_48', 'TRA_49': 'TRA_49', 'TRA_44': 'TRA_44', 'C2H6': 'C2H6', 'RO2': 'RO2', 'TRA_47': 'TRA_47', 'TRA_40': 'TRA_40', 'CH3I': 'TRA_75', 'TRA_42': 'TRA_42', 'TRA_43': 'TRA_43', 'TRA_97': 'TRA_97', 'MPN': 'TRA_54', 'ETO2': 'ETO2', 'INO': 'TRA_82', 'MP': 'MP', 'CH2Br2': 'TRA_52', 'SALC': 'TRA_43', 'NH3': 'TRA_30', 'TRA_30': 'TRA_30', 'TRA_64': 'TRA_64', 'CH2ICl': 'TRA_93', 'TRA_59': 'TRA_59', 'TRA_58': 'TRA_58', 'RIP': 'TRA_61', 'TRA_45': 'TRA_45', 'TRA_53': 'TRA_53', 'TRA_52': 'TRA_52', 'TRA_51': 'TRA_51', 'TRA_50': 'TRA_50', 'TRA_57': 'TRA_57', 'GMAO_VWND': 'GMAO_VWND', 'TRA_55': 'TRA_55', 'TRA_54': 'TRA_54', 'ClO': 'TRA_90', 'NO': 'NO', 'SALA': 'TRA_42', 'MOBA': 'TRA_56', 'R4N2': 'R4N2', 'TRA_41': 'TRA_41', 'BrCl': 'TRA_92', 'OClO': 'TRA_91', 'PMN': 'PMN', 'TRA_25': 'TRA_25', 'CO': 'CO', 'TRA_09': 'TRA_09', 'ISALA': 'TRA_97', 'BCPI': 'TRA_34', 'ISOP': 'ISOP', 'ISALC': 'TRA_98', 'BCPO': 'TRA_36', 'TRA_22': 'TRA_22', 'MVK': 'MVK', 'BrNO2': 'TRA_49', 'IONO': 'TRA_72', 'Cl2': 'TRA_87', 'HOBr': 'TRA_47', 'PROPNN': 'TRA_57', 'TRA_28': 'TRA_28', 'Cl': 'TRA_88', 'TRA_26': 'TRA_26', 'TRA_27': 'TRA_27', 'I2O2': 'TRA_74', 'I2O3': 'TRA_83', 'I2O4': 'TRA_84', 'I2O5': 'TRA_85', 'MEK': 'MEK', 'TRA_21': 'TRA_21', 'MMN': 'TRA_60', 'ISOPN': 'TRA_55', 'SO4s': 'TRA_28', 'I2O': 'TRA_81', 'TRA_90': 'TRA_90', 'TRA_74': 'TRA_74', 'ALK4': 'ALK4', 'TRA_79': 'TRA_79', 'MSA': 'MSA', 'TRA_39': 'TRA_39', 'TRA_38': 'TRA_38', 'TRA_81': 'TRA_81', 'TRA_35': 'TRA_35', 'TRA_34': 'TRA_34', 'TRA_37': 'TRA_37', 'I2': 'TRA_67', 'TRA_31': 'TRA_31', 'Br2': 'TRA_44', 'TRA_33': 'TRA_33', 'TRA_32': 'TRA_32', 'HO2': 'HO2', 'IBr': 'TRA_77', 'MACR': 'TRA_14', 'I': 'TRA_79', 'AERI': 'TRA_86', 'HOI': 'TRA_68', 'BrO': 'TRA_46', 'NH4': 'TRA_31', 'SO2': 'SO2', 'SO4': 'SO4', 'IO': 'TRA_69', 'H2O2': 'H2O2', 'TRA_08': 'TRA_08', 'CH2IBr': 'TRA_94', 'ICl': 'TRA_78', 'TRA_01': 'TRA_01', 'TRA_02': 'TRA_02', 'TRA_03': 'TRA_03', 'TRA_04': 'TRA_04', 'TRA_05': 'TRA_05', 'TRA_06': 'TRA_06', 'TRA_07': 'TRA_07', 'TRA_80': 'TRA_80', 'GLYC': 'TRA_59', 'TRA_82': 'TRA_82', 'TRA_83': 'TRA_83', 'TRA_84': 'TRA_84', 'TRA_85': 'TRA_85', 'TRA_86': 'TRA_86', 'TRA_87': 'TRA_87', 'TRA_88': 'TRA_88', 'TRA_89': 'TRA_89'},
        'GCFP_d2TRA_justTRA_1.6': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_96': 'C2H5I', 'TRA_95': 'C3H7I', 'TRA_94': 'CH2IBr', 'TRA_93': 'CH2ICl', 'TRA_92': 'BrCl', 'TRA_91': 'OClO', 'TRA_90': 'ClO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'I2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'HOI', 'TRA_69': 'IO', 'TRA_71': 'HI', 'TRA_70': 'OIO', 'TRA_73': 'IONO2', 'TRA_72': 'IONO', 'TRA_75': 'CH3IT', 'TRA_74': 'I2O2', 'TRA_77': 'IBr', 'TRA_76': 'CH2I2', 'TRA_79': 'I', 'TRA_78': 'ICl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_80': 'HIO3', 'TRA_81': 'I2O', 'TRA_82': 'INO', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'I2O5', 'TRA_86': 'AERI', 'TRA_87': 'Cl2', 'TRA_88': 'Cl', 'TRA_89': 'HOCl'},
        'GCFP_d2TRA_justTRA_1.6.3': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_96': 'C2H5I', 'TRA_95': 'C3H7I', 'TRA_94': 'CH2IBr', 'TRA_93': 'CH2ICl', 'TRA_92': 'BrCl', 'TRA_91': 'OClO', 'TRA_90': 'ClO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'I2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'HOI', 'TRA_69': 'IO', 'TRA_71': 'HI', 'TRA_70': 'OIO', 'TRA_73': 'IONO2', 'TRA_72': 'IONO', 'TRA_75': 'CH3IT', 'TRA_74': 'I2O2', 'TRA_77': 'IBr', 'TRA_76': 'CH2I2', 'TRA_79': 'I', 'TRA_78': 'ICl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_80': 'HIO3', 'TRA_81': 'I2O', 'TRA_82': 'INO', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'I2O5', 'TRA_86': 'AERI', 'TRA_87': 'Cl2', 'TRA_88': 'Cl', 'TRA_89': 'HOCl',  'TRA_98': 'ISALC', 'TRA_97': 'ISALA'},
        #                    'GCFP_d2TRA_all_1.7' : {'TRA_74': 'ICl', 'TRA_25': 'DMS', 'TRA_68': 'CH2I2', 'TRA_44': 'Br2', 'TRA_70': 'CH2IBr', 'TRA_22': 'N2O5', 'TRA_76': 'IO', 'TRA_79': 'INO', 'TRA_23': 'HNO4', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_21': 'C2H6', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_69': 'CH2ICl', 'TRA_50': 'BrNO3', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_73': 'IBr', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_77': 'HI', 'TRA_83': 'I2O3', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_72': 'I2', 'TRA_59': 'GLYC', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_20': 'CH2O', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'TRA_75': 'I', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_01': 'NO', 'TRA_02': 'O3', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'IONO', 'TRA_81': 'IONO2', 'TRA_82': 'I2O2', 'TRA_58': 'HAC', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'TRA_27': 'SO4', 'TRA_78': 'OIO', 'TRA_66': 'HNO2', 'TRA_71': 'HOI', 'TRA_24': 'MP', 'TRA_67': 'CH3IT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO'},
        'GCFP_d2TRA_all_1.7': {'TRA_25': 'DMS', 'TRA_77': 'HI', 'TRA_76': 'IO', 'TRA_23': 'HNO4', 'TRA_71': 'HOI', 'TRA_70': 'CH2IBr', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_79': 'INO', 'TRA_78': 'OIO', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_52': 'CH2Br2', 'TRA_46': 'BrO', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_47': 'HOBr', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_81': 'IONO2', 'TRA_35': 'OCPI', 'TRA_57': 'PROPNN', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_56': 'MOBA', 'TRA_83': 'I2O3', 'TRA_55': 'ISOPN', 'TRA_84': 'I2O4', 'TRA_54': 'MPN', 'TRA_5': 'ALK4', 'TRA_49': 'BrNO2', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_59': 'GLYC', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'CH3IT', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_68': 'CH2I2', 'TRA_69': 'CH2ICl', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_17': 'R4N2', 'TRA_28': 'SO4s', 'TRA_16': 'PPN', 'TRA_58': 'HAC', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_29': 'MSA', 'TRA_22': 'N2O5', 'TRA_73': 'IBr', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_80': 'IONO', 'TRA_26': 'SO2', 'TRA_82': 'I2O2', 'TRA_72': 'I2', 'TRA_48': 'HBr', 'TRA_85': 'AERI', 'TRA_34': 'BCPI', 'TRA_75': 'I', 'TRA_53': 'CH3Br', 'TRA_74': 'ICl'},
        'GCFP_d2TRA_all_2.0': {'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_99': 'I2O3', 'TRA_98': 'I2O2', 'TRA_97': 'IONO2', 'TRA_96': 'IONO', 'TRA_95': 'INO', 'TRA_94': 'OIO', 'TRA_93': 'HI', 'TRA_92': 'IO', 'TRA_91': 'I', 'TRA_90': 'ICl', 'TRA_100': 'I2O4', 'TRA_101': 'ISALA', 'TRA_102': 'ISALC', 'TRA_103': 'AERI', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'BrCl', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'Cl2', 'TRA_69': 'Cl', 'TRA_71': 'HOCl', 'TRA_70': 'ClO', 'TRA_73': 'ClNO2', 'TRA_72': 'HCl', 'TRA_75': 'ClOO', 'TRA_74': 'ClNO3', 'TRA_77': 'Cl2O2', 'TRA_76': 'OClO', 'TRA_79': 'CH2Cl2', 'TRA_78': 'CH3Cl', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_80': 'CHCl3', 'TRA_81': 'BrSALA', 'TRA_82': 'BrSALC', 'TRA_83': 'CH3IT', 'TRA_84': 'CH2I2', 'TRA_85': 'CH2ICl', 'TRA_86': 'CH2IBr', 'TRA_87': 'HOI', 'TRA_88': 'I2', 'TRA_89': 'IBr'},
        'GCFP_d2TRA_all_1.7_EOH_actual_names': {'HNO4': 'HNO4', 'PPN': 'PPN', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'O3': 'O3', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'GMAO_UWND': 'GMAO_UWND', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'CH3IT', 'TRA_65': 'NO3', 'TRA_68': 'CH2I2', 'TRA_69': 'CH2ICl', 'OH': 'OH', 'LAT': 'LAT', 'TRA_71': 'HOI', 'TRA_70': 'CH2IBr', 'TRA_73': 'IBr', 'TRA_72': 'I2', 'TRA_75': 'I', 'TRA_74': 'ICl', 'TRA_77': 'HI', 'TRA_76': 'IO', 'TRA_79': 'INO', 'TRA_78': 'OIO', 'NO2': 'NO2', 'NO3': 'NO3', 'N2O5': 'N2O5', 'H2O2': 'H2O2', 'GMAO_VWND': 'GMAO_VWND', 'PAN': 'PAN', 'GMAO_TEMP': 'GMAO_TEMP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_59': 'GLYC', 'TRA_58': 'HAC', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'NO': 'NO', 'PMN': 'PMN', 'HNO3': 'HNO3', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_25': 'DMS', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'RO2': 'RO2', 'LON': 'LON', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'HO2': 'HO2', 'SO2': 'SO2', 'SO4': 'SO4', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'HNO2': 'HNO2', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'IONO', 'TRA_81': 'IONO2', 'TRA_82': 'I2O2', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'TRA_86': 'EOH'},
        'TRA_spec_met_all_1.7_EOH': {'MAO3': 'MAO3', 'DHMOB': 'DHMOB', 'ETP': 'ETP', 'RCO3': 'RCO3', 'MO2': 'MO2', 'EOH': 'EOH', 'MVKN': 'MVKN', 'R4P': 'R4P', 'ISNP': 'ISNP', 'RB3P': 'RB3P', 'MGLY': 'MGLY', 'MAOPO2': 'MAOPO2', 'RIO2': 'RIO2', 'PMNN': 'PMNN', 'PP': 'PP', 'VRP': 'VRP', 'RP': 'RP', 'MRO2': 'MRO2', 'HC5': 'HC5', 'ATO2': 'ATO2', 'PYAC': 'PYAC', 'R4N1': 'R4N1', 'DIBOO': 'DIBOO', 'LISOPOH': 'LISOPOH', 'HO2': 'HO2', 'ETHLN': 'ETHLN', 'ISNOOB': 'ISNOOB', 'ISNOOA': 'ISNOOA', 'ROH': 'ROH', 'MAN2': 'MAN2', 'B3O2': 'B3O2', 'INPN': 'INPN', 'MACRN': 'MACRN', 'PO2': 'PO2', 'VRO2': 'VRO2', 'MRP': 'MRP', 'PRN1': 'PRN1', 'ISNOHOO': 'ISNOHOO', 'MOBAOO': 'MOBAOO', 'MACRNO2': 'MACRNO2', 'ISOPND': 'ISOPND', 'HC5OO': 'HC5OO', 'ISOPNBO2': 'ISOPNBO2', 'RA3P': 'RA3P', 'ISOPNB': 'ISOPNB', 'ISOPNDO2': 'ISOPNDO2', 'PMNO2': 'PMNO2', 'IAP': 'IAP', 'MCO3': 'MCO3', 'IEPOXOO': 'IEPOXOO', 'MAOP': 'MAOP', 'INO2': 'INO2', 'OH': 'OH', 'PRPN': 'PRPN', 'GLYX': 'GLYX', 'A3O2': 'A3O2', 'ETO2': 'ETO2', 'R4O2': 'R4O2', 'ISN1': 'ISN1', 'KO2': 'KO2', 'ATOOH': 'ATOOH', 'GMAO_PSFC': 'GMAO_PSFC', 'GMAO_SURF': 'GMAO_SURF', 'GMAO_TEMP': 'GMAO_TEMP', 'GMAO_ABSH': 'GMAO_ABSH', 'GMAO_UWND': 'GMAO_UWND', 'GMAO_VWND': 'GMAO_VWND', 'TRA_9': 'ACET', 'TRA_8': 'H2O2', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'TRA_3': 'PAN', 'TRA_2': 'O3', 'TRA_1': 'NO', 'TRA_74': 'ICl', 'TRA_25': 'DMS', 'TRA_68': 'CH2I2', 'TRA_44': 'Br2', 'TRA_70': 'CH2IBr', 'TRA_22': 'N2O5', 'TRA_76': 'IO', 'TRA_79': 'INO', 'TRA_23': 'HNO4', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_21': 'C2H6', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'TRA_69': 'CH2ICl', 'TRA_50': 'BrNO3', 'TRA_39': 'DST2', 'TRA_38': 'DST1', 'TRA_73': 'IBr', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'TRA_32': 'NIT', 'TRA_77': 'HI', 'TRA_83': 'I2O3', 'TRA_55': 'ISOPN', 'TRA_54': 'MPN', 'TRA_72': 'I2', 'TRA_59': 'GLYC', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_20': 'CH2O', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'TRA_08': 'H2O2', 'TRA_09': 'ACET', 'TRA_75': 'I', 'TRA_28': 'SO4s', 'TRA_29': 'MSA', 'TRA_26': 'SO2', 'TRA_01': 'NO', 'TRA_02': 'O3', 'TRA_03': 'PAN', 'TRA_04': 'CO', 'TRA_05': 'ALK4', 'TRA_06': 'ISOP', 'TRA_07': 'HNO3', 'TRA_80': 'IONO', 'TRA_81': 'IONO2', 'TRA_82': 'I2O2', 'TRA_58': 'HAC', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'TRA_27': 'SO4', 'TRA_78': 'OIO', 'TRA_66': 'HNO2', 'TRA_71': 'HOI', 'TRA_24': 'MP', 'TRA_67': 'CH3IT'},
        'TRA_spec_met_all_1.7_EOH_no_trailing_zeroes':  {'MVKN': 'MVKN', 'ETP': 'ETP', 'MGLY': 'MGLY', 'EOH': 'EOH', 'TRA_17': 'R4N2', 'TRA_16': 'PPN', 'TRA_15': 'PMN', 'TRA_14': 'MACR', 'TRA_13': 'MVK', 'TRA_12': 'RCHO', 'TRA_11': 'ALD2', 'TRA_10': 'MEK', 'TRA_53': 'CH3Br', 'TRA_52': 'CH2Br2', 'TRA_51': 'CHBr3', 'TRA_50': 'BrNO3', 'TRA_57': 'PROPNN', 'TRA_56': 'MOBA', 'TRA_19': 'C3H8', 'TRA_18': 'PRPE', 'RIO2': 'RIO2', 'PYAC': 'PYAC', 'DHMOB': 'DHMOB', 'RP': 'RP', 'HC5OO': 'HC5OO', 'U10M': 'U10M', 'R4N1': 'R4N1', 'ISNOOB': 'ISNOOB', 'ETHLN': 'ETHLN', 'TRA_8': 'H2O2', 'GMAO_UWND': 'GMAO_UWND', 'GMAO_PSFC': 'GMAO_PSFC', 'MAN2': 'MAN2', 'TRA_32': 'NIT', 'B3O2': 'B3O2', 'TRA_59': 'GLYC', 'VRO2': 'VRO2', 'MRP': 'MRP', 'PRN1': 'PRN1', 'ISNOHOO': 'ISNOHOO', 'TRA_62': 'IEPOX', 'TRA_63': 'MAP', 'TRA_60': 'MMN', 'TRA_61': 'RIP', 'TRA_66': 'HNO2', 'TRA_67': 'CH3IT', 'TRA_64': 'NO2', 'TRA_65': 'NO3', 'TRA_68': 'CH2I2', 'TRA_69': 'CH2ICl', 'IAP': 'IAP', 'MCO3': 'MCO3', 'TRA_3': 'PAN', 'TRA_28': 'SO4s', 'GMAO_SURF': 'GMAO_SURF', 'OH': 'OH', 'PRPN': 'PRPN', 'TRA_27': 'SO4', 'TRA_24': 'MP', 'TRA_29': 'MSA', 'TRA_22': 'N2O5', 'TRA_23': 'HNO4', 'TRA_20': 'CH2O', 'TRA_21': 'C2H6', 'TRA_26': 'SO2', 'TRA_58': 'HAC', 'TRA_81': 'IONO2', 'GLYX': 'GLYX', 'R4P': 'R4P', 'MAO3': 'MAO3', 'TRA_25': 'DMS', 'TRA_77': 'HI', 'KO2': 'KO2', 'RCO3': 'RCO3', 'MO2': 'MO2', 'TRA2': 'O3', 'MACRNO2': 'MACRNO2', 'R4O2': 'R4O2', 'TRA_71': 'HOI', 'TRA_70': 'CH2IBr', 'TRA_73': 'IBr', 'TRA_72': 'I2', 'TRA_75': 'I', 'TRA_74': 'ICl', 'ISNP': 'ISNP', 'TRA_76': 'IO', 'TRA_79': 'INO', 'RB3P': 'RB3P', 'TRA_80': 'IONO', 'MAOPO2': 'MAOPO2', 'ROH': 'ROH', 'PMNN': 'PMNN', 'PP': 'PP', 'ISOPNDO2': 'ISOPNDO2', 'MRO2': 'MRO2', 'HC5': 'HC5', 'TRA_35': 'OCPI', 'TRA_34': 'BCPI', 'TRA_37': 'OCPO', 'TRA_36': 'BCPO', 'TRA_31': 'NH4', 'TRA_30': 'NH3', 'TRA_33': 'NITs', 'GMAO_VWND': 'GMAO_VWND', 'MACRN': 'MACRN', 'DIBOO': 'DIBOO', 'LISOPOH': 'LISOPOH', 'HO2': 'HO2', 'TRA_55': 'ISOPN', 'GMAO_ABSH': 'GMAO_ABSH', 'PRESS': 'PRESS', 'ATOOH': 'ATOOH', 'TRA8': 'H2O2', 'TRA_54': 'MPN', 'GMAO_TEMP': 'GMAO_TEMP', 'ISNOOA': 'ISNOOA', 'TRA_9': 'ACET', 'INPN': 'INPN', 'TRA_7': 'HNO3', 'TRA_6': 'ISOP', 'TRA_5': 'ALK4', 'TRA_4': 'CO', 'PO2': 'PO2', 'TRA_2': 'O3', 'TRA_1': 'NO', 'MOBAOO': 'MOBAOO', 'ISOPND': 'ISOPND', 'VRP': 'VRP', 'TRA_48': 'HBr', 'TRA_49': 'BrNO2', 'RA3P': 'RA3P', 'ISOPNB': 'ISOPNB', 'TRA_44': 'Br2', 'TRA_45': 'Br', 'TRA_46': 'BrO', 'TRA_47': 'HOBr', 'TRA_40': 'DST3', 'TRA_41': 'DST4', 'TRA_42': 'SALA', 'TRA_43': 'SALC', 'IEPOXOO': 'IEPOXOO', 'MAOP': 'MAOP', 'INO2': 'INO2', 'TRA_38': 'DST1', 'A3O2': 'A3O2', 'ETO2': 'ETO2', 'ISOPNBO2': 'ISOPNBO2', 'ATO2': 'ATO2', 'TRA_82': 'I2O2', 'TRA_83': 'I2O3', 'TRA_84': 'I2O4', 'TRA_85': 'AERI', 'ISN1': 'ISN1', 'TRA_78': 'OIO', 'TRA_39': 'DST2', 'PMNO2': 'PMNO2'},
        # Reduced output for EU grid
        'red_specs_f_name': [ \
            'O3', 'NO2', 'NO', 'NO3', 'N2O5', 'HNO4', 'HNO3', 'HNO2', 'PAN', \
            'PPN', 'PMN', 'H2O2', 'HO2', 'OH', 'RO2', 'SO2', 'SO4', \
            'GMAO_TEMP', 'GMAO_UWND', 'GMAO_VWND', 'I2', 'HOI', \
            'IO', 'I', 'HI', 'OIO', 'INO', 'IONO', 'IONO2', 'I2O2', 'I2O4', 'I2O3',\
            'CH3IT', 'CH2I2', 'CH2ICl', 'CH2IBr'],
        # Photolysis/Fast-J
        'FastJ_lower': [ \
            289.0, 298.25, 307.45, 312.45, 320.3, 345.0, 412.45],
        'FastJ_upper': [\
            298.25, 307.45, 312.45, 320.3, 345.0, 412.45, 850.0],
        'FastJ_mids':  [294, 303, 310, 316, 333, 380, 574],
        # ---  OH loss reactions
        'OH_loss_rxns_1.6': [ \
            'LO3_02', 'LR86', \
            'LR96', 'LR89', 'LR87', 'LR88', 'LR84', 'LR79', 'LR94',\
            'PO3_91', 'LR41', 'LR81', 'LR10', 'LR76', 'LR91', 'LR93', \
            'LR92', 'LR40', 'LR77', 'LR85', 'LR82', 'PO3_86', 'LR74',\
            'LR4', 'LO3_78', 'LR78', 'PO3_67', 'PO3_92', 'RD08', 'LR75', \
            'PO3_01', 'RD07', 'LR9', 'LR62', 'LR37', 'LR73', 'LR19', 'LO3_79', \
            'RD15', 'PO3_68', 'RD06', 'LO3_80', 'LR83', 'LR80', 'LR99', \
        ],
        'OH_loss_rxns': [ \
            'LR100', 'LR101', 'LR97', 'LR102', 'LO3_02', 'LR86', \
            'LR96', 'LR89', 'LR87', 'LR88', 'LR84', 'LR79', 'LR94',\
            'PO3_91', 'LR41', 'LR81', 'LR10', 'LR76', 'LR91', 'LR93', \
            'LR92', 'LR40', 'LR77', 'LR85', 'LR82', 'PO3_86', 'LR74',\
            'LR4', 'LO3_78', 'LR78', 'PO3_67', 'PO3_92', 'RD08', 'LR75', \
            'PO3_01', 'RD07', 'LR9', 'LR62', 'LR37', 'LR73', 'LR19', 'LO3_79', \
            'RD15', 'PO3_68', 'RD06', 'LO3_80', 'LR83', 'LR80', 'LR99', \
            # LR125 is the tag for ALD2 (hash out for runs without this tag)
            #    'LR125'
        ],
        # not outputted by p/l ( but should be) : 'PO3_103', 'PO3_104', 'PO3_105',
        # 'PO3_10'
        'Br_ox_org_rxns':  ['LR12', 'LR13', 'LR14', 'LR15', 'LR16'],
        'ClO_ox_org_rxns': ['LO3_83'],
        'OH_loss_rxns4cl_comp': [
        ],
        'Cl_ox_org_rxns': [
            'LR63', 'LR51', 'LR54', 'LR59', 'LR52', 'LR64', 'LR58', 'LR57', 'LR50', \
            'LR60', 'LR53', 'LR55', 'LR49', 'LR56', 'LR123', 'LR122'],
        'ClO_ox': [
            'LR68', 'LR61', 'LR69', 'LR74', 'LR48', 'LR73', 'LR70',
        ],
        'ClHOx': ['LR67',  'LR66', 'LR61',  'PO3_106', 'LR65'],
        'ClNOx': ['LR68', 'LR69', 'LR48'],
    }

    if rtn_dict:
        return GC_var_dict
    else:
        return GC_var_dict[input_x]


def get_ref_spec(spec='LIOx'):
    """
    Store of reference species for families

    Parameters
    ----------
    spec (str): species/tracer/variable name

    Returns
    -------
    ref_spec (str) reference species for a given family

    Notes
    -----
    This is for use in conbination  with functions that calculate relative values
    (e.g. in units of Ox, I, etc)
    """
    d = {
        'Cly': 'Cl',
        'Cl': 'Cl',
        'LOx': 'O3',
        'POx': 'O3',
        'LOX': 'O3',
        'POX': 'O3',
        'LIOx': 'I',
        'PIOx': 'I',
        'PClOx': 'Cl',
        'LClOx': 'Cl',
        'PClOxI': 'Cl',
        'LClOxI': 'Cl',
        'PClOxII': 'Cl',
        'LClOxII': 'Cl',
        'PClOxI': 'Cl',
        'LCI': 'Cl',
        'LCII': 'Cl',
        'PBrOx': 'Br',
        'LBrOx': 'Br',
        'Br': 'Br',
        'Bry': 'Br',
        'I': 'I',
        'Iy': 'I',
        'IxOy': 'I',
        'SO4': 'S',
        'NIT': 'N',
        'NH4': 'N',
    }
    return d[spec]
