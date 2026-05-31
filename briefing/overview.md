# Overview

This paper studies off-grid sparse spike recovery when measurements are both
coarsely sampled and low-bit quantized. Conventional ADCs clip strong signals
or bury weak ones under quantization noise. The proposed US-SRes method uses
modulo sensing to avoid clipping, then recovers the hidden integer residues and
performs spectral super-resolution to estimate spike times and amplitudes.

The reproduction package implements the paper's modulo finite-difference
recovery path on a deterministic synthetic weak/strong ToF-like benchmark.
The hardware ToF data and the full robust SRes-IterSiS loop are not reproduced;
the packaged experiment focuses on the central Fig. 2-style claim that modulo
sensing can retain high-dynamic-range information under a fixed low bit budget
where conventional clipped acquisition fails.
