# Experiments

All five experiments score the same task on hidden scenes: recover a
high-dynamic-range two-reflection waveform and both off-grid spike times
(including the weak reflection) from low-bit modulo samples with thermal
sensor noise.  Each is scored against recovery from a conventional ADC with
the same input range and bit budget, which clips.  The settings follow the
paper's Fig. 2 axes (dynamic range and bit depth).

## synthetic_lowbit_hdr_dr10

Moderate dynamic range (signal 10x the ADC range) at 3 bits.  Establishes the
basic claim that modulo sensing recovers both the waveform and the timing far
better than a clipping ADC under a fixed low bit budget; the folding is mild
enough that recovery quality is limited mainly by quantization.

## synthetic_lowbit_hdr_dr20

The same task at twice the dynamic range (20x), 3 bits.  Checks that the
advantage persists and grows as clipping becomes more severe.

## synthetic_lowbit_hdr_dr30

The paper's largest dynamic range (30x) at 3 bits.  Here the signal changes
fast enough relative to the sampling grid that noise and coarse quantization
make the folding hard to undo sample by sample; it tests whether recovery
stays robust under these sensor distortions rather than failing on most
scenes.

## synthetic_lowbit_hdr_dr30_bits5

30x dynamic range with 5-bit sensing.  The bit-depth axis of Fig. 2: finer
quantization should translate into better waveform and timing accuracy, while
thermal noise still makes the folding occasionally ambiguous.

## synthetic_lowbit_hdr_dr30_bits8

30x dynamic range with 8-bit sensing, where thermal noise rather than
quantization dominates.  Tests the high-resolution end of the bit-depth axis
and robustness to sporadic noise-induced folding ambiguities.
