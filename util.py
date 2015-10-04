##
## This file is part of the sigrok-meter project.
##
## Copyright (C) 2015 Jens Steinhauser <jens.steinhauser@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
##

import sigrok.core as sr

def format_unit(u):
    units = {
        sr.Unit.VOLT:                   'V',
        sr.Unit.AMPERE:                 'A',
        sr.Unit.OHM:                   u'\u03A9',
        sr.Unit.FARAD:                  'F',
        sr.Unit.KELVIN:                 'K',
        sr.Unit.CELSIUS:               u'\u00B0C',
        sr.Unit.FAHRENHEIT:            u'\u00B0F',
        sr.Unit.HERTZ:                  'Hz',
        sr.Unit.PERCENTAGE:             '%',
      # sr.Unit.BOOLEAN
        sr.Unit.SECOND:                 's',
        sr.Unit.SIEMENS:                'S',
        sr.Unit.DECIBEL_MW:             'dBm',
        sr.Unit.DECIBEL_VOLT:           'dBV',
      # sr.Unit.UNITLESS
        sr.Unit.DECIBEL_SPL:            'dB',
      # sr.Unit.CONCENTRATION
        sr.Unit.REVOLUTIONS_PER_MINUTE: 'rpm',
        sr.Unit.VOLT_AMPERE:            'VA',
        sr.Unit.WATT:                   'W',
        sr.Unit.WATT_HOUR:              'Wh',
        sr.Unit.METER_SECOND:           'm/s',
        sr.Unit.HECTOPASCAL:            'hPa',
        sr.Unit.HUMIDITY_293K:          '%rF',
        sr.Unit.DEGREE:                u'\u00B0',
        sr.Unit.HENRY:                  'H'
    }

    return units.get(u, '')

def quantity_from_unit(u):
    quantities = {
        sr.Unit.VOLT:                   'Voltage',
        sr.Unit.AMPERE:                 'Current',
        sr.Unit.OHM:                    'Resistance',
        sr.Unit.FARAD:                  'Capacity',
        sr.Unit.KELVIN:                 'Temperature',
        sr.Unit.CELSIUS:                'Temperature',
        sr.Unit.FAHRENHEIT:             'Temperature',
        sr.Unit.HERTZ:                  'Frequency',
        sr.Unit.PERCENTAGE:             'Duty Cycle',
        sr.Unit.BOOLEAN:                'Continuity',
        sr.Unit.SECOND:                 'Time',
        sr.Unit.SIEMENS:                'Conductance',
        sr.Unit.DECIBEL_MW:             'Power Ratio',
        sr.Unit.DECIBEL_VOLT:           'Voltage Ratio',
        sr.Unit.UNITLESS:               'Unitless Quantity',
        sr.Unit.DECIBEL_SPL:            'Sound Pressure',
        sr.Unit.CONCENTRATION:          'Concentration',
        sr.Unit.REVOLUTIONS_PER_MINUTE: 'Revolutions',
        sr.Unit.VOLT_AMPERE:            'Apparent Power',
        sr.Unit.WATT:                   'Power',
        sr.Unit.WATT_HOUR:              'Energy',
        sr.Unit.METER_SECOND:           'Velocity',
        sr.Unit.HECTOPASCAL:            'Pressure',
        sr.Unit.HUMIDITY_293K:          'Humidity',
        sr.Unit.DEGREE:                 'Angle',
        sr.Unit.HENRY:                  'Inductance'
    }

    return quantities.get(u, '')
