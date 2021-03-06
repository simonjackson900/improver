#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017-2019 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Script to convert from probabilities to ensemble realization data."""

from iris.exceptions import CoordinateNotFoundError
from improver.argparser import ArgParser
from improver.ensemble_copula_coupling.ensemble_copula_coupling import (
    GeneratePercentilesFromProbabilities, RebadgePercentilesAsRealizations,
    EnsembleReordering)
from improver.utilities.load import load_cube
from improver.utilities.save import save_netcdf


def main(argv=None):
    """Convert from probabilities to ensemble realizations via a CLI."""

    cli_specific_arguments = [
        (['--no_of_realizations'],
         {'metavar': 'NUMBER_OF_REALIZATIONS', 'default': None, 'type': int,
          'help': (
              "Optional definition of the number of ensemble realizations to "
              "be generated. These are generated through an intermediate "
              "percentile representation. These percentiles will be "
              "distributed regularly with the aim of dividing into blocks of "
              "equal probability. If the reordering option is specified and "
              "the number of realizations is not given then the number of "
              "realizations is taken from the number of realizations in the "
              "raw forecast NetCDF file.")
          })]

    cli_definition = {'central_arguments': ('input_file', 'output_file'),
                      'specific_arguments': cli_specific_arguments,
                      'description': ('Convert a dataset containing '
                                      'probabilities into one containing '
                                      'ensemble realizations.')}
    parser = ArgParser(**cli_definition)
    # add mutually exclusive options rebadge and reorder.
    # If reordering add option for raw ensemble - raise error if
    # raw ens missing.
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--reordering', default=False, action='store_true',
                       help='The option used to create ensemble realizations '
                       'from percentiles by reordering the input '
                       'percentiles based on the order of the '
                       'raw ensemble forecast.')
    group.add_argument('--rebadging', default=False, action='store_true',
                       help='The option used to create ensemble realizations '
                       'from percentiles by rebadging the input '
                       'percentiles.')

    # If reordering, we need a raw ensemble forecast.
    reordering = parser.add_argument_group(
        'Reordering options', 'Options for reordering the input percentiles '
        'using the raw ensemble forecast as required to create ensemble '
        'realizations.')
    reordering.add_argument('--raw_forecast_filepath',
                            metavar='RAW_FORECAST_FILE',
                            help='A path to an raw forecast NetCDF file to be '
                            'processed. This option is compulsory, if the '
                            'reordering option is selected.')
    reordering.add_argument(
        '--random_seed', default=None,
        help='Option to specify a value for the random seed for testing '
             'purposes, otherwise, the default random seed behaviour is '
             'utilised. The random seed is used in the generation of the '
             'random numbers used for splitting tied values '
             'within the raw ensemble, so that the values from the input '
             'percentiles can be ordered to match the raw ensemble.')
    reordering.add_argument(
        '--ecc_bounds_warning', default=False, action='store_true',
        help='If True, where percentiles (calculated as an intermediate '
             'output before realizations) exceed the ECC bounds range, raise '
             'a warning rather than an exception.')

    args = parser.parse_args(args=argv)

    # CLI argument checking:
    # Can only do one of reordering or rebadging: if options are passed which
    # correspond to the opposite method, raise an exception.
    # Note: Shouldn't need to check that both/none are set, since they are
    # defined as mandatory, but mutually exclusive, options.
    if args.rebadging:
        if ((args.raw_forecast_filepath is not None) or
                (args.random_seed is not None)):
            parser.wrong_args_error(
                'raw_forecast_filepath, random_seed', 'rebadging')

    # Process the data
    cube = load_cube(args.input_filepath)

    if args.reordering:
        if args.raw_forecast_filepath is None:
            message = ("You must supply a raw forecast filepath if using the "
                       "reordering option.")
            raise ValueError(message)
        else:
            raw_forecast = load_cube(args.raw_forecast_filepath)
            try:
                raw_forecast.coord("realization")
            except CoordinateNotFoundError:
                message = ("The netCDF file from the raw_forecast_filepath "
                           "must have a realization coordinate.")
                raise ValueError(message)

        no_of_realizations = args.no_of_realizations
        # If no_of_realizations is not given, take the number from the raw
        # ensemble cube.
        if args.no_of_realizations is None:
            no_of_realizations = len(raw_forecast.coord("realization").points)

        cube = GeneratePercentilesFromProbabilities(
            ecc_bounds_warning=args.ecc_bounds_warning).process(
                cube, no_of_percentiles=no_of_realizations)
        cube = EnsembleReordering().process(
            cube, raw_forecast, random_ordering=False,
            random_seed=args.random_seed)
    elif args.rebadging:
        cube = GeneratePercentilesFromProbabilities(
            ecc_bounds_warning=args.ecc_bounds_warning).process(
                cube, no_of_percentiles=args.no_of_realizations)
        cube = RebadgePercentilesAsRealizations().process(cube)

    save_netcdf(cube, args.output_filepath)


if __name__ == '__main__':
    main()
