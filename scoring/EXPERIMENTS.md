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
