#!/usr/bin/python

import sys
import subprocess
import argparse
import os
import shutil

parser = argparse.ArgumentParser(description='Replace abisonic and/or atmos audio')
parser.add_argument('-i_bf', help='4ch b-format wav (WXYZ)', required=False)
parser.add_argument('-ambix', action='store_true', help='convert i_bf to WYZX, SN3D normalization', required=False)
parser.add_argument('-i_ec3', help='DD+ JOC ATMOS stream', required=False)
parser.add_argument('-i_mp4', nargs='+', help='videos to replace')
parser.add_argument('-offset', help='offset', default=0.0, type=float)
parser.add_argument('-yt360', action='store_true', help='convert audio to ambix format and package in mov container', required=False)
args = parser.parse_args()

tmpdir = 'replace-audio-temp'

def shell( args ):
    try:
        output = subprocess.check_output(args)
        print output
        return output
    except subprocess.CalledProcessError as e:
        print e.output
        print '*** ERROR %d ***' % e.returncode
        exit()

def usage():
    print "usage: replace-audio-multi.py -i_bf <in.wav> -i_ec3 <in.ec3> [<in_mp4> ...] -i_mp4 <out.mp4>"

def cleanup():
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)

def main():
    print ''
    if args.i_bf:
        print 'replacing with b-format: %s' % args.i_bf

    if args.i_ec3:
        print 'adding ec3: %s' % args.i_ec3

    if args.i_ec3 == None and args.i_bf == None:
        print 'no input audio specified'
        usage()
        exit()

    print ''

    if args.i_mp4 > 0:
        print 'input videos:'
        for v in args.i_mp4:
            print v

    cleanup()

    if not os.path.exists(tmpdir):
        os.mkdir(tmpdir)

    ambifiles = []
    if args.i_bf:

        if args.ambix:
            ext = os.path.splitext(args.i_bf)[1]
            ambix = os.path.splitext(args.i_bf)[0] + '-ambix' + ext
            shell(['ffmpeg', '-ss', str(args.offset), '-i', args.i_bf, \
            '-af', 'pan=0x107:c0=c0:c1=0.707946*c2:c2=0.707946*c3:c3=0.707946*c1', \
            '-codec', 'copy', '-acodec', 'pcm_s16le', '-ac', '4', ambix])
            cleanup()
            print 'wrote ', ambix
            exit()

        if args.yt360:
            for v in args.i_mp4:
                name = os.path.basename(v)
                name = os.path.splitext(name)[0]
                ext = os.path.splitext(v)[1]
                noaudio = tmpdir + '/' + name + '-noaudio' + ext
                shell(['ffmpeg', '-i', v, '-codec', 'copy', '-an', noaudio])
                out = os.path.splitext(v)[0] + '-yt360' + '.mov'
                shell(['ffmpeg', '-ss', str(args.offset), \
                    '-i', args.i_bf, \
                    '-i', noaudio, \
                    '-af', 'pan=0x107:c0=c0:c1=0.707946*c2:c2=0.707946*c3:c3=0.707946*c1', \
                    '-codec', 'copy', '-acodec', 'pcm_s16le', '-ac', '4', out])
            cleanup()
            print 'wrote ', out
            exit()

        shell(['ffmpeg', '-ss', str(args.offset), '-i', args.i_bf, \
            '-map_channel', '0.0.0', tmpdir+'/1.wav', \
            '-map_channel', '0.0.1', tmpdir+'/2.wav', \
            '-map_channel', '0.0.2', tmpdir+'/3.wav', \
            '-map_channel', '0.0.3', tmpdir+'/4.wav'])

        shell(['ffmpeg', '-i', tmpdir+'/1.wav','-i', tmpdir+'/2.wav', \
            '-filter_complex', '[0:a][1:a]amerge[aout]', \
            '-map', '[aout]', tmpdir+'/12.wav'])

        shell(['ffmpeg', '-i', tmpdir+'/3.wav','-i', tmpdir+'/4.wav', \
            '-filter_complex', '[0:a][1:a]amerge[aout]', \
            '-map', '[aout]', tmpdir+'/34.wav'])

        for v in args.i_mp4:
            name = os.path.basename(v)
            name = os.path.splitext(name)[0]
            ext = os.path.splitext(v)[1]
            noaudio = tmpdir + '/' + name + '-noaudio' + ext
            shell(['ffmpeg', '-i', v, '-codec', 'copy', '-an', noaudio])
            out = os.path.splitext(v)[0] + '-ambi' + ext
            shell(['ffmpeg', '-i', noaudio, '-i', tmpdir+'/12.wav', '-i', tmpdir+'/34.wav', \
                '-map', '0', '-map', '1', '-map', '2', \
                '-codec', 'copy', '-acodec', 'libfdk_aac', \
                '-movflags', 'faststart', \
                '-strict', '-2', '-ab', '320k', '-ac', '2', \
                '-shortest', '-y', out])
            ambifiles.append(out)

    ddpFiles = []
    if args.i_ec3:
        files = args.i_mp4
        if len(ambifiles) > 0:
            files = ambifiles
        for v in files:
            ext = os.path.splitext(v)[1]
            out = os.path.splitext(v)[0] + '-ddp' + ext
            shell(['ffmpeg', '-i', v, \
                '-ss', str(args.offset), \
                '-i', args.i_ec3, \
                '-map', '0', '-map', '1', \
                '-codec', 'copy', '-acodec', 'copy', out])
            ddpFiles.append(out)

    if len(ambifiles) > 0 or len(ddpFiles) > 0:
        print 'wrote'

    for v in ambifiles:
        print v
    for v in ddpFiles:
        print v


    cleanup()
       
if __name__ == "__main__":
    main()