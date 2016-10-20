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
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

ifneq ($(MAKECMDGOALS),clean)
  ifeq   (0,$(shell which pyrcc4     >/dev/null 2>&1; echo $$?))
    RCC = pyrcc4
  else
    ifeq (0,$(shell which pyside-rcc >/dev/null 2>&1; echo $$?))
      RCC = pyside-rcc
    else
      $(error "resource compiler not found")
    endif
  endif
endif

resources.py: resources.qrc
	$(RCC) -py3 -o $@ $<

.PHONY: clean
clean:
	rm -f resources.py
