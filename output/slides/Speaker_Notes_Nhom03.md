# Group 03 - Speaker notes

Use the short scripts below. Source references in PPTX notes are not spoken.

- Võ Thanh Quân: 167 seconds, 278 spoken words.
- Vương Quốc Trung: 153 seconds, 250 spoken words.
- Đinh Huỳnh Nguyên Khang: 167 seconds, 280 spoken words.

## Slide 1 - DSP Midterm, Group 03

Presenter: Võ Thanh Quân. Target: 10 seconds.

Hello. We are Group 03. We compare Binary Search, Histogram and Statistics for speech and silence segmentation.

## Slide 2 - Shared experiment settings

Presenter: Võ Thanh Quân. Target: 20 seconds.

We use four TRAIN WAVs and four separate TEST WAVs. Each 25 ms window is centered on a 10 ms decision cell. We normalize STE per WAV, then fill silence below 200 ms. Red boundaries come from LAB. Blue boundaries come from the algorithm. F0 is an independent estimate.

## Slide 3 - Binary Search

Presenter: Võ Thanh Quân. Target: 35 seconds.

TRAIN selects a median order after STE normalization. LAB labels split the frames into two classes. We keep overlap values and bisect to balance their energy errors. Boundary errors, then MAE, select median 15. The shared threshold is about 0.0016. TEST uses the same processing, followed by the 200 ms silence rule.

## Slide 4 - Binary Search: finding the balance

Presenter: Võ Thanh Quân. Target: 30 seconds.

The left plot uses the actual TRAIN overlap. Increasing T reduces Silence energy above T and increases Speech energy below T. The green line marks their balance. The right plot records the real midpoint and search interval over 24 iterations. It converges to the shared threshold. The curves and iteration history come from the same solver used for classification.

## Slide 5 - Binary Search: phone_F2

Presenter: Võ Thanh Quân. Target: 18 seconds.

For phone_F2, Start matches. End 60 ms late. MAE is 30 ms. Tail median STE remains above the fixed threshold. Extra and missing boundaries are zero.

## Slide 6 - Binary Search: phone_M2

Presenter: Võ Thanh Quân. Target: 18 seconds.

For phone_M2, Start matches. End matches. MAE is 0 ms. Both LAB timestamps match the detected transitions. Extra and missing boundaries are zero.

## Slide 7 - Binary Search: studio_F2

Presenter: Võ Thanh Quân. Target: 18 seconds.

For studio_F2, Start 10 ms early. End 10 ms early. MAE is 10 ms. Energy crosses T before the LAB transitions. Extra and missing boundaries are zero.

## Slide 8 - Binary Search: studio_M2

Presenter: Võ Thanh Quân. Target: 18 seconds.

For studio_M2, Start 10 ms late. End matches. MAE is 5 ms. Possible cause: weak energy near the onset. Extra and missing boundaries are zero.

## Slide 9 - Histogram

Presenter: Vương Quốc Trung. Target: 35 seconds.

We build 128-bin histograms and smooth the counts over three bins. TRAIN selects W from eight candidates using boundary errors, then MAE. The selected W is 30. For each TEST recording, we choose the first two local peaks along the energy axis. We combine their locations with more weight on the first peak. The threshold therefore adapts to each WAV. If fewer than two peaks exist, we use the mean STE of that WAV. After classification, we fill silence below 200 ms.

## Slide 10 - Histogram: selected peaks and threshold

Presenter: Vương Quốc Trung. Target: 30 seconds.

These are the actual energy counts for phone_F2. The blue line is the three-bin smoothing. M1 and M2 are the first two local peaks along the energy axis. The green line marks T. W equals 30, so T stays close to M1. The zoom uses logarithmic counts to make the smaller second peak visible. No TEST labels select these peaks.

## Slide 11 - Histogram: phone_F2

Presenter: Vương Quốc Trung. Target: 22 seconds.

For phone_F2, Start 10 ms late. End 10 ms early. MAE is 10 ms. Possible cause: weak energy near the boundaries. Extra and missing boundaries are zero.

## Slide 12 - Histogram: phone_M2

Presenter: Vương Quốc Trung. Target: 22 seconds.

For phone_M2, Start matches. End 10 ms early. MAE is 5 ms. Possible cause: weak energy near the boundaries. Extra and missing boundaries are zero.

## Slide 13 - Histogram: studio_F2

Presenter: Vương Quốc Trung. Target: 22 seconds.

For studio_F2, Start 10 ms early. End 20 ms early. MAE is 15 ms. Onset window includes speech. Tail energy falls below T.. Extra and missing boundaries are zero.

## Slide 14 - Histogram: studio_M2

Presenter: Vương Quốc Trung. Target: 22 seconds.

For studio_M2, Start 20 ms late. End 10 ms early. MAE is 15 ms. Possible cause: weak energy near the boundaries. Extra and missing boundaries are zero.

## Slide 15 - Gaussian Statistics

Presenter: Đinh Huỳnh Nguyên Khang. Target: 35 seconds.

Statistics uses labeled normalized STE from all four TRAIN recordings. LAB labels give 503 silence frames and 794 speech frames. We calculate each class mean and standard deviation, then choose a Gaussian crossing between the class means. The learned threshold is about 0.00276. We keep it fixed for every TEST WAV. This method uses unfiltered normalized STE. After classification, we fill silence shorter than 200 ms.

## Slide 16 - Gaussian: observed data and crossing

Presenter: Đinh Huỳnh Nguyên Khang. Target: 30 seconds.

The left panel compares observed TRAIN features with the two fitted Gaussian models. Silence is concentrated near zero, while Speech spreads more widely. Expanded axes make both visible. The right panel zooms on the selected crossing at about 0.00276. Observations do not perfectly follow Gaussian curves. The crossing provides the shared threshold used on TEST.

## Slide 17 - Statistics: phone_F2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 18 seconds.

For phone_F2, Start matches. End 10 ms late. MAE is 5 ms. Tail STE remains above the shared threshold. Extra and missing boundaries are zero.

## Slide 18 - Statistics: phone_M2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 18 seconds.

For phone_M2, Start matches. End 10 ms early. MAE is 5 ms. Possible cause: weak energy near the boundaries. Extra and missing boundaries are zero.

## Slide 19 - Statistics: studio_F2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 18 seconds.

For studio_F2, Start 10 ms early. End 20 ms early. MAE is 15 ms. Onset window includes speech. Tail energy falls below T.. Extra and missing boundaries are zero.

## Slide 20 - Statistics: studio_M2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 18 seconds.

For studio_M2, Start 10 ms late. End 10 ms early. MAE is 10 ms. Possible cause: weak energy near the boundaries. Extra and missing boundaries are zero.

## Slide 21 - Statistics has the lowest mean TEST MAE (ms)

Presenter: Đinh Huỳnh Nguyên Khang. Target: 25 seconds.

On these four TEST WAVs, Binary Search and Histogram both average 11.25 ms. Statistics averages 8.75 ms, the lowest in our comparison. All three methods match eight reference boundaries with zero extra or missing boundaries. The mean row averages the four files. These results apply to this TEST set.

## Slide 22 - Thank you

Presenter: Đinh Huỳnh Nguyên Khang. Target: 5 seconds.

Thank you for listening.