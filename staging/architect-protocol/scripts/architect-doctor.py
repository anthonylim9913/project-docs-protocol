#!/usr/bin/env python3
"""Read-only schema-2 Architect lifecycle and evidence identity checks."""
import argparse
from pathlib import Path
from architect_packet import Invalid, validate


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    parser.add_argument('--packet-dir',default='docs/architect',help='project-relative packet directory')
    parser.add_argument('--structural-example',action='store_true',help='explicit non-production example only')
    args=parser.parse_args(argv)
    try:
        print(validate(args.root,args.packet_dir,args.structural_example))
        return 0
    except (OSError,UnicodeError,ValueError,NotImplementedError) as error:
        print('FAIL architect: '+str(error))
        return 1


if __name__=='__main__':raise SystemExit(main())
