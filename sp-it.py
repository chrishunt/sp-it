#!/usr/bin/env python

from pedalboard import load_plugin
from pedalboard.io import AudioFile
import subprocess
import os
import re
import sys
import ffmpeg
import json
import argparse

# Bump for new release.
VERSION='1.0'

# Audio files will be re-sampled and written in this sample rate when not
# specified.
DEFAULT_SAMPLE_RATE_HZ = 44100

# Audio files will be normalized to this peak dB.
NORMALIZATION_PEAK_DB = 0.5

parser = argparse.ArgumentParser(
    description=f'Each .wav audio file is re-sampled, processed with the VST, then normalized to at least -{NORMALIZATION_PEAK_DB}dB.',
)

parser.add_argument('--version', action='version', version=f'%(prog)s v{VERSION}')
parser.add_argument('--input', required=True, action='extend', nargs="+", type=str, help='audio .wav file(s) to process (example: \'/foo/bar.wav\' \'/baz/buz.wav\')')
parser.add_argument('--vst', required=True, help='file path to VST effect (example: \'/foo/bar/my-vst.vst3\')')
parser.add_argument('--vst-parameters', type=json.loads, help='parameters for vst plugin in json format (example: \'{"foo":"bar", "baz":"buz"}\')')
parser.add_argument('--sample-rate-hz', default=DEFAULT_SAMPLE_RATE_HZ, type=int, help='sample rate for processesing audio (default: %(default)s)')
parser.add_argument('--output', help='output directory (default: same directory as input file(s))')
args = parser.parse_args()

# Check that output directory exists, if specified
output_directory = args.output
if output_directory:
    if not os.path.isdir(output_directory):
        sys.exit(f"'{output_directory}' output directory does not exist")

# Check that VST exists
if not (os.path.isfile(args.vst) or os.path.isdir(args.vst)):
    sys.exit(f"'{args.vst}' vst does not exist")

# 1. Check that each input file exists.
# 2. Check that each input file has the extension .wav
# 3. Check that temporary and output files do not already exist.
# 4. Extract directories and filenames for processing.
wav_files = []
for filepath in args.input:
    if os.path.isfile(filepath):
        _root, ext = os.path.splitext(filepath)
        if ext.lower() == '.wav':
            input_directory, input_filename = os.path.split(filepath)

            wav_file = {
                'input_filename': input_filename,
                'temp_filename': f"temp-{input_filename}",
                'output_filename': f"sp-{input_filename}",
                'input_directory': input_directory,
                'output_directory': output_directory or input_directory,
            }

            for filename in [wav_file['temp_filename'], wav_file['output_filename']]:
                filepath = os.path.join(wav_file['output_directory'], filename)
                if os.path.isfile(filepath):
                    sys.exit(f"'{filepath}' already exists, delete to continue")

            wav_files.append(wav_file)
        else:
            sys.exit(f"'{filepath}' does not have the extension '.wav'")
    else:
        sys.exit(f"'{filepath}' is not a file")

# Load VST and check that parameters are valid
plugin = load_plugin(args.vst)
valid_parameters = plugin.parameters.keys()
for key in args.vst_parameters or {}:
    if key not in valid_parameters:
        sys.exit(f"'{key}' vst parameter is not a valid effect parameter.\nValid parameters: {valid_parameters}")
plugin = load_plugin(args.vst, args.vst_parameters)

for wav_file in wav_files:
    input_filename = wav_file['input_filename']
    input_file = os.path.join(wav_file['input_directory'], input_filename)
    temp_file = os.path.join(wav_file['output_directory'], wav_file['temp_filename'])
    output_file = os.path.join(wav_file['output_directory'], wav_file['output_filename'])

    # Process with VST audio plugin, write to temp file.
    with AudioFile(input_file).resampled_to(args.sample_rate_hz) as f:
        audio = f.read(f.frames)
    effected = plugin(audio, args.sample_rate_hz)
    with AudioFile(temp_file, 'w', args.sample_rate_hz, effected.shape[0]) as f:
        f.write(effected)

    # Get volume of temp file.
    ffmpeg_output = subprocess.Popen(
        (ffmpeg
         .input(temp_file)
         .filter_('volumedetect')
         .output('-', format='null')
         .compile()
         ),
        stderr=subprocess.PIPE
    ).communicate()[1].decode('utf-8')

    for line in ffmpeg_output.splitlines():
        max_volume = re.compile('max_volume: -?(.+) dB').search(line)
        if max_volume:
            gain = round(float(max_volume.group(1)) - NORMALIZATION_PEAK_DB, 1)
            if gain > 0:
                print(f"{input_filename}: Increasing volume by {str(gain)} dB.")
                _ffmpeg_output = subprocess.Popen(
                    (ffmpeg
                        .input(temp_file)
                        .filter_('volume', '+' + str(gain) + 'dB')
                        .output(output_file)
                        .compile()
                     ),
                    stderr=subprocess.PIPE
                ).communicate()[1].decode('utf-8')
                os.remove(temp_file)
            elif gain == -NORMALIZATION_PEAK_DB:
                print(f"{input_filename}: Volume is at 0dB, audio might be clipped.")
                os.rename(temp_file, output_file)
            else:
                print(f"{input_filename}: Volume is already good.")
                os.rename(temp_file, output_file)
            break
