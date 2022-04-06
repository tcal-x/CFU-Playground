#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
from litex.soc.integration import builder
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import soc_core
from litex.soc.cores.cpu.vexriscv import core
from litex.soc.cores.spi import SPIMaster
from litex.build.generic_platform import Subsignal, Pins, IOStandard, Misc

from typing import Callable
from patch_cpu_variant import patch_cpu_variant, copy_cpu_variant_if_needed
from patch_cpu_variant import build_cpu_variant_if_needed
from dac import DAC



class GeneralSoCWorkflow():
    """Base class that implements general workflow for building/loading a SoC.

    For many boards this class is sufficient, but some boards will require
    a subclass that overrides one or more of the methods for designing,
    building, and loading the SoC.

    Attributes:
        args: An argparse Namespace that holds SoC and build options.
        soc_constructor: The constructor for the LiteXSoC.
        builder_constructor: The constructor for the LiteX Builder.
    """
    def __init__(
        self,
        args: argparse.Namespace,
        soc_constructor: Callable[..., litex_soc.LiteXSoC],
        builder_constructor: Callable[..., builder.Builder] = None,
    ) -> None:
        """Initializes the GeneralSoCWorkflow.
        
        Args:
            args: An argparse Namespace that holds SoC and build options.
            soc_constructor: The constructor for the LiteXSoC.
            builder_constructor: The constructor for the LiteX Builder. If
              omitted, litex.soc.integration.builder.Builder will be used.
        """
        self.args = args
        self.soc_constructor = soc_constructor
        self.builder_constructor = builder_constructor or builder.Builder
        patch_cpu_variant()


    def add_mic3_to_soc(self, soc, pmod = "PMOD1A"):
        mic3_spi_d = [
            ("mic3_spi", 0,
                Subsignal("cs_n",  Pins(f"{pmod}:0")),
                Subsignal("mosi",  Pins(f"{pmod}:1")),
                Subsignal("miso",  Pins(f"{pmod}:2")),
                Subsignal("clk",   Pins(f"{pmod}:3")),
                IOStandard("LVCMOS33"),
                Misc("SLEW=FAST"),
            )
        ]
        soc.platform.add_extension(mic3_spi_d)
        pads = soc.platform.request("mic3_spi")
        soc.submodules.mic3_spi = SPIMaster(pads, 16, soc.sys_clk_freq, 20e6)
        soc.mic3_spi.add_clk_divider()


    def add_dac_to_soc(self, soc, pmod = "PMOD1B"):
        dac_d = [ (pmod, 0, Pins(f"{pmod}:0"), IOStandard("LVCMOS33")) ]
        soc.platform.add_extension(dac_d)
        #self.platform.add_extension(icebreaker.raw_pmod_io("PMOD1B"))
        outsig = soc.platform.request(pmod)[0]
        soc.submodules.dac = DAC(outsig, 12)


    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        """Utilizes self.soc_constructor to make a LiteXSoC.
        
        Args:
            **kwargs: Arguments meant to extend/overwrite the general
              arguments to self.soc_constructor.
        
        Returns:
            The LiteXSoC for the target board.
        """
        base_soc_kwargs = {
            'with_ethernet': self.args.with_ethernet,
            'with_etherbone': self.args.with_etherbone,
            'with_mapped_flash': self.args.with_mapped_flash,
            'with_spi_sdcard': self.args.with_spi_sdcard,
            'with_video_framebuffer': self.args.with_video_framebuffer,
        }
        base_soc_kwargs.update(soc_core.soc_core_argdict(self.args))
        if self.args.toolchain:
            base_soc_kwargs['toolchain'] = self.args.toolchain
        if self.args.sys_clk_freq:
            base_soc_kwargs['sys_clk_freq'] = self.args.sys_clk_freq

        print("make_soc: cpu_variant is", self.args.cpu_variant)
        build_cpu_variant_if_needed(self.args.cpu_variant)

        base_soc_kwargs.update(kwargs)
        this_soc_constructor = self.soc_constructor
        print("TJC Soc constructor is ", this_soc_constructor)
        soc = this_soc_constructor(**base_soc_kwargs)
        print("TJC Soc is ", soc)
        soc_ident = soc.identifier.get_memories()[0][1].init
        soc_ident_str = ''.join(map(chr, soc_ident))
        print("TJC Soc ident is ", soc_ident)
        print("TJC Soc ident is ", soc_ident_str)
        print("TJC Soc submodules ", soc.submodules)
        if "Arty" in soc_ident_str:
            print("Setting up stuff for Arty")
            self.add_mic3_to_soc(soc, pmod="pmodd")
            self.add_dac_to_soc(soc, pmod="pmodb")
        elif "iCEBreaker" in soc_ident_str:
            print("Setting up stuff for icebreaker")
            self.add_mic3_to_soc(soc, pmod="PMOD1A")
            self.add_dac_to_soc(soc, pmod="PMOD1B")
        else:
            print("Setting up stuff for unknown")
            self.add_mic3_to_soc(soc)
            self.add_dac_to_soc(soc)
        print("kwargs", kwargs)
        print("base_soc_kwargs", base_soc_kwargs)
        return soc

    def build_soc(self, soc: litex_soc.LiteXSoC, **kwargs) -> builder.Builder:
        """Creates a LiteX Builder and builds the Soc if self.args.build.
        
        Args:
            soc: The LiteXSoC meant to be built.
            **kwargs: Arguments meant to extend/overwrite the general
              arguments to the LiteX Builder.

        Returns:
            The LiteX Builder for the SoC.
        """
        copy_cpu_variant_if_needed(self.args.cpu_variant)
        soc_builder = self.builder_constructor(
            soc, **builder.builder_argdict(self.args))
        soc_builder.build(run=self.args.build, **kwargs)
        return soc_builder

    def load(self, soc: litex_soc.LiteXSoC,
             soc_builder: builder.Builder) -> None:
        """Loads a SoC onto the target board.
        
        Args:
            soc: The LiteXSoc meant to be loaded.
            soc_builder: The LiteX builder used to build the SoC.
        """
        prog = soc.platform.create_programmer()
        bitstream_filename = self.format_bitstream_filename(
            soc_builder.gateware_dir, soc.build_name)
        prog.load_bitstream(bitstream_filename)

    @classmethod
    def format_bitstream_filename(cls, directory: str, build_name: str) -> str:
        return os.path.join(directory, f'{build_name}.bit')

    def run(self) -> None:
        """Runs the workflow in order (make_soc -> build_soc -> load)."""
        soc = self.make_soc()
        soc_builder = self.build_soc(soc)
        if self.args.load:
            self.load(soc, soc_builder)

    def software_load(self, filename: str) -> None:
        """Perform software loading procedures.
        
        For boards that use serialboot, this can be a no-op.

        Args:
            filename: The name of the software file to load on the board.
        """
        pass  # Most boards can use serialboot.
