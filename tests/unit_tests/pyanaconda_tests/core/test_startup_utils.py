#
# Copyright (C) 2021  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Test code from the startup_utils.py. Most of the parts are not
# easy to test but we can try to improve that.
#

import unittest

from unittest.mock import patch, mock_open, Mock
from textwrap import dedent

from pyanaconda.startup_utils import print_dracut_errors, check_if_geolocation_should_be_used


class StartupUtilsTestCase(unittest.TestCase):

    def test_print_dracut_errors(self):
        logger_mock = Mock()

        with patch("pyanaconda.startup_utils.open", mock_open(read_data="test text")) as m:
            print_dracut_errors(logger_mock)

            m.assert_called_once_with("/run/anaconda/initrd_errors.txt", "rt")

            logger_mock.warning.assert_called_once_with(
                dedent("""
                ############## Installer errors encountered during boot ##############
                test text
                ############ Installer errors encountered during boot end ############"""))

    @patch("pyanaconda.core.constants.DRACUT_ERRORS_PATH", "None")
    def test_print_dracut_errors_missing_file(self):
        logger_mock = Mock()
        print_dracut_errors(logger_mock)
        logger_mock.assert_not_called()

    @patch("pyanaconda.startup_utils.flags")
    @patch("pyanaconda.startup_utils.conf")
    def test_geoloc_check(self, conf_mock, flags_mock):
        """Test check_if_geolocation_should_be_used()

        This is a nasty function that actually takes 4 different "inputs". It is not possible to
        express these 16 combinations in a readable way, so pay attention to coverage - all code
        paths should be tested.
        """
        opts_mock = Mock()

        # dirinstall or image install
        flags_mock.automatedInstall = False
        conf_mock.target.is_hardware = False  # this causes False
        opts_mock.geoloc = None
        opts_mock.geoloc_use_with_ks = None
        assert check_if_geolocation_should_be_used(opts_mock) is False

        # kickstart
        flags_mock.automatedInstall = True  # this causes False
        conf_mock.target.is_hardware = True
        opts_mock.geoloc = None
        opts_mock.geoloc_use_with_ks = None
        assert check_if_geolocation_should_be_used(opts_mock) is False

        # kickstart + enable option
        flags_mock.automatedInstall = True  # this causes False
        conf_mock.target.is_hardware = True
        opts_mock.geoloc = None
        opts_mock.geoloc_use_with_ks = True  # this overrides it to True
        assert check_if_geolocation_should_be_used(opts_mock) is True

        # disabled by option
        flags_mock.automatedInstall = False
        conf_mock.target.is_hardware = True
        opts_mock.geoloc = "0"  # this causes False
        opts_mock.geoloc_use_with_ks = None
        assert check_if_geolocation_should_be_used(opts_mock) is False

        # enabled by option value
        flags_mock.automatedInstall = False
        conf_mock.target.is_hardware = True
        opts_mock.geoloc_use_with_ks = None
        for value in ("1", "yes", "whatever", "I typed here something"):  # anything causes True
            opts_mock.geoloc = value
            assert check_if_geolocation_should_be_used(opts_mock) is True

        # normal install without boot options defaults to True
        flags_mock.automatedInstall = False
        conf_mock.target.is_hardware = True
        opts_mock.geoloc = None
        opts_mock.geoloc_use_with_ks = None
        assert check_if_geolocation_should_be_used(opts_mock) is True
