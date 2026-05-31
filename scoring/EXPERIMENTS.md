# Experiments

## synthetic_lowbit_hdr_dr10

This experiment checks whether a method can recover a high-dynamic-range
two-reflection waveform and its off-grid spike times from low-bit measurements
when the conventional ADC range is moderately exceeded. It measures benefit
over a clipped sparse-recovery baseline while preserving low bit depth,
weak/strong amplitude disparity, and a fixed dynamic-range stress level.

## synthetic_lowbit_hdr_dr20

This experiment checks the same low-bit two-reflection recovery problem under
a stronger dynamic-range stress level. It asks whether the main claimed effect
remains visible when the strong component is much larger than the sensing
range available to a conventional clipped ADC.

## synthetic_lowbit_hdr_dr30

This experiment checks robustness at the hardest dynamic-range setting included
in the compact reproduction. It is intended to show whether the recovery
advantage persists as the clipping problem becomes more severe while the
measurement bit depth and weak/strong amplitude disparity remain fixed.

## synthetic_lowbit_hdr_dr20_bits5

This experiment keeps the middle dynamic-range stress level fixed and increases
the quantization budget to 5 bits. It checks whether recovery quality remains
high when the measurement has finer low-range quantization but still faces the
same high-dynamic-range clipping challenge.

## synthetic_lowbit_hdr_dr20_bits8

This experiment repeats the middle dynamic-range stress level with 8-bit
measurements. It adds a less quantization-limited setting so the benchmark
tests both dynamic-range stress and bit-depth variation.
