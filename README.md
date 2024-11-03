# sp-it.py

## What is it?

This is a python CLI for processing one or more input .wav audio files with a
VST, then normalizing the audio output to peaks of -0.5dB.

## Why is it called `sp-it`?

This was written to make it easier to "sample" audio with a vintage sampler
using the [SP950][sp950] VST.

1. Gather all the audio we want to use for our song.
2. "Sample" the audio by running through `sp-it`.
3. Chop/mix the sampled audio, the color is baked in.

Later, we added the ability to load up any VST, but the `sp-it` name remains.

## Installation

Required:
- [pedalboard][pedalboard] - CLI VST host for applying effects to our input.
- [ffmpeg][ffmpeg] - CLI audio processing framework for normalizing our output.

```
$ brew install ffmpeg
$ pip install pedalboard ffmpeg-python
```

## Usage

```
$ ./sp-it.py --help
usage: sp-it.py [-h] [--version] --input INPUT [INPUT ...] --vst VST [--vst-parameters VST_PARAMETERS] [--sample-rate-hz SAMPLE_RATE_HZ] [--output OUTPUT]

Each .wav audio file is re-sampled, processed with the VST, then normalized to at least -0.5dB.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --input INPUT [INPUT ...]
                        audio .wav file(s) to process (example: '/foo/bar.wav' '/baz/buz.wav')
  --vst VST             file path to VST effect (example: '/foo/bar/my-vst.vst3')
  --vst-parameters VST_PARAMETERS
                        parameters for vst plugin in json format (example: '{"foo":"bar", "baz":"buz"}')
  --sample-rate-hz SAMPLE_RATE_HZ
                        sample rate for processesing audio (default: 44100)
  --output OUTPUT       output directory (default: same directory as input file(s))
```

## Example

Here's an example where we process two audio files with the [SP950][sp950] VST:

```
./sp-it.py \
  --input audio1.wav audio2.wav \
  --vst '/Library/Audio/Plug-Ins/VST/SP950.vst3' \
  --vst-parameters '{
      "bypass":false,
      "extended_range":false,
      "filter":99.0,
      "fine_steps":false,
      "input_gain_cb":0.0,
      "layout":"Mono Sum",
      "link_in_out_gain":false,
      "mix":100.0,
      "output_gain_cb":0.0,
      "tune":-5.0
  }'
```

[ffmpeg]: https://www.ffmpeg.org
[pedalboard]: https://spotify.github.io/pedalboard
[sp950]: https://wavetracing.com/products/sp950
