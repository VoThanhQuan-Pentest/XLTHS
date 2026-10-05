# Group 03 - Speaker notes

Use these short scripts for the English presentation. Source references in PPTX notes are not spoken.

- Võ Thanh Quân: 170 seconds, 289 spoken words.
- Vương Quốc Trung: 148 seconds, 230 spoken words.
- Đinh Huỳnh Nguyên Khang: 165 seconds, 265 spoken words.

## Slide 1 - DSP Midterm, Group 03

Presenter: Võ Thanh Quân. Target: 12 seconds.

Hello. We are Group 03. We compare Binary Search, Histogram and Statistics for speech and silence segmentation.

## Slide 2 - Shared experiment settings

Presenter: Võ Thanh Quân. Target: 26 seconds.

We use four TRAIN WAVs and four separate TEST WAVs. Each 25 ms window is centered on a 10 ms decision cell. We normalize STE per WAV, then fill silence below 200 ms. Red boundaries come from LAB. Blue boundaries come from the algorithm. F0 is an independent estimate.

## Slide 3 - Binary Search

Presenter: Võ Thanh Quân. Target: 48 seconds.

On TRAIN, we try six median orders after normalization. LAB timestamps split the frames into silence and speech. We keep only overlapping energy values. Binary Search halves the interval to balance misclassified energy on the two sides. We select the median by extra or missing boundaries, then MAE. This is calibration on TRAIN. The selected median is 15 frames and the shared threshold is about 0.0016. On TEST, we use the same median and threshold, then fill silence shorter than 200 ms.

## Slide 4 - Binary Search: phone_F2

Presenter: Võ Thanh Quân. Target: 21 seconds.

For phone_F2, Start matches. End 60 ms late. MAE is 30 ms, with zero extra or missing boundaries. Tail median STE remains above the fixed threshold. The bottom plot shows F0 and the LAB mean reference.

## Slide 5 - Binary Search: phone_M2

Presenter: Võ Thanh Quân. Target: 21 seconds.

For phone_M2, Start matches. End matches. MAE is 0 ms, with zero extra or missing boundaries. Both LAB timestamps match the detected transitions. The bottom plot shows F0 and the LAB mean reference.

## Slide 6 - Binary Search: studio_F2

Presenter: Võ Thanh Quân. Target: 21 seconds.

For studio_F2, Start 10 ms early. End 10 ms early. MAE is 10 ms, with zero extra or missing boundaries. Energy crosses T before the LAB transitions. The bottom plot shows F0 and the LAB mean reference.

## Slide 7 - Binary Search: studio_M2

Presenter: Võ Thanh Quân. Target: 21 seconds.

For studio_M2, Start 10 ms late. End matches. MAE is 5 ms, with zero extra or missing boundaries. Possible cause: weak energy near the onset. The bottom plot shows F0 and the LAB mean reference.

## Slide 8 - Histogram

Presenter: Vương Quốc Trung. Target: 48 seconds.

We build 128-bin histograms and smooth the counts over three bins. TRAIN selects W from eight candidates using boundary errors, then MAE. The selected W is 30. For each TEST recording, we choose the first two local peaks along the energy axis. We combine their locations with more weight on the first peak. The threshold therefore adapts to each WAV. If fewer than two peaks exist, we use the mean STE of that WAV. After classification, we fill silence below 200 ms.

## Slide 9 - Histogram: phone_F2

Presenter: Vương Quốc Trung. Target: 25 seconds.

For phone_F2, Start 10 ms late. End 10 ms early. MAE is 10 ms, with zero extra or missing boundaries. Possible cause: weak energy near the boundaries. The bottom plot shows F0 and the LAB mean reference.

## Slide 10 - Histogram: phone_M2

Presenter: Vương Quốc Trung. Target: 25 seconds.

For phone_M2, Start matches. End 10 ms early. MAE is 5 ms, with zero extra or missing boundaries. Possible cause: weak energy near the boundaries. The bottom plot shows F0 and the LAB mean reference.

## Slide 11 - Histogram: studio_F2

Presenter: Vương Quốc Trung. Target: 25 seconds.

For studio_F2, Start 10 ms early. End 20 ms early. MAE is 15 ms, with zero extra or missing boundaries. Onset window includes speech. Tail energy falls below T.. The bottom plot shows F0 and the LAB mean reference.

## Slide 12 - Histogram: studio_M2

Presenter: Vương Quốc Trung. Target: 25 seconds.

For studio_M2, Start 20 ms late. End 10 ms early. MAE is 15 ms, with zero extra or missing boundaries. Possible cause: weak energy near the boundaries. The bottom plot shows F0 and the LAB mean reference.

## Slide 13 - Gaussian Statistics

Presenter: Đinh Huỳnh Nguyên Khang. Target: 44 seconds.

Statistics uses labeled normalized STE from all four TRAIN recordings. LAB labels give 503 silence frames and 794 speech frames. We calculate each class mean and standard deviation, then choose a Gaussian crossing between the class means. The learned threshold is about 0.00276. We keep it fixed for every TEST WAV. This method uses unfiltered normalized STE. After classification, we fill silence shorter than 200 ms.

## Slide 14 - Statistics: phone_F2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 21 seconds.

For phone_F2, Start matches. End 10 ms late. MAE is 5 ms, with zero extra or missing boundaries. Tail STE remains above the shared threshold. The bottom plot shows F0 and the LAB mean reference.

## Slide 15 - Statistics: phone_M2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 21 seconds.

For phone_M2, Start matches. End 10 ms early. MAE is 5 ms, with zero extra or missing boundaries. Possible cause: weak energy near the boundaries. The bottom plot shows F0 and the LAB mean reference.

## Slide 16 - Statistics: studio_F2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 21 seconds.

For studio_F2, Start 10 ms early. End 20 ms early. MAE is 15 ms, with zero extra or missing boundaries. Onset window includes speech. Tail energy falls below T.. The bottom plot shows F0 and the LAB mean reference.

## Slide 17 - Statistics: studio_M2

Presenter: Đinh Huỳnh Nguyên Khang. Target: 21 seconds.

For studio_M2, Start 10 ms late. End 10 ms early. MAE is 10 ms, with zero extra or missing boundaries. Possible cause: weak energy near the boundaries. The bottom plot shows F0 and the LAB mean reference.

## Slide 18 - Statistics has the lowest mean TEST MAE (ms)

Presenter: Đinh Huỳnh Nguyên Khang. Target: 32 seconds.

On these four TEST WAVs, Binary Search and Histogram both average 11.25 ms. Statistics averages 8.75 ms, the lowest in our comparison. All three methods match eight reference boundaries with zero extra or missing boundaries. The mean row averages the four files. These results apply to this TEST set.

## Slide 19 - Thank you

Presenter: Đinh Huỳnh Nguyên Khang. Target: 5 seconds.

Thank you for listening.