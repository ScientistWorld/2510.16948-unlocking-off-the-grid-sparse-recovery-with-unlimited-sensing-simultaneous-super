# Overview

Guo & Bhandari, "Unlocking Off-the-Grid Sparse Recovery with Unlimited
Sensing: Simultaneous Super-Resolution in Time and Amplitude" (IEEE JSTSP).

Conventional ADCs with a fixed bit budget either clip strong reflections or
bury weak ones under quantization noise.  The paper uses modulo (unlimited)
sensing to avoid clipping and develops SRes-IterSiS, which recovers the hidden
folding residue and then the off-grid spikes by spectral fitting, robustly to
sensor noise.  It reports at least 30 dB lower recovery MSE than a
conventional ADC across dynamic ranges of 10-30 lambda and 3-15 bits (Fig. 2),
and hardware time-of-flight results.

This gym is a synthetic substitute (the hardware tensors are not released):
weak/strong Gaussian-pulse pairs at the Fig. 2 settings, with thermal sensor
noise, recovered from 3-, 5- or 8-bit modulo samples.  Methods are scored on
hidden scenes for waveform fidelity (gain over a clipping ADC, PSNR) and spike
timing (both spikes, the weak spike, and their separation).  The reference is
the paper's Algorithm 1; it reproduces the >= 30 dB claim in every setting,
and its robust residue loop is what keeps it working at 30 lambda where naive
first-difference unwrapping breaks.  It is not at the limit of any metric:
better estimators score several dB higher in every setting.
