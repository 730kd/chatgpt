"""USB Audio descriptor parser (UAC1/UAC2-oriented, lightweight).

Usage:
    python usb_audio_parser.py --hex "09 04 00 00 00 01 01 00 00 ..."
    python usb_audio_parser.py --file descriptors.bin

This parser focuses on USB interface + class-specific Audio descriptors and
prints a readable summary.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Any


# Standard descriptor types
DESC_TYPE_INTERFACE = 0x04
DESC_TYPE_ENDPOINT = 0x05
DESC_TYPE_CS_INTERFACE = 0x24
DESC_TYPE_CS_ENDPOINT = 0x25

# Audio Interface Subclasses
AUDIO_SUBCLASS_CONTROL = 0x01
AUDIO_SUBCLASS_STREAMING = 0x02
AUDIO_SUBCLASS_MIDI_STREAMING = 0x03


@dataclass
class Descriptor:
    offset: int
    bLength: int
    bDescriptorType: int
    raw: bytes
    decoded: Dict[str, Any] = field(default_factory=dict)


class USBAudioParser:
    def __init__(self, data: bytes):
        self.data = data
        self.descriptors: List[Descriptor] = []

    def parse(self) -> List[Descriptor]:
        i = 0
        while i < len(self.data):
            if i + 2 > len(self.data):
                break

            b_length = self.data[i]
            b_type = self.data[i + 1]

            if b_length == 0:
                # Prevent infinite loop on malformed descriptor
                break

            if i + b_length > len(self.data):
                raw = self.data[i:]
                desc = Descriptor(
                    offset=i,
                    bLength=len(raw),
                    bDescriptorType=b_type,
                    raw=raw,
                    decoded={"error": "truncated descriptor"},
                )
                self.descriptors.append(desc)
                break

            raw = self.data[i : i + b_length]
            desc = Descriptor(offset=i, bLength=b_length, bDescriptorType=b_type, raw=raw)
            desc.decoded = self._decode_descriptor(raw)
            self.descriptors.append(desc)
            i += b_length

        return self.descriptors

    def _decode_descriptor(self, raw: bytes) -> Dict[str, Any]:
        b_type = raw[1]
        info: Dict[str, Any] = {}

        if b_type == DESC_TYPE_INTERFACE and len(raw) >= 9:
            info.update(
                {
                    "kind": "INTERFACE",
                    "bInterfaceNumber": raw[2],
                    "bAlternateSetting": raw[3],
                    "bNumEndpoints": raw[4],
                    "bInterfaceClass": raw[5],
                    "bInterfaceSubClass": raw[6],
                    "bInterfaceProtocol": raw[7],
                    "iInterface": raw[8],
                }
            )
            info["audio_subclass_name"] = self._audio_subclass_name(raw[6])

        elif b_type == DESC_TYPE_ENDPOINT and len(raw) >= 7:
            w_max_packet = raw[4] | (raw[5] << 8)
            info.update(
                {
                    "kind": "ENDPOINT",
                    "bEndpointAddress": raw[2],
                    "bmAttributes": raw[3],
                    "wMaxPacketSize": w_max_packet,
                    "bInterval": raw[6],
                }
            )

        elif b_type == DESC_TYPE_CS_INTERFACE and len(raw) >= 3:
            subtype = raw[2]
            info["kind"] = "CS_INTERFACE"
            info["bDescriptorSubtype"] = subtype
            info["subtype_name"] = self._cs_interface_subtype_name(subtype)

            # UAC Header (common layout for UAC1/2 differs slightly)
            if subtype == 0x01 and len(raw) >= 8:
                bcd_adc = raw[3] | (raw[4] << 8)
                info["bcdADC"] = f"0x{bcd_adc:04x}"

            # Input Terminal (uac1: 12+ bytes, uac2: usually longer)
            elif subtype == 0x02 and len(raw) >= 8:
                terminal_id = raw[3]
                w_terminal_type = raw[4] | (raw[5] << 8)
                assoc_terminal = raw[6]
                info.update(
                    {
                        "bTerminalID": terminal_id,
                        "wTerminalType": f"0x{w_terminal_type:04x}",
                        "bAssocTerminal": assoc_terminal,
                    }
                )
                if len(raw) >= 9:
                    info["bNrChannels_or_bCSourceID"] = raw[7]

            # Output Terminal
            elif subtype == 0x03 and len(raw) >= 9:
                info.update(
                    {
                        "bTerminalID": raw[3],
                        "wTerminalType": f"0x{(raw[4] | (raw[5] << 8)):04x}",
                        "bAssocTerminal": raw[6],
                        "bSourceID": raw[7],
                    }
                )

            # Feature Unit (basic)
            elif subtype == 0x06 and len(raw) >= 6:
                info.update(
                    {
                        "bUnitID": raw[3],
                        "bSourceID": raw[4],
                        "controls_bytes": list(raw[5:-1]) if len(raw) > 6 else [],
                        "iFeature": raw[-1],
                    }
                )

        elif b_type == DESC_TYPE_CS_ENDPOINT and len(raw) >= 3:
            info["kind"] = "CS_ENDPOINT"
            info["bDescriptorSubtype"] = raw[2]

        else:
            info["kind"] = "UNKNOWN_OR_UNSUPPORTED"

        return info

    @staticmethod
    def _audio_subclass_name(subcls: int) -> str:
        return {
            AUDIO_SUBCLASS_CONTROL: "AUDIOCONTROL",
            AUDIO_SUBCLASS_STREAMING: "AUDIOSTREAMING",
            AUDIO_SUBCLASS_MIDI_STREAMING: "MIDISTREAMING",
        }.get(subcls, "UNKNOWN")

    @staticmethod
    def _cs_interface_subtype_name(subtype: int) -> str:
        return {
            0x01: "HEADER",
            0x02: "INPUT_TERMINAL",
            0x03: "OUTPUT_TERMINAL",
            0x04: "MIXER_UNIT",
            0x05: "SELECTOR_UNIT",
            0x06: "FEATURE_UNIT",
            0x07: "PROCESSING_UNIT",
            0x08: "EXTENSION_UNIT",
            0x0A: "CLOCK_SOURCE (UAC2)",
        }.get(subtype, "UNKNOWN_SUBTYPE")


def parse_hex_string(hex_str: str) -> bytes:
    cleaned = hex_str.replace(" ", "").replace("\n", "").replace("\t", "")
    if len(cleaned) % 2 != 0:
        raise ValueError("hex string length must be even")
    return bytes.fromhex(cleaned)


def format_descriptor(desc: Descriptor) -> str:
    header = (
        f"@0x{desc.offset:04x} len={desc.bLength:02d} "
        f"type=0x{desc.bDescriptorType:02x} raw={desc.raw.hex()}"
    )
    detail = ", ".join(f"{k}={v}" for k, v in desc.decoded.items())
    return f"{header}\n  {detail}" if detail else header


def main() -> None:
    parser = argparse.ArgumentParser(description="USB Audio descriptor parser")
    parser.add_argument("--hex", dest="hex_string", help="Descriptor bytes in hex")
    parser.add_argument("--file", dest="file_path", help="Binary descriptor file")
    args = parser.parse_args()

    if not args.hex_string and not args.file_path:
        parser.error("one of --hex or --file is required")

    if args.hex_string:
        data = parse_hex_string(args.hex_string)
    else:
        with open(args.file_path, "rb") as f:
            data = f.read()

    usb_parser = USBAudioParser(data)
    descs = usb_parser.parse()

    print(f"Parsed {len(descs)} descriptor(s)")
    for d in descs:
        print(format_descriptor(d))


if __name__ == "__main__":
    main()
