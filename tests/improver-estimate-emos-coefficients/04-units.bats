#!/usr/bin/env bats
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

. $IMPROVER_DIR/tests/lib/utils

@test "estimate-emos-coefficients in prescribed units that may not match inputs" {
  improver_check_skip_acceptance
  KGO="estimate-emos-coefficients/gaussian/kgo.nc"

  # Estimate the EMOS coefficients and check that they match the kgo.
  run improver estimate-emos-coefficients 'gaussian' '20170605T0300Z' --units 'K' \
      "$IMPROVER_ACC_TEST_DIR/ensemble-calibration/gaussian/history/*.nc" \
      "$IMPROVER_ACC_TEST_DIR/ensemble-calibration/gaussian/truth/*.nc" \
      "$TEST_DIR/output.nc" --max_iterations 600
  [[ "$status" -eq 0 ]]

  improver_check_recreate_kgo "output.nc" $KGO

  # Run nccmp to compare the output and kgo realizations and check it passes.
  improver_compare_output_lower_precision "$TEST_DIR/output.nc" \
      "$IMPROVER_ACC_TEST_DIR/$KGO"
}
