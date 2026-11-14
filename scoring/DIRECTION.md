# Direction

Work on recovering sparse off-grid spikes and the high-dynamic-range waveform
from low-bit modulo samples under sensor noise: better ways to undo the
folding robustly, more accurate spike estimation from the recovered signal,
and better use of the known sensor model, at a fixed bit budget.

Out of scope: learned regressors trained on the generator's labels that do not
model the sensing physics, exploiting the synthetic scene distribution (e.g.
hard-coding position or ratio ranges) instead of solving the inverse problem,
reading anything other than the method input, and changing the acquisition.
